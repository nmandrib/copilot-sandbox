"""Servidor web para dwb.py: pega un enlace de YouTube y descarga el video o el audio.

La descarga se hace en segundo plano y la página va preguntando cómo va, así ninguna
petición tarda mucho (Cloudflare corta las que no responden en 100 segundos).

Local:      flask --app web run
Producción: gunicorn -b 0.0.0.0:8000 --threads 4 web:app
            (un solo proceso: las descargas en curso se guardan en memoria)

Variables de entorno opcionales:
    DWB_CLAVE    si se define, hay que enviar ?clave=... para poder descargar
    DWB_COOKIES  ruta a un cookies.txt de YouTube (los servidores en la nube suelen necesitarlo)
"""
import hmac
import os
import secrets
import shutil
import tempfile
import threading
import time
from urllib.parse import urlparse

from flask import Flask, abort, jsonify, redirect, render_template_string, request, send_file, url_for

import dwb

app = Flask(__name__)

YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be"}
CALIDADES = {"360", "480", "720", "1080"}
CADUCIDAD = 3600  # segundos que se guarda un archivo que nadie ha recogido

trabajos: dict[str, dict] = {}
cerrojo = threading.Lock()

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
  .tarjeta { width: 100%; max-width: 480px; background: var(--card); border: 1px solid var(--line);
             border-radius: 12px; padding: 24px; display: grid; gap: 14px; }
  h1 { margin: 0; font-size: 1.3rem; }
  label { display: grid; gap: 4px; font-size: .9rem; color: var(--muted); }
  input, select, button { font: inherit; padding: 10px 12px; border-radius: 8px;
                          border: 1px solid var(--line); background: var(--bg); color: var(--text); }
  .fila { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  button { background: var(--accent); color: #fff; border: 0; font-weight: 600; cursor: pointer; }
  #estado { margin: 0; }
  a { color: var(--accent); }
</style>
</head>
<body>
{% if trabajo_id %}
<div class="tarjeta">
  <h1>Descargador de YouTube</h1>
  <p id="estado" role="status">Preparando la descarga…</p>
  <a href="{{ url_for('index') }}">Descargar otro video</a>
</div>
<script>
  const estado = document.getElementById("estado");
  async function comprobar() {
    try {
      const t = await (await fetch({{ url_for('estado', trabajo_id=trabajo_id)|tojson }})).json();
      estado.textContent = t.mensaje;
      if (t.estado === "listo") {
        location.href = {{ url_for('archivo', trabajo_id=trabajo_id)|tojson }};
        return;
      }
      if (t.estado === "error") return;
    } catch {
      estado.textContent = "Sin conexión con el servidor, reintentando…";
    }
    setTimeout(comprobar, 2000);
  }
  comprobar();
</script>
{% else %}
<form class="tarjeta" action="{{ url_for('descargar') }}" method="get">
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
</form>
{% endif %}
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

    _borrar_caducados()
    trabajo_id = secrets.token_urlsafe(16)
    trabajo = {"estado": "descargando", "mensaje": "Preparando la descarga…",
               "creado": time.time(), "carpeta": tempfile.mkdtemp(prefix="dwb-")}
    with cerrojo:
        trabajos[trabajo_id] = trabajo
    threading.Thread(
        target=_descargar, daemon=True,
        args=(trabajo, url, request.args.get("tipo") == "audio", int(calidad) if calidad else None),
    ).start()
    return redirect(url_for("espera", trabajo_id=trabajo_id))


@app.get("/espera/<trabajo_id>")
def espera(trabajo_id):
    return render_template_string(PAGE, trabajo_id=trabajo_id)


@app.get("/estado/<trabajo_id>")
def estado(trabajo_id):
    trabajo = trabajos.get(trabajo_id)
    if not trabajo:
        return jsonify(estado="error", mensaje="Esta descarga no existe o ya se entregó."), 404
    return jsonify(estado=trabajo["estado"], mensaje=trabajo["mensaje"])


@app.get("/archivo/<trabajo_id>")
def archivo(trabajo_id):
    with cerrojo:
        trabajo = trabajos.get(trabajo_id)
        if not trabajo or trabajo["estado"] != "listo":
            abort(404, "Esta descarga no existe o todavía no está lista.")
        del trabajos[trabajo_id]

    respuesta = send_file(trabajo["ruta"], as_attachment=True)
    # Con direct_passthrough el servidor recibe el archivo tal cual y nunca llama a
    # call_on_close, así que la carpeta temporal se quedaría en disco para siempre.
    respuesta.direct_passthrough = False
    respuesta.call_on_close(lambda: shutil.rmtree(trabajo["carpeta"], ignore_errors=True))
    return respuesta


def _descargar(trabajo: dict, url: str, audio_only: bool, max_height: int | None) -> None:
    def progreso(d: dict) -> None:
        total = d.get("total_bytes") or d.get("total_bytes_estimate")
        if d["status"] == "downloading" and total:
            trabajo["mensaje"] = f"Descargando… {d.get('downloaded_bytes', 0) * 100 // total}%"
        elif d["status"] == "finished":
            trabajo["mensaje"] = "Procesando…"

    try:
        trabajo["ruta"] = dwb.download(
            url, trabajo["carpeta"], audio_only=audio_only, max_height=max_height,
            cookies=os.getenv("DWB_COOKIES"),
            # Solo el extractor de YouTube: así nadie puede usar el servidor para pedir otras URLs.
            extra_opts={"allowed_extractors": ["youtube"], "progress_hooks": [progreso]},
        )
    except Exception as exc:
        shutil.rmtree(trabajo["carpeta"], ignore_errors=True)
        trabajo["mensaje"] = f"No se pudo descargar: {exc}"
        trabajo["estado"] = "error"
    else:
        trabajo["mensaje"] = "¡Listo! La descarga empieza ahora."
        trabajo["estado"] = "listo"


def _borrar_caducados() -> None:
    """Borra los archivos que nadie recogió (no toca las descargas en curso)."""
    limite = time.time() - CADUCIDAD
    with cerrojo:
        viejos = [i for i, t in trabajos.items() if t["creado"] < limite and t["estado"] != "descargando"]
        for trabajo_id in viejos:
            shutil.rmtree(trabajos.pop(trabajo_id)["carpeta"], ignore_errors=True)
