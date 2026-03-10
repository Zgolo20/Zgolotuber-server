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

app = Flask(__name__)
CORS(app)  # Allow requests from your website

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

YDL_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
    "youtube_include_dash_manifest": False,
    "http_headers": {
        "User-Agent": "Mozilla/5.0 (Android 13; Mobile) AppleWebKit/537.36 Chrome/120",
    },
}


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

    logger.info(f"Extracting: {url}")

    try:
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            info = ydl.extract_info(url, download=False)

        if not info:
            return jsonify({"error": "Could not extract video info"}), 404

        if info.get("_type") == "playlist":
            entries = info.get("entries", [])
            if not entries:
                return jsonify({"error": "Empty playlist"}), 404
            info = entries[0]

        formats = []
        for f in info.get("formats", []):
            if not f.get("url"):
                continue
            formats.append({
                "format_id": f.get("format_id", ""),
                "ext":        f.get("ext", "mp4"),
                "format_note": f.get("format_note", ""),
                "height":     f.get("height"),
                "width":      f.get("width"),
                "filesize":   f.get("filesize") or f.get("filesize_approx") or 0,
                "url":        f.get("url", ""),
                "vcodec":     f.get("vcodec", ""),
                "acodec":     f.get("acodec", ""),
                "tbr":        f.get("tbr"),
            })

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
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
