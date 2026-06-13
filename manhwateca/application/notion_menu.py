def show(
    title_color,
    exit_color,
    reset_color,
    run_command,
    confirm_sync_batch,
):
    while True:
        print("\nSINCRONIZAÇÃO COM NOTION\n")
        print(f"  {title_color}1. 🔄 Simular próximo lote no Notion{reset_color}")
        print("     Mostra as próximas 25 obras e quantas ainda ficarão pendentes.\n")
        print(f"  {title_color}2. ✅ Importar próximo lote no Notion{reset_color}")
        print("     Cria até 25 obras ausentes sem duplicar as já importadas.\n")
        print(f"  {title_color}3. 🌐 Atualizar dados do MangaUpdates{reset_color}")
        print("     Consulta somente as obras com ID confirmado na configuração.\n")
        print(f"  {title_color}4. ♻️ Atualizar páginas já importadas{reset_color}")
        print("     Atualiza campos e contagens sem criar novas páginas.\n")
        print(f"  {exit_color}0. ↩ Voltar{reset_color}")
        option = input("\nEscolha uma opção: ").strip()
        if option == "1":
            return run_command(
                ["scripts/sync.py", "--simulate-batch", "--batch-size", "25"]
            )
        if option == "2":
            return confirm_sync_batch()
        if option == "3":
            if not run_command(["scripts/mangaupdates.py"]):
                return False
            return run_command(["scripts/scan.py"])
        if option == "4":
            return run_command(["scripts/sync.py", "--update-existing"])
        if option == "0":
            return True
        print("\nOpção inválida. Escolha 0, 1, 2, 3 ou 4.")
