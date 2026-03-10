# Zgolotuber API Server — Deploy Guide

## Files in this folder
- `server.py` — Flask + yt-dlp API
- `requirements.txt` — Python dependencies
- `Procfile` — tells the host how to start the server
- `runtime.txt` — Python version

---

## OPTION A: Deploy on Render.com (Free)

### Step 1 — Push to GitHub
1. Create a free account at https://github.com
2. Create a new repository called `zgolotuber-server`
3. Upload all 4 files in this folder to that repo

### Step 2 — Connect to Render
1. Go to https://render.com and sign up free
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub account and select your `zgolotuber-server` repo
4. Fill in the settings:
   - **Name:** zgolotuber-api
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn server:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
   - **Instance Type:** Free
5. Click **"Create Web Service"**

### Step 3 — Get your URL
Render will give you a URL like:
```
https://zgolotuber-api.onrender.com
```
That is your API_BASE URL. Copy it.

⚠️ **Note:** Free Render services "sleep" after 15 minutes of inactivity.
The first request after sleeping takes ~30 seconds to wake up. This is normal.

---

## OPTION B: Deploy on Koyeb (Free)

### Step 1 — Push to GitHub (same as above)
Upload the 4 files to a GitHub repo.

### Step 2 — Deploy on Koyeb
1. Go to https://app.koyeb.com and sign up free
2. Click **"Create App"**
3. Choose **GitHub** as the source
4. Select your `zgolotuber-server` repo
5. Fill in:
   - **Run command:** `gunicorn server:app --bind 0.0.0.0:8000 --workers 2 --timeout 120`
   - **Port:** `8000`
   - **Instance:** Free (Nano)
6. Click **"Deploy"**

### Step 3 — Get your URL
Koyeb gives you a URL like:
```
https://zgolotuber-api-yourname.koyeb.app
```
That is your API_BASE URL.

✅ **Koyeb advantage:** Does NOT sleep on the free tier — always on.

---

## Step 4 — Update the website

Open `zgolotuber-webapp.html` and find this line near the bottom:

```javascript
const API_BASE = 'https://api.zgolotuber.com';
```

Replace it with YOUR server URL, for example:

```javascript
const API_BASE = 'https://zgolotuber-api.onrender.com';
```
or
```javascript
const API_BASE = 'https://zgolotuber-api-yourname.koyeb.app';
```

Save the file. Done — your website now works fully!

---

## Test your server

Once deployed, open this in your browser to confirm it's running:

```
https://YOUR-SERVER-URL/health
```

You should see:
```json
{"status": "ok"}
```

Then test a real extraction:
```
https://YOUR-SERVER-URL/extract?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ
```
