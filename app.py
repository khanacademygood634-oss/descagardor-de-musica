import os
import sys
import threading
import time
import re
from pathlib import Path
from flask import Flask, request, render_template, send_from_directory, jsonify
from flask_sock import Sock
import yt_dlp
import pyperclip
import json

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

def download_audio(url: str, output_dir=DOWNLOADS):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            # replace extension with .mp3 if postprocessing changed it
            base = os.path.splitext(filename)[0] + ".mp3"
            return {"status": "ok", "file": base, "title": info.get("title")}
    except Exception as e:
        return {"status": "error", "error": str(e)}

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
        return jsonify({"status":"error","error":"URL no válida de YouTube"}), 400
    result = download_audio(url)
    return jsonify(result)

@app.route("/archivo/<path:nombre>")
def archivo(nombre):
    # Send from downloads path (note: only for local use)
    try:
        return send_from_directory(DOWNLOADS, nombre, as_attachment=True)
    except Exception as e:
        return str(e), 404

# WebSocket to notify frontend about clipboard-detected URLs and download events
clients = set()

@sock.route("/monitor_ws")
def monitor_ws(ws):
    clients.add(ws)
    try:
        while True:
            msg = ws.receive()
            # if frontend sends command to toggle monitor
            if msg is None:
                break
            try:
                obj = json.loads(msg)
            except Exception:
                continue
            cmd = obj.get("cmd")
            if cmd == "status":
                ws.send(json.dumps({"type":"status","monitor":clipboard_monitor_enabled}))
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

def clipboard_watcher():
    last = ""
    global clipboard_monitor_enabled
    while True:
        time.sleep(1.5)
        with clipboard_lock:
            enabled = clipboard_monitor_enabled
        if not enabled:
            continue
        try:
            text = pyperclip.paste()
        except Exception:
            text = ""
        if text and text != last and valid_youtube_url(text):
            last = text
            notify_clients({"type":"detected","url":text})
            # perform download in a separate thread so watcher keeps running
            def dl_and_notify(u):
                notify_clients({"type":"status","message":"Descargando", "url": u})
                res = download_audio(u)
                if res.get("status") == "ok":
                    notify_clients({"type":"done","file": os.path.basename(res.get("file")), "title": res.get("title")})
                else:
                    notify_clients({"type":"error","error": res.get("error")})
            threading.Thread(target=dl_and_notify, args=(text,), daemon=True).start()

# start watcher thread
t = threading.Thread(target=clipboard_watcher, daemon=True)
t.start()

if __name__ == "__main__":
    # run local dev server (not for production)
    app.run(host="0.0.0.0", port=5000, debug=True)


# Small endpoint to toggle monitor (called by frontend)

from flask import request
@app.route("/toggle_monitor", methods=["POST"])
def toggle_monitor():
    global clipboard_monitor_enabled
    data = request.get_json() or {}
    enabled = bool(data.get("enabled", False))
    with clipboard_lock:
        clipboard_monitor_enabled = enabled
    return jsonify({"monitor": clipboard_monitor_enabled})
