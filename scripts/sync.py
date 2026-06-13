import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from manhwateca.notion_sync import catalog_workflow


if __name__ == "__main__":
    catalog_workflow.main()
else:
    sys.modules[__name__] = catalog_workflow
