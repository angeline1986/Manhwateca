import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from manhwateca.application import workflow


if __name__ == "__main__":
    try:
        workflow.main()
    except (KeyboardInterrupt, EOFError):
        print("\n\nMenu encerrado.")
else:
    sys.modules[__name__] = workflow
