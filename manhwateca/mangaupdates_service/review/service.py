from manhwateca.reporting.files import write_report


def generate_report(
    ids_path,
    report_path,
    csv_path,
    load_items,
    consolidate_items,
    render_report,
):
    items = load_items(ids_path)
    review_items = consolidate_items(items, csv_path=csv_path)
    write_report(report_path, render_report(items, csv_path=csv_path))
    print(f"Relatório gerado: {report_path}")
    print(f"Obras aguardando revisão: {len(review_items)}")


def run_cli(args, operations):
    if not args.import_decisions:
        operations["generate_report"](ids_path=args.ids_file)
        return

    applied, rejected, backup = operations["import_decisions"](
        args.import_decisions,
        ids_path=args.ids_file,
    )
    print(f"Decisões aplicadas: {len(applied)}")
    for name in applied:
        print(f"- {name}")
    print(f"Decisões rejeitadas: {len(rejected)}")
    for reason in rejected:
        print(f"- {reason}")
    if backup:
        print(f"Backup criado: {backup}")

    pending_details = operations["count_pending_details"](
        operations["load_items"](args.ids_file)
    )
    if pending_details:
        print()
        print(
            f"Próximo passo: {pending_details} ID(s) confirmado(s) ainda "
            "não possuem detalhes."
        )
        print(
            "Use a opção 5.2 - Consultar próximo lote na API. "
            "Ela também atualizará o CSV."
        )
    operations["generate_report"](ids_path=args.ids_file)
