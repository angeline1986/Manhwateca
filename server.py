import argparse
import os
import sys
import threading
import webbrowser
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent


def _ensure_project_python():
    if os.environ.get("MANHWATECA_PYTHON_BOOTSTRAPPED") == "1":
        return

    candidates = [
        PROJECT_ROOT / ".venv/bin/python",
        Path("/opt/homebrew/Caskroom/miniconda/base/bin/python"),
    ]
    current = Path(sys.executable).resolve()
    for candidate in candidates:
        if candidate.is_file() and candidate.resolve() != current:
            os.environ["MANHWATECA_PYTHON_BOOTSTRAPPED"] = "1"
            os.execv(str(candidate), [str(candidate), str(PROJECT_ROOT / "server.py"), *sys.argv[1:]])


_ensure_project_python()

from dotenv import load_dotenv

from manhwateca.webapp.server import create_server


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
