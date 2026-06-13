import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from manhwateca.catalog import chapter_audit


if __name__ == "__main__":
    chapter_audit.main()
else:
    sys.modules[__name__] = chapter_audit
