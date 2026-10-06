FROM python:3.13-slim

# ffmpeg une video y audio (deno, que yt-dlp necesita para YouTube, llega con pip).
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY dwb.py web.py ./

# Sin --bind, gunicorn escucha en 0.0.0.0:$PORT.
ENV PORT=8000
CMD ["gunicorn", "--threads", "4", "web:app"]
