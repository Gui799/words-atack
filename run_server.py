"""Servidor local com Waitress, sem depurador. CTRL+C encerra."""
import os
from waitress import serve
from server.app import create_app

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    print(f"Words Atack: http://{host}:{port}", flush=True)
    serve(create_app(), host=host, port=port, threads=4)
