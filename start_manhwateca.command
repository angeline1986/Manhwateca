#!/bin/bash
cd "$(dirname "$0")" || exit 1

PYTHON=".venv/bin/python"

if [ ! -x "$PYTHON" ]; then
  cat <<'EOF'
Ambiente virtual não encontrado.

Execute:

python -m venv .venv
.venv/bin/pip install -r requirements.txt
EOF
  exit 1
fi

"$PYTHON" - <<'PY'
import sys

missing = []
for module in ("dotenv", "psycopg"):
    try:
        __import__(module)
    except ModuleNotFoundError:
        missing.append(module)

if missing:
    print("Ambiente Python incompleto.")
    print()
    print("Módulos ausentes: " + ", ".join(missing))
    print()
    print("Execute:")
    print()
    print(".venv/bin/pip install -r requirements.txt")
    sys.exit(1)
PY

if [ $? -ne 0 ]; then
  exit 1
fi

"$PYTHON" server.py --open
