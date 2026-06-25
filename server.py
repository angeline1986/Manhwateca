import argparse
import importlib.util
import os
import sys
import threading
import webbrowser
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
OFFICIAL_PYTHON = PROJECT_ROOT / ".venv/bin/python"


def _ensure_official_python():
    current = Path(sys.executable)
    if OFFICIAL_PYTHON.exists() and current.samefile(OFFICIAL_PYTHON):
        return

    message = f"""
Runtime Python inválido.

Use o inicializador oficial:

./start_manhwateca.command

Runtime esperado:
{OFFICIAL_PYTHON}

Runtime atual:
{current}
"""
    raise SystemExit(message.strip())


def _ensure_dependencies():
    missing = [
        module
        for module in ("dotenv", "psycopg")
        if importlib.util.find_spec(module) is None
    ]
    if not missing:
        return

    message = f"""
Ambiente Python incompleto.

Módulos ausentes: {", ".join(missing)}

Execute:

.venv/bin/pip install -r requirements.txt
"""
    raise SystemExit(message.strip())


_ensure_official_python()
_ensure_dependencies()

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
