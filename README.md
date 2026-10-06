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
