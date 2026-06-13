def csv_menu(api_color, exit_color, reset_color, saved, details, run_command):
    while True:
        print("\nMANGAUPDATES: DADOS E CSV\n")
        print(f"  {api_color}1. 📄 Atualizar CSV com dados salvos{reset_color}")
        print("     Usa somente o cache local. Não consulta a API.\n")
        print(f"  {api_color}2. 🌐 Consultar próximo lote na API{reset_color}")
        print("     Busca detalhes de até 10 IDs e atualiza o CSV.\n")
        print(f"  {exit_color}0. ↩ Voltar{reset_color}")
        option = input("\nEscolha uma opção: ").strip()
        if option == "1":
            return run_command(saved)
        if option == "2":
            if not run_command(details):
                return False
            return run_command(saved)
        if option == "0":
            return True
        print("\nOpção inválida. Escolha 0, 1 ou 2.")


def id_menu(
    api_color,
    exit_color,
    reset_color,
    id_command,
    refresh_command,
    run_command,
):
    while True:
        _print_id_options(api_color, exit_color, reset_color)
        option = input("\nEscolha uma opção: ").strip()
        if option == "1":
            return _search_ids(id_command, run_command)
        if option == "2":
            return run_command(refresh_command)
        if option == "3":
            return run_command(["scripts/id_review.py"])
        if option == "4":
            return _import_decisions(run_command)
        if option == "0":
            return True
        print("\nOpção inválida. Escolha 0, 1, 2, 3 ou 4.")


def _print_id_options(api_color, exit_color, reset_color):
    print("\nMANGAUPDATES: LOCALIZAR E REVISAR IDS\n")
    print(f"  {api_color}1. 🔎 Buscar próximo lote de IDs{reset_color}")
    print("     Consulta até 10 obras e atualiza buscaIds.json.\n")
    print(f"  {api_color}2. ♻️ Atualizar candidatos incompletos{reset_color}")
    print("     Atualiza link, descrição e gênero BL de candidatos antigos.\n")
    print(f"  {api_color}3. 📋 Gerar página de revisão dos IDs{reset_color}")
    print("     Compara candidatos marcados como Revisar em um relatório HTML.\n")
    print(f"  {api_color}4. 📥 Importar decisões da revisão{reset_color}")
    print("     Valida o JSON exportado e atualiza buscaIds.json com backup.\n")
    print(f"  {exit_color}0. ↩ Voltar{reset_color}")


def _search_ids(id_command, run_command):
    print("\nInforme as letras iniciais que deseja consultar.")
    print("Exemplos: A, ABC ou 0-9. Pressione Enter para todas.")
    initials = input("Letras: ").strip()
    command = list(id_command)
    if initials:
        command.extend(["--initials", initials])
    return run_command(command)


def _import_decisions(run_command):
    default_path = "reports/integrations/mangaupdates_id_decisions.json"
    print("\nInforme o caminho do JSON exportado pelo relatório.")
    print(f"Pressione Enter para usar: {default_path}")
    path = input("Arquivo: ").strip() or default_path
    return run_command(["scripts/id_review.py", "--import-decisions", path])
