"""
Zgolotuber API Server
=====================
yt-dlp powered video info extractor.
Deploy on Render.com or Koyeb for free.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import logging
import os
import urllib.request

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

YDL_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
    "youtube_include_dash_manifest": False,
    "geo_bypass": True,
    "http_headers": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    },
}


def resolve_redirect(url):
    """Follow redirects to get the real URL — fixes Facebook /share/r/ links."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120"}
        )
        res = urllib.request.urlopen(req, timeout=10)
        return res.url
    except Exception:
        return url


def is_redirect_url(url):
    patterns = ["facebook.com/share/", "fb.watch/", "fb.com/", "t.co/", "bit.ly/", "tinyurl.com/"]
    return any(p in url for p in patterns)


@app.route("/")
def index():
    return jsonify({"app": "Zgolotuber API", "status": "running"})


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/extract")
def extract():
    url = request.args.get("url", "").strip()
    if not url or not url.startswith("http"):
        return jsonify({"error": "Invalid or missing URL"}), 400

    if is_redirect_url(url):
        logger.info(f"Resolving redirect: {url}")
        url = resolve_redirect(url)
        logger.info(f"Resolved to: {url}")

    logger.info(f"Extracting: {url}")

    try:
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            info = ydl.extract_info(url, download=False)

        if not info:
            return jsonify({"error": "Could not extract video info"}), 404

        if info.get("_type") == "playlist":
            entries = [e for e in info.get("entries", []) if e]
            if not entries:
                return jsonify({"error": "Empty playlist"}), 404
            info = entries[0]

        formats = []
        seen = set()

        for f in info.get("formats", []):
            dl_url = f.get("url", "")
            if not dl_url:
                continue

            ext = f.get("ext", "mp4")
            vcodec = f.get("vcodec", "")
            height = f.get("height")
            is_audio = (vcodec == "none" or not vcodec)

            if is_audio:
                quality = f.get("format_note") or "Audio only"
            elif height:
                quality = f"{height}p"
                if (f.get("fps") or 0) >= 60:
                    quality += "60"
            else:
                quality = f.get("format_note") or "Unknown"

            key = f"{quality}_{ext}_{'a' if is_audio else 'v'}"
            if key in seen:
                continue
            seen.add(key)

            formats.append({
                "format_id":     f.get("format_id", ""),
                "ext":           ext,
                "format_note":   quality,
                "height":        height,
                "width":         f.get("width"),
                "filesize":      f.get("filesize") or f.get("filesize_approx") or 0,
                "url":           dl_url,
                "vcodec":        vcodec,
                "acodec":        f.get("acodec", ""),
                "tbr":           f.get("tbr"),
                "is_audio_only": is_audio,
            })

        formats.sort(key=lambda x: (0 if not x["is_audio_only"] else 1, -(x["height"] or 0)))

        if not formats:
            return jsonify({"error": "No downloadable formats found. The video may be private or require login."}), 404

        return jsonify({
            "id":          info.get("id", ""),
            "title":       info.get("title", ""),
            "description": (info.get("description") or "")[:300],
            "thumbnail":   info.get("thumbnail", ""),
            "duration":    info.get("duration", 0),
            "uploader":    info.get("uploader") or info.get("channel", ""),
            "view_count":  info.get("view_count", 0),
            "formats":     formats,
            "webpage_url": info.get("webpage_url", url),
        })

    except yt_dlp.utils.DownloadError as e:
        msg = str(e)
        if "login" in msg.lower() or "sign in" in msg.lower():
            return jsonify({"error": "This video requires login. Try a public video."}), 422
        if "private" in msg.lower():
            return jsonify({"error": "This video is private."}), 422
        return jsonify({"error": f"Could not process this URL: {msg}"}), 422

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return jsonify({"error": "Internal server error. Please try again."}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
