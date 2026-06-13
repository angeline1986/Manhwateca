import argparse
from pathlib import Path


def build_parser(default_ids_file):
    parser = argparse.ArgumentParser(
        description="Gera o relatório ou importa decisões de IDs."
    )
    parser.add_argument(
        "--import-decisions",
        type=Path,
        help="Importa o JSON exportado pela página de revisão.",
    )
    parser.add_argument(
        "--ids-file",
        type=Path,
        default=default_ids_file,
        help="Arquivo buscaIds.json que será lido ou atualizado.",
    )
    return parser
