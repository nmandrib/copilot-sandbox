# copilot-sandbox

Sandbox repository for AI Engineering System copilot draft PR validation.
Not production. Safe for automated draft PR tests.

## dwb.py — descargador de YouTube

```bash
pip install -r requirements.txt
python dwb.py "https://youtu.be/ID"                 # video en mp4 (mejor calidad)
python dwb.py "https://youtu.be/ID" --calidad 720   # limitar a 720p
python dwb.py "https://youtu.be/ID" --audio         # solo audio en mp3
python dwb.py "https://youtu.be/ID" --cookies-navegador chrome  # si YouTube pide iniciar sesión
```

Los archivos se guardan en `descargas/`. Para unir video y audio en alta calidad hace falta `ffmpeg`.

### Versión web

`web.py` es una página donde pegas el enlace y el navegador descarga el archivo.

```bash
flask --app web run          # en tu ordenador: http://127.0.0.1:5000
docker build -t dwb-web . && docker run -p 8000:8000 dwb-web   # para publicarla
```

Para usarlo desde otra web basta con enlazar o enviar un formulario a
`https://TU-SERVIDOR/descargar?url=ENLACE&tipo=video|audio&calidad=720`.

Variables de entorno opcionales:

- `DWB_CLAVE`: si se define, la página pide una clave antes de descargar.
- `DWB_COOKIES`: ruta a un `cookies.txt` de YouTube. Los servidores en la nube casi
  siempre lo necesitan, porque YouTube les responde "Sign in to confirm you're not a bot".

Solo acepta enlaces de YouTube, para que nadie pueda usar el servidor para pedir otras direcciones.
