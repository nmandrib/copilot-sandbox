import os
import time

MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
TIMEOUT = int(os.getenv("TIMEOUT", "30"))
CONNECTION_POOL_SIZE = int(os.getenv("CONNECTION_POOL_SIZE", "10"))


def connect(host: str, port: int = 5432):
    # Validate port
    if port < 1 or port > 65535:
        raise ValueError(f"Port must be between 1 and 65535 (inclusive). Received: {port}")

    retries = 0
    while retries < MAX_RETRIES:
        try:
            # TODO: replace with real connection
            time.sleep(0.1)
            return {"host": host, "port": port, "status": "connected"}
        except Exception as exc:
            retries += 1
            if retries >= MAX_RETRIES:
                raise RuntimeError(f"Failed to connect after {MAX_RETRIES} retries") from exc


def main():
    conn = connect(os.getenv("DB_HOST", "localhost"))
    print(f"Connected: {conn}")


if __name__ == "__main__":
    main()
