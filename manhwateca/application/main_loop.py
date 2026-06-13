def run(banner, menu, actions, pause):
    while True:
        print(banner)
        print(menu)
        option = input("Opção: ").strip()
        if option == "0":
            print("\nAté a próxima.")
            return
        action = actions.get(option)
        if action is None:
            print("\nOpção inválida. Escolha um número de 0 a 9.")
            pause()
            continue
        action()
        pause()
