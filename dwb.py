"""Descargador de videos de YouTube basado en yt-dlp.

Uso:
    python dwb.py <url> [-o carpeta] [--audio] [--calidad 720] [--cookies cookies.txt]
"""
import argparse
import shutil
import sys

try:
    from yt_dlp import YoutubeDL
except ImportError:
    sys.exit("Falta yt-dlp. Instálalo con: pip install yt-dlp")


def build_options(output_dir: str, audio_only: bool, max_height: int | None,
                  cookies: str | None = None, cookies_browser: str | None = None) -> dict:
    has_ffmpeg = shutil.which("ffmpeg") is not None
    opts = {
        "outtmpl": f"{output_dir}/%(title)s [%(id)s].%(ext)s",
        "noplaylist": True,
        "noprogress": True,
        "progress_hooks": [_progress],
    }
    # YouTube pide iniciar sesión a algunas IPs (servidores, VPN): las cookies lo evitan.
    if cookies:
        opts["cookiefile"] = cookies
    if cookies_browser:
        opts["cookiesfrombrowser"] = (cookies_browser,)

    if audio_only:
        opts["format"] = "bestaudio/best"
        if has_ffmpeg:
            opts["postprocessors"] = [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
            ]
    elif has_ffmpeg:
        # Mejor video + mejor audio, unidos en un mp4.
        height = f"[height<={max_height}]" if max_height else ""
        opts["format"] = f"bestvideo{height}+bestaudio/best{height}"
        opts["merge_output_format"] = "mp4"
    else:
        # Sin ffmpeg no se pueden unir pistas: usa un formato que ya traiga ambas.
        height = f"[height<={max_height}]" if max_height else ""
        opts["format"] = f"best{height}[acodec!=none][vcodec!=none]/best"

    return opts


def _progress(d: dict) -> None:
    if d["status"] == "downloading":
        print(f"\r  {d.get('_percent_str', '').strip()} de {d.get('_total_bytes_str', '?').strip()}"
              f" a {d.get('_speed_str', '?').strip()}", end="", flush=True)
    elif d["status"] == "finished":
        print(f"\n  Descargado: {d['filename']}")


def download(url: str, output_dir: str = "descargas", audio_only: bool = False,
             max_height: int | None = None, cookies: str | None = None,
             cookies_browser: str | None = None) -> str:
    opts = build_options(output_dir, audio_only, max_height, cookies, cookies_browser)
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        print(f"Título: {info.get('title')}")
        print(f"Duración: {info.get('duration_string') or '?'}")
        return ydl.prepare_filename(info)


def main() -> None:
    parser = argparse.ArgumentParser(description="Descarga videos de YouTube.")
    parser.add_argument("url", help="URL del video de YouTube")
    parser.add_argument("-o", "--output", default="descargas", help="carpeta de destino")
    parser.add_argument("--audio", action="store_true", help="descargar solo el audio (mp3)")
    parser.add_argument("--calidad", type=int, help="altura máxima del video, p. ej. 720")
    parser.add_argument("--cookies", help="archivo cookies.txt (formato Netscape) de YouTube")
    parser.add_argument("--cookies-navegador", metavar="NAVEGADOR",
                        help="leer cookies del navegador: chrome, firefox, edge, safari...")
    args = parser.parse_args()

    try:
        download(args.url, args.output, args.audio, args.calidad,
                 args.cookies, args.cookies_navegador)
    except Exception as exc:
        sys.exit(f"Error al descargar: {exc}")


if __name__ == "__main__":
    main()
