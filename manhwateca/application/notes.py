def register_review_note(path, project_root, note):
    if not note:
        print("\nNenhuma observação registrada.")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("# Ajustes pendentes da revisão\n\n", encoding="utf-8")
    with path.open("a", encoding="utf-8") as file:
        file.write(f"- [ ] {note}\n")
    try:
        display_path = path.relative_to(project_root)
    except ValueError:
        display_path = path
    print(f"\nObservação registrada em {display_path}.")
    return True
