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
La descarga se hace en segundo plano y la página muestra el progreso.

```bash
flask --app web run          # en tu ordenador: http://127.0.0.1:5000
docker build -t dwb-web . && docker run -p 8000:8000 dwb-web   # con Docker: http://localhost:8000
```

Para usarlo desde otra web basta con enlazar o enviar un formulario a
`https://TU-DOMINIO/descargar?url=ENLACE&tipo=video|audio&calidad=720`.

Variables de entorno opcionales:

- `DWB_CLAVE`: si se define, la página pide una clave antes de descargar.
- `DWB_COOKIES`: ruta a un `cookies.txt` de YouTube. Los servidores en la nube casi
  siempre lo necesitan, porque YouTube les responde "Sign in to confirm you're not a bot".

Solo acepta enlaces de YouTube, para que nadie pueda usar el servidor para pedir otras direcciones.

### Publicarla desde tu ordenador con tu dominio de Cloudflare

Así el servidor es tu ordenador (YouTube no suele bloquear las conexiones de casa) y
Cloudflare la publica en, por ejemplo, `https://youtube.findaihome.com`, sin abrir puertos.

1. En Cloudflare entra en **Zero Trust → Networks → Tunnels → Create a tunnel**, elige
   **Cloudflared**, ponle un nombre y copia el token que aparece en el comando de instalación
   (la parte larga después de `--token`).
2. En el mismo túnel, en **Public hostname**, añade:
   subdominio `youtube`, dominio `findaihome.com`, tipo `HTTP`, URL `web:8000`.
3. En tu ordenador, con Docker instalado:
   ```bash
   git clone https://github.com/nmandrib/copilot-sandbox && cd copilot-sandbox
   cp .env.example .env      # y pega el token en TUNNEL_TOKEN (y una clave en DWB_CLAVE)
   docker compose up -d
   ```
4. Abre `https://youtube.findaihome.com`. Funciona mientras el ordenador esté encendido.

Si es público, pon `DWB_CLAVE`, o protégela en Cloudflare con **Zero Trust → Access →
Applications** para que solo entren los correos que elijas.
