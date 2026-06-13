def standardization_menu(
    title_color,
    exit_color,
    reset_color,
    generate_reports,
    apply_file_names,
    register_review_note,
):
    while True:
        print("\nPADRONIZAÇÃO DOS ARQUIVOS\n")
        print(f"  {title_color}1. 📄 Verificar organização e nomes{reset_color}")
        print("     Gera relatórios HTML com pastas e arquivos a padronizar.")
        print("     Não altera a biblioteca.\n")
        print(f"  {title_color}2. ✏️ Aplicar padronização dos arquivos{reset_color}")
        print("     Renomeia os capítulos conforme a prévia após confirmação.\n")
        print(f"  {title_color}3. 📝 Registrar ajustes da revisão{reset_color}")
        print("     Salva críticas e correções pendentes para revisão manual.\n")
        print(f"  {exit_color}0. ↩ Voltar{reset_color}")
        option = input("\nEscolha uma opção: ").strip()
        if option == "1":
            return generate_reports()
        if option == "2":
            return apply_file_names()
        if option == "3":
            return register_review_note()
        if option == "0":
            return True
        print("\nOpção inválida. Escolha 0, 1, 2 ou 3.")


def organization_menu(
    title_color,
    exit_color,
    reset_color,
    apply_organization,
):
    while True:
        print("\nORGANIZAÇÃO ALFABÉTICA\n")
        print(f"  {title_color}1. 📚 Aplicar organização alfabética{reset_color}")
        print("     Move as pastas para os grupos alfabéticos após confirmação.\n")
        print(f"  {exit_color}0. ↩ Voltar{reset_color}")
        option = input("\nEscolha uma opção: ").strip()
        if option == "1":
            return apply_organization()
        if option == "0":
            return True
        print("\nOpção inválida. Escolha 0 ou 1.")
