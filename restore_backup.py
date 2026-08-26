#!/usr/bin/env python3
from pathlib import Path
import shutil
root = Path.cwd()
backup = root / '.tracking_patch_backup_20260824'
files = {
    backup / 'trackingPage.js': root / 'web/js/pages/trackingPage.js',
    backup / 'releases.css': root / 'web/css/pages/releases.css',
}
for src, dst in files.items():
    if not src.exists():
        raise SystemExit(f'Backup não encontrado: {src}')
    shutil.copy2(src, dst)
print('Backup restaurado com sucesso.')
