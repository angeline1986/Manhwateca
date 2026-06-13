#!/bin/bash
cd "$(dirname "$0")" || exit 1
python server.py --open
