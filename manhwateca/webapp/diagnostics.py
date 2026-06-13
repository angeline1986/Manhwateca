import os
import sys
from pathlib import Path


REQUIRED_FILES = [
    Path("web/index.html"),
    Path("data/mangas.json"),
    Path("reports/integrations/manhwateca_import.csv"),
]
WRITABLE_DIRS = [
    Path("data"),
    Path("reports"),
    Path("config"),
]


def build_diagnostics(project_root):
    root = Path(project_root)
    manga_root = os.getenv("MANGA_ROOT", "").strip()
    checks = [
        _check(
            "Python",
            sys.version_info >= (3, 10),
            f"{sys.version_info.major}.{sys.version_info.minor}",
        ),
        _check(".env", (root / ".env").is_file(), "Configuração local"),
        _check(
            "MANGA_ROOT",
            bool(manga_root) and Path(manga_root).is_dir(),
            "Biblioteca acessível" if manga_root else "Não configurado",
        ),
        _check(
            "Notion",
            all(os.getenv(name, "").strip() for name in (
                "NOTION_TOKEN", "NOTION_DATABASE_ID"
            )),
            "Credenciais configuradas",
        ),
    ]
    checks.extend(
        _check(str(path), (root / path).is_file(), "Arquivo disponível")
        for path in REQUIRED_FILES
    )
    checks.extend(
        _check(
            f"Escrita em {path}",
            _writable(root / path),
            "Diretório gravável",
        )
        for path in WRITABLE_DIRS
    )
    return {
        "ready": all(check["ok"] for check in checks),
        "checks": checks,
    }


def _writable(path):
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".manhwateca-write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return True
    except OSError:
        return False


def _check(name, ok, detail):
    return {"name": name, "ok": bool(ok), "detail": detail}
