"""Genera el ejecutable DescargadorYouTube (para el sistema en el que se ejecute este script).

    pip install -r requirements.txt pyinstaller imageio-ffmpeg
    python empaquetar.py        # el resultado queda en dist/

Incluye ffmpeg y deno, así que el ejecutable no necesita nada instalado.
"""
import os
import shutil
import sys

import deno
import imageio_ffmpeg
import PyInstaller.__main__

os.makedirs("build", exist_ok=True)
# yt-dlp busca un programa que se llame exactamente "ffmpeg".
ffmpeg = shutil.copy(imageio_ffmpeg.get_ffmpeg_exe(),
                     os.path.join("build", "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"))

PyInstaller.__main__.run([
    "web.py",
    "--onefile",
    "--name", "DescargadorYouTube",
    "--add-binary", f"{ffmpeg}{os.pathsep}.",
    "--add-binary", f"{deno.find_deno_bin()}{os.pathsep}.",
    "--noconfirm",
])
