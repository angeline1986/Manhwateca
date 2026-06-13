import argparse
import threading
import webbrowser
from pathlib import Path

from dotenv import load_dotenv

from manhwateca.webapp.server import create_server


PROJECT_ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(
        description="Inicia a aplicação web local da Manhwateca."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--open",
        action="store_true",
        help="Abre a aplicação no navegador padrão.",
    )
    args = parser.parse_args()
    load_dotenv(PROJECT_ROOT / ".env")
    server = create_server(PROJECT_ROOT, args.host, args.port)
    url = f"http://{args.host}:{args.port}"
    print(f"Manhwateca disponível em {url}")
    if args.open:
        threading.Timer(0.5, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
