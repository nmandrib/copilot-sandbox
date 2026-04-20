import os
import time

MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
TIMEOUT = int(os.getenv("TIMEOUT", "30"))
CONNECTION_POOL_SIZE = int(os.getenv("CONNECTION_POOL_SIZE", "10"))


def connect(host: str, port: int = 5432):
    """
    Connect to a database host and port with retry logic.

    Args:
        host (str): The database host to connect to.
        port (int, optional): The database port to connect to. Defaults to 5432.

    Returns:
        dict: A dictionary containing the host, port, and status of the connection.

    Raises:
        RuntimeError: If the connection fails after max retries.
    """
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