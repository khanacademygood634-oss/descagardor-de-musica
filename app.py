import os
import sys
import threading
import time
import re
import json
from pathlib import Path
from flask import Flask, request, render_template, send_from_directory, jsonify
from flask_sock import Sock
import yt_dlp

app = Flask(__name__)
sock = Sock(app)

# Cross-platform downloads folder
def get_downloads_folder():
    home = Path.home()
    if sys.platform.startswith("win"):
        return os.path.join(os.environ.get("USERPROFILE", home), "Downloads")
    if sys.platform.startswith("linux"):
        # Android Termux common path
        if "ANDROID_ROOT" in os.environ or "com.termux" in str(home):
            return os.path.join(str(home), "storage", "downloads")
        return os.path.join(str(home), "Downloads")
    if sys.platform == "darwin":
        return os.path.join(str(home), "Downloads")
    return os.path.join(str(home), "Downloads")

DOWNLOADS = get_downloads_folder()
os.makedirs(DOWNLOADS, exist_ok=True)

clipboard_monitor_enabled = False
clipboard_lock = threading.Lock()

YOUTUBE_REGEX = re.compile(r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/\S+")

def valid_youtube_url(url: str):
    return bool(YOUTUBE_REGEX.search(url))


def get_cookies_file():
    """Return a path to a cookies file if available.

    Priority:
      1. Environment var `YTDLP_COOKIES_CONTENT` (contents of cookies file)
      2. Environment var `YTDLP_COOKIES` (path on filesystem)
      3. ./cookies.txt in current working dir
    """
    # 1) content provided in env var (useful for Render secrets)
    content = os.environ.get("YTDLP_COOKIES_CONTENT")
    if content:
        try:
            target = os.path.join("/tmp", "ytdlp_cookies.txt")
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)
            return target
        except Exception:
            return None

    # 2) path provided
    path = os.environ.get("YTDLP_COOKIES")
    if path and os.path.exists(path):
        return path

    # 3) fallback ./cookies.txt
    fallback = os.path.join(os.getcwd(), "cookies.txt")
    if os.path.exists(fallback):
        return fallback

    return None

def download_audio(url: str, output_dir=DOWNLOADS):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'socket_timeout': 30,
        'extractor_args': {'youtube': {'player_client': ['ios']}},
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        },
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
    }
    # Attach cookiefile if provided via environment or local file
    cookie_file = get_cookies_file()
    if cookie_file:
        ydl_opts['cookiefile'] = cookie_file
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            base = os.path.splitext(filename)[0] + ".mp3"
            return {"status": "ok", "file": base, "title": info.get("title")}
    except Exception as e:
        msg = str(e)
        # Detect common yt-dlp auth message and return actionable instructions
        if "Sign in to confirm" in msg or "--cookies" in msg or "use --cookies" in msg:
            help_text = (
                "YouTube requires cookies to download this video. "
                "Provide a cookies file via the environment variable `YTDLP_COOKIES` (path) "
                "or `YTDLP_COOKIES_CONTENT` (file contents). See: https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp"
            )
            return {"status": "error", "error": help_text}
        return {"status": "error", "error": msg}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/descargar", methods=["POST"])
def descargar():
    data = request.get_json() or {}
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"status":"error","error":"No URL provided"}), 400
    if not valid_youtube_url(url):
           return jsonify({"status":"error","error":"URL no valida de YouTube"}), 400
    result = download_audio(url)
    return jsonify(result)

@app.route("/archivo/<path:nombre>")
def archivo(nombre):
    try:
        return send_from_directory(DOWNLOADS, nombre, as_attachment=True)
    except Exception as e:
        return str(e), 404

clients = set()

@sock.route("/monitor_ws")
def monitor_ws(ws):
    clients.add(ws)
    try:
        while True:
            try:
                msg = ws.receive(timeout=5)
                if msg is None:
                    break
                try:
                    obj = json.loads(msg)
                except Exception:
                    continue
                cmd = obj.get("cmd")
                if cmd == "status":
                    ws.send(json.dumps({"type":"status","monitor":clipboard_monitor_enabled}))
            except Exception:
                break
    finally:
        clients.discard(ws)

def notify_clients(obj):
    dead = []
    for ws in list(clients):
        try:
            ws.send(json.dumps(obj))
        except Exception:
            dead.append(ws)
    for d in dead:
        clients.discard(d)

def process_clipboard_url(url: str):
    """Procesa URL desde el portapapeles del navegador"""
    if valid_youtube_url(url):
        notify_clients({"type":"detected","url":url})
        def dl_and_notify(u):
            notify_clients({"type":"status","message":"Descargando", "url": u})
            res = download_audio(u)
            if res.get("status") == "ok":
                notify_clients({"type":"done","file": os.path.basename(res.get("file")), "title": res.get("title")})
            else:
                notify_clients({"type":"error","error": res.get("error")})
        threading.Thread(target=dl_and_notify, args=(url,), daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

@app.route("/toggle_monitor", methods=["POST"])
def toggle_monitor():
    global clipboard_monitor_enabled
    data = request.get_json() or {}
    enabled = bool(data.get("enabled", False))
    with clipboard_lock:
        clipboard_monitor_enabled = enabled
    return jsonify({"monitor": clipboard_monitor_enabled})

@app.route("/check_clipboard_url", methods=["POST"])
def check_clipboard_url():
    """Endpoint para recibir URLs del portapapeles desde el navegador (Clipboard API)"""
    global clipboard_monitor_enabled
    data = request.get_json() or {}
    url = data.get("url", "").strip()
    
    with clipboard_lock:
        enabled = clipboard_monitor_enabled
    
    if enabled and url:
        process_clipboard_url(url)
        return jsonify({"status": "ok"})
    return jsonify({"status": "ignored"})
