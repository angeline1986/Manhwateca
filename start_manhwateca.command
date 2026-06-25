#!/bin/bash
cd "$(dirname "$0")" || exit 1

if [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
elif [ -x "/opt/homebrew/Caskroom/miniconda/base/bin/python" ]; then
  PYTHON="/opt/homebrew/Caskroom/miniconda/base/bin/python"
else
  PYTHON="python"
fi

"$PYTHON" server.py --open
