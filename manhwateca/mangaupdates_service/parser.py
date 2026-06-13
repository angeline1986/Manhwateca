import argparse
from pathlib import Path


def build_parser():
    parser = argparse.ArgumentParser(
        description="Consulta e armazena metadados confirmados do MangaUpdates."
    )
    parser.add_argument("--search", help="Busca candidatos sem alterar o cache.")
    parser.add_argument(
        "--generate-csv",
        action="store_true",
        help="Executa busca e detalhe para gerar o CSV de importação.",
    )
    parser.add_argument(
        "--update-csv-from-ids",
        type=Path,
        help="Atualiza o CSV usando os IDs confirmados no JSON informado.",
    )
    parser.add_argument(
        "--fetch-details-from-ids",
        type=Path,
        help="Consulta detalhes dos IDs confirmados e atualiza o cache.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=3.0,
        help="Intervalo entre requisições, em segundos (padrão: 3).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limita a quantidade de obras processadas nesta execução.",
    )
    parser.add_argument(
        "--fill-ids",
        type=Path,
        help="Lê um JSON de obras e preenche IDs/candidatos da busca.",
    )
    parser.add_argument(
        "--per-page",
        type=int,
        default=10,
        help="Quantidade de candidatos por busca de ID (padrão: 10).",
    )
    parser.add_argument(
        "--retry-review",
        action="store_true",
        help="Reprocessa itens marcados como Revisar.",
    )
    parser.add_argument(
        "--initials",
        default="",
        help="Filtra obras pelas letras iniciais, por exemplo A, ABC ou 0-9.",
    )
    parser.add_argument(
        "--refresh-incomplete-candidates",
        type=Path,
        help="Atualiza candidatos sem URL, descrição ou classificação BL.",
    )
    return parser
