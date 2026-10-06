"""Servidor web para dwb.py: pega un enlace de YouTube y descarga el video o el audio.

Local:      flask --app web run
Producción: gunicorn -b 0.0.0.0:8000 --threads 4 --timeout 600 web:app

Variables de entorno opcionales:
    DWB_CLAVE    si se define, hay que enviar ?clave=... para poder descargar
    DWB_COOKIES  ruta a un cookies.txt de YouTube (los servidores en la nube suelen necesitarlo)
"""
import hmac
import os
import shutil
import tempfile
from urllib.parse import urlparse

from flask import Flask, abort, render_template_string, request, send_file

import dwb

app = Flask(__name__)

YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be"}
CALIDADES = {"360", "480", "720", "1080"}

PAGE = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Descargador de YouTube</title>
<style>
  :root { --bg: #f6f6f4; --card: #fff; --text: #1d1d1b; --muted: #6b6b66; --line: #d9d9d4; --accent: #c4302b; }
  @media (prefers-color-scheme: dark) {
    :root { --bg: #161615; --card: #20201f; --text: #ededea; --muted: #a3a39d; --line: #3a3a37; --accent: #ff5a52; }
  }
  * { box-sizing: border-box; }
  body { margin: 0; min-height: 100vh; display: grid; place-items: center; padding: 16px;
         background: var(--bg); color: var(--text); font: 16px/1.5 system-ui, sans-serif; }
  form { width: 100%; max-width: 480px; background: var(--card); border: 1px solid var(--line);
         border-radius: 12px; padding: 24px; display: grid; gap: 14px; }
  h1 { margin: 0; font-size: 1.3rem; }
  label { display: grid; gap: 4px; font-size: .9rem; color: var(--muted); }
  input, select, button { font: inherit; padding: 10px 12px; border-radius: 8px;
                          border: 1px solid var(--line); background: var(--bg); color: var(--text); }
  .fila { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  button { background: var(--accent); color: #fff; border: 0; font-weight: 600; cursor: pointer; }
  #estado { margin: 0; min-height: 1.5em; font-size: .9rem; color: var(--muted); }
</style>
</head>
<body>
<form action="descargar" method="get" onsubmit="document.getElementById('estado').textContent = 'Preparando la descarga… puede tardar un poco.'">
  <h1>Descargador de YouTube</h1>
  <label>Enlace del video
    <input name="url" type="url" required placeholder="https://youtu.be/…">
  </label>
  <div class="fila">
    <label>Formato
      <select name="tipo">
        <option value="video">Video (mp4)</option>
        <option value="audio">Solo audio (mp3)</option>
      </select>
    </label>
    <label>Calidad máxima
      <select name="calidad">
        <option value="">La mejor</option>
        <option>1080</option><option>720</option><option>480</option><option>360</option>
      </select>
    </label>
  </div>
  {% if con_clave %}
  <label>Clave
    <input name="clave" type="password" required>
  </label>
  {% endif %}
  <button type="submit">Descargar</button>
  <p id="estado" role="status"></p>
</form>
</body>
</html>
"""


@app.get("/")
def index():
    return render_template_string(PAGE, con_clave=bool(os.getenv("DWB_CLAVE")))


@app.get("/descargar")
def descargar():
    clave = os.getenv("DWB_CLAVE")
    if clave and not hmac.compare_digest(request.args.get("clave", "").encode(), clave.encode()):
        abort(403, "Clave incorrecta.")

    url = request.args.get("url", "").strip()
    if urlparse(url).hostname not in YOUTUBE_HOSTS:
        abort(400, "Solo se admiten enlaces de YouTube.")
    calidad = request.args.get("calidad", "")
    if calidad and calidad not in CALIDADES:
        abort(400, "Calidad no válida.")

    carpeta = tempfile.mkdtemp(prefix="dwb-")
    try:
        ruta = dwb.download(
            url, carpeta,
            audio_only=request.args.get("tipo") == "audio",
            max_height=int(calidad) if calidad else None,
            cookies=os.getenv("DWB_COOKIES"),
            # Solo el extractor de YouTube: así nadie puede usar el servidor para pedir otras URLs.
            extra_opts={"allowed_extractors": ["youtube"]},
        )
    except Exception as exc:
        shutil.rmtree(carpeta, ignore_errors=True)
        abort(502, f"No se pudo descargar: {exc}")

    respuesta = send_file(ruta, as_attachment=True)
    # Con direct_passthrough el servidor recibe el archivo tal cual y nunca llama a
    # call_on_close, así que la carpeta temporal se quedaría en disco para siempre.
    respuesta.direct_passthrough = False
    respuesta.call_on_close(lambda: shutil.rmtree(carpeta, ignore_errors=True))
    return respuesta
