from pathlib import Path

from manhwateca.application.notes import register_review_note


def save_review_note(project_root, note):
    project_root = Path(project_root)
    path = project_root / "reports/reviews/review_notes.md"
    return register_review_note(path, project_root, (note or "").strip())
