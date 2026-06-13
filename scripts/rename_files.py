import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from manhwateca.file_normalizer import workflow


if __name__ == "__main__":
    args = workflow.parse_args()
    if not workflow.main(apply=args.apply):
        raise SystemExit(1)
else:
    sys.modules[__name__] = workflow
