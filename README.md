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

### Ejecutable (sin instalar nada)

En la [release `ultima`](https://github.com/nmandrib/copilot-sandbox/releases/tag/ultima) hay un
ejecutable para Windows, Mac y Linux, que GitHub vuelve a generar con cada cambio en `main`. Lleva
dentro ffmpeg y deno. Al abrirlo arranca el servidor en tu ordenador y abre `http://127.0.0.1:8765`;
para pararlo, cierra su ventana.

- **Windows**: como no está firmado, puede salir "Windows protegió tu PC": pulsa
  "Más información" → "Ejecutar de todas formas".
- **Mac**: la primera vez, clic derecho → Abrir (o Ajustes → Privacidad y seguridad → "Abrir igualmente").

Para generarlo tú: `pip install -r requirements.txt pyinstaller imageio-ffmpeg && python empaquetar.py`.

### Que cualquiera la use desde el móvil o el ordenador (Cloudflare)

El servidor es tu ordenador (YouTube no suele bloquear las conexiones de casa) y Cloudflare lo
publica en tu dominio, por ejemplo `https://youtube.findaihome.com`, sin abrir puertos. Quien la
use solo necesita abrir el enlace.

1. En Cloudflare entra en **Zero Trust → Networks → Tunnels → Create a tunnel**, elige
   **Cloudflared** y ponle un nombre.
2. Arranca el servidor de una de estas dos formas:
   - **Con el ejecutable**: Cloudflare te enseña un comando para instalar `cloudflared` en tu
     sistema; ejecútalo y abre `DescargadorYouTube`.
   - **Con Docker**: copia el token del comando (la parte larga después de `--token`) y:
     ```bash
     git clone https://github.com/nmandrib/copilot-sandbox && cd copilot-sandbox
     cp .env.example .env      # pega el token en TUNNEL_TOKEN
     docker compose up -d
     ```
3. En el túnel, en **Public hostname**, añade: subdominio `youtube`, dominio `findaihome.com`,
   tipo `HTTP` y URL `localhost:8765` (ejecutable) o `web:8000` (Docker).
4. Abre `https://youtube.findaihome.com` desde cualquier móvil u ordenador. Funciona mientras tu
   ordenador esté encendido con el servidor abierto.

Todas las descargas salen por tu conexión. Si no quieres que la use cualquiera, protégela en
Cloudflare con **Zero Trust → Access → Applications** (solo entran los correos que elijas) o,
con Docker, pon una clave en `DWB_CLAVE`.
