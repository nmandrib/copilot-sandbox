FROM python:3.13-slim

# ffmpeg une video y audio; deno lo usa yt-dlp para resolver los videos de YouTube.
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*
COPY --from=denoland/deno:bin /deno /usr/local/bin/deno

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY dwb.py web.py ./

ENV PORT=8000
CMD gunicorn -b 0.0.0.0:$PORT --threads 4 --timeout 600 web:app
