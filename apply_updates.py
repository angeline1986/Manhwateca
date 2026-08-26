#!/usr/bin/env python3
from pathlib import Path
import shutil, sys, re

ROOT = Path.cwd()
JS = ROOT / 'web/js/pages/trackingPage.js'
CSS = ROOT / 'web/css/pages/releases.css'

for p in (JS, CSS):
    if not p.exists():
        raise SystemExit(f'ERRO: arquivo não encontrado: {p}\nExecute este script na raiz do projeto Manhwateca.')

backup = ROOT / '.tracking_patch_backup_20260824'
backup.mkdir(exist_ok=True)
shutil.copy2(JS, backup / 'trackingPage.js')
shutil.copy2(CSS, backup / 'releases.css')

js = JS.read_text(encoding='utf-8')
original_js = js

# 1) Histórico: somente os 6 lançamentos mais recentes.
js = re.sub(
    r'const rows = history\.filter\(row => Number\(row\.manga_id\) === Number\(item\.manga_id\)\);',
    'const rows = history.filter(row => Number(row.manga_id) === Number(item.manga_id)).slice(0, 6);',
    js,
)
js = re.sub(
    r'getReleases\(\{ manga_id: selectedMangaId, days: 365, per_page: \d+ \}\)',
    'getReleases({ manga_id: selectedMangaId, days: 365, per_page: 6 })',
    js,
)

# Remove eventual botão "Ver mais" criado por uma versão intermediária.
js = re.sub(r'\n\s*<button[^>]*data-tracking-history-more[^>]*>.*?</button>', '', js, flags=re.S)
js = re.sub(r'\n\s*\$\{[^\n]*Ver mais[^\n]*\}', '', js)

# 2) A verificação geral pode durar mais de 30s. Não recarregar a página com dados antigos.
js = js.replace(
    'for (let index = 0; index < 30; index += 1) {',
    'for (let index = 0; index < 600; index += 1) {'
)
old = '''    if (task && !["queued", "running"].includes(task.status)) return;\n    await new Promise(resolve => setTimeout(resolve, 1000));\n  }\n}'''
new = '''    if (task && !["queued", "running"].includes(task.status)) {\n      if (task.status === "failed") {\n        throw new Error(task.error || task.message || "A verificação de lançamentos falhou.");\n      }\n      return task;\n    }\n    await new Promise(resolve => setTimeout(resolve, 1000));\n  }\n  throw new Error("A verificação ainda não terminou após 10 minutos.");\n}'''
if old in js:
    js = js.replace(old, new)

if js == original_js:
    print('AVISO: nenhuma substituição JS foi necessária; o arquivo pode já conter parte dos ajustes.')
else:
    JS.write_text(js, encoding='utf-8')

css = CSS.read_text(encoding='utf-8')
marker = '/* TRACKING_STANDARD_GEOMETRY_20260824 */'
block = r'''

/* TRACKING_STANDARD_GEOMETRY_20260824
   Acompanhamento segue o mesmo enquadramento externo aprovado em Organização. */
.page-container:has(#page-tracking.active) {
  padding: 16px;
}

#page-tracking {
  width: min(1180px, 100%);
  margin: 0 auto;
}

#page-tracking .tracking-releases-panel,
#page-tracking .tracking-works-panel {
  width: 100%;
}

/* Evita que o grid distribua altura ociosa entre os blocos do detalhe.
   Assim os cards mantêm geometria estável mesmo sem lançamento/verificação. */
#page-tracking .tracking-work-detail {
  align-content: start;
}

#page-tracking .tracking-detail-grid {
  align-items: stretch;
}

#page-tracking .tracking-detail-grid article {
  min-height: 66px;
  align-content: start;
}

/* Fila/detalhe seguem a proporção estrutural já consolidada na Organização. */
#page-tracking .tracking-workspace {
  grid-template-columns: 340px minmax(0, 1fr);
  gap: 0;
  align-items: stretch;
}

#page-tracking .tracking-work-list {
  min-width: 340px;
  width: 340px;
}

/* Mantém respiro consistente entre as duas grandes seções. */
#page-tracking .tracking-releases-panel + .tracking-works-panel {
  margin-top: 16px;
}

@media (max-width: 900px) {
  #page-tracking .tracking-workspace {
    grid-template-columns: 1fr;
  }
  #page-tracking .tracking-work-list {
    min-width: 0;
    width: auto;
  }
}
'''
if marker not in css:
    CSS.write_text(css.rstrip() + block + '\n', encoding='utf-8')
else:
    print('AVISO: bloco CSS já existe; não foi duplicado.')

print('OK: ajustes aplicados.')
print(f'Backup: {backup}')
print('Arquivos tratados:')
print(f' - {JS}')
print(f' - {CSS}')
