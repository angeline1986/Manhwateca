def run_cli(args, operations, paths):
    _validate_args(args)

    if args.search:
        _print_search(operations["search_series"](args.search))
        return
    if args.fill_ids:
        _fill_ids(args, operations)
        return
    if args.refresh_incomplete_candidates:
        _refresh_candidates(args, operations)
        return
    if args.update_csv_from_ids:
        _update_csv(args, operations, paths)
        return
    if args.fetch_details_from_ids:
        _fetch_details(args, operations)
        return
    if args.generate_csv:
        _generate_csv(args, operations, paths)
        return

    operations["refresh_cache"]()
    print(f"Cache atualizado: {paths['cache']}")


def _validate_args(args):
    if args.delay < 0:
        raise SystemExit("--delay não pode ser negativo.")
    if args.per_page < 1:
        raise SystemExit("--per-page deve ser maior que zero.")


def _print_search(response):
    for result in response.get("results", []):
        record = result.get("record", {})
        print(
            f"{record.get('series_id')} | {record.get('title')} | "
            f"{record.get('type')} | {record.get('year')}"
        )


def _fill_ids(args, operations):
    items, processed = operations["fill_ids"](
        args.fill_ids,
        delay=args.delay,
        limit=args.limit,
        per_page=args.per_page,
        retry_review=args.retry_review,
        initials=args.initials,
    )
    confirmed = sum(bool(item.get("ID")) for item in items)
    review = sum(item.get("Status") == "Revisar" for item in items)
    pending = len(items) - confirmed - review
    print()
    print(f"Arquivo atualizado: {args.fill_ids}")
    print(f"Processadas nesta execução: {processed}")
    print(f"IDs confirmados: {confirmed}")
    print(f"Para revisão: {review}")
    print(f"Pendentes: {pending}")


def _refresh_candidates(args, operations):
    processed, pending = operations["refresh_candidates"](
        args.refresh_incomplete_candidates,
        delay=args.delay,
        limit=args.limit,
        per_page=args.per_page,
    )
    print()
    print(f"Obras atualizadas nesta execução: {processed}")
    print(f"Obras antigas para próximos lotes: {pending}")


def _update_csv(args, operations, paths):
    updated, checked, uncached, missing = operations["update_csv"](
        args.update_csv_from_ids,
        delay=args.delay,
        limit=args.limit,
    )
    print()
    print(f"CSV atualizado: {paths['csv']}")
    print(f"Obras verificadas: {checked}")
    print(f"Linhas realmente alteradas: {updated}")
    print(f"Aguardando consulta de detalhes na API: {len(uncached)}")
    for name in uncached:
        print(f"- {name}")
    if uncached:
        print()
        print(
            "Próximo passo: use a opção 5.2 para consultar "
            "o próximo lote na API."
        )
    print(f"Obras realmente ausentes no CSV: {len(missing)}")
    for name in missing:
        print(f"- {name}")


def _fetch_details(args, operations):
    processed, pending = operations["fetch_details"](
        args.fetch_details_from_ids,
        delay=args.delay,
        limit=args.limit,
        force_refresh=getattr(args, "force_refresh", False),
    )
    print()
    print(f"Detalhes consultados nesta execução: {processed}")
    print(f"IDs confirmados ainda pendentes: {pending}")


def _generate_csv(args, operations, paths):
    mangas = operations["load_catalog"]()
    progress, cache = operations["enrich_catalog"](
        mangas,
        delay=args.delay,
        limit=args.limit,
    )
    operations["write_csv"](mangas, cache, progress)
    completed = sum(1 for manga in mangas if manga["nome"] in progress)
    print(f"CSV gerado: {paths['csv']}")
    print(f"Obras processadas: {completed}/{len(mangas)}")
    print(f"Pendentes para outra execução: {len(mangas) - completed}")
