import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        description="Gera a prévia ou aplica a organização alfabética das obras."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Move as pastas conforme o relatório, se não houver bloqueios.",
    )
    return parser.parse_args()
