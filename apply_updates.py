#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_ROOT = ROOT / "reports" / "patch_backups" / f"queue_capsules_{STAMP}"

FILES = {
    "docs": ROOT / "docs" / "frontend_page_standard.md",
    "organization_js": ROOT / "web" / "js" / "pages" / "organizationPage.js",
    "organization_css": ROOT / "web" / "css" / "pages" / "organization.css",
    "tracking_js": ROOT / "web" / "js" / "pages" / "trackingPage.js",
    "tracking_css": ROOT / "web" / "css" / "pages" / "releases.css",
    "notion_js": ROOT / "web" / "js" / "flows" / "syncNotionPanel.js",
    "flows_css": ROOT / "web" / "css" / "pages" / "flows-journey.css",
}

class PatchError(RuntimeError):
    pass

def read(path: Path) -> str:
    if not path.is_file():
        raise PatchError(f"Arquivo não encontrado: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")

def backup(paths: list[Path]) -> None:
    for path in paths:
        target = BACKUP_ROOT / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)

def replace_once(text: str, old: str, new: str, label: str, *, already: str | None = None) -> str:
    if already and already in text:
        print(f"[SKIP] {label}: já aplicado.")
        return text
    count = text.count(old)
    if count != 1:
        raise PatchError(
            f"{label}: trecho esperado encontrado {count} vez(es). "
            "Patch interrompido para não alterar código inesperado."
        )
    print(f"[OK] {label}")
    return text.replace(old, new, 1)

def append_once(text: str, marker: str, block: str, label: str) -> str:
    if marker in text:
        print(f"[SKIP] {label}: já aplicado.")
        return text
    print(f"[OK] {label}")
    return text.rstrip() + "\n\n" + block.strip() + "\n"

def patch_docs(text: str) -> str:
    block = r'''
## Padrão visual dos itens de fila — Cápsulas leves

<!-- QUEUE_CAPSULES_STANDARD_20260827 -->

Para telas do arquétipo **Fila + detalhe + capa**, o padrão visual oficial dos itens
da coluna esquerda é **Cápsulas leves**.

A fila tem uma responsabilidade simples: **localizar e selecionar a obra**.
Ela não deve explicar o estado da obra.

### Conteúdo permitido na fila

Cada item pode conter apenas:

- controle de seleção quando a etapa trabalhar com seleção em lote;
- interação própria da entidade quando indispensável, como a estrela de Favorito em
  Acompanhamento;
- **nome da obra**;
- affordance discreto de navegação, como `›`, sem texto adicional.

Não exiba ao redor ou abaixo do nome:

- ID;
- status;
- data;
- quantidade de divergências;
- estado de sincronização;
- caminho;
- grupo;
- capítulo;
- mensagens operacionais;
- qualquer outro metadado.

Essas informações pertencem ao **painel de detalhe à direita**.

### Aparência da Cápsula leve

O item deve manter o estilo Rose Edition já existente, sem introduzir nova paleta:

- altura mínima de referência: **48px**;
- raio de referência: **10–11px**;
- fundo em repouso muito sutil, próximo ao fundo da fila;
- borda transparente ou extremamente discreta em repouso;
- `gap` vertical de aproximadamente **6–7px** entre itens;
- nome com peso moderado, sem negrito excessivo;
- `overflow: hidden`, `text-overflow: ellipsis` e `white-space: nowrap` para nomes longos.

#### Hover

No hover:

- a cápsula pode deslocar-se horizontalmente em aproximadamente **2px**;
- fundo passa para o painel branco;
- borda Rose suave aparece;
- o `›` pode surgir com transição curta.

O movimento deve ser pequeno e não pode causar reflow da fila.

#### Item aberto no detalhe

A obra atualmente aberta no painel direito deve receber:

- borda Rose;
- fundo claro;
- sombra muito sutil;
- `›` visível;
- nenhuma informação textual adicional.

O estado de **item aberto** é diferente do estado de **checkbox marcado**.
Marcar um checkbox para ação em lote não deve alterar qual obra está aberta no detalhe.

### Aplicação no projeto

Este padrão deve ser compartilhado por filas equivalentes, incluindo:

- **Organização v2**;
- **Acompanhamento > Busca e favoritas**;
- **Fluxos > Sincronizar Notion**.

As telas continuam livres para especializar o conteúdo do painel direito, mas a fila
de obras deve manter a mesma linguagem de seleção e navegação.

### Checklist específico da fila

- [ ] A fila mostra somente interação indispensável + nome da obra.
- [ ] Nenhum status, ID ou metadado aparece abaixo do nome.
- [ ] Informações operacionais estão no painel direito.
- [ ] Hover usa acabamento leve e deslocamento de no máximo 2px.
- [ ] Item aberto possui destaque Rose sem acrescentar texto.
- [ ] Checkbox marcado e item aberto continuam estados independentes.
- [ ] Nomes longos são truncados de forma previsível.
- [ ] `flow-pager` continua sendo usado quando a fila é paginada.
'''
    return append_once(
        text,
        "QUEUE_CAPSULES_STANDARD_20260827",
        block,
        "Documentar Cápsulas leves como padrão oficial de fila",
    )

def patch_organization_js(text: str) -> str:
    old = '''          <h4>${escapeHtml(item.title)}</h4>
        </article>'''
    new = '''          <h4 title="${escapeHtml(item.title)}">${escapeHtml(item.title)}</h4>
          <span class="organization-queue-arrow" aria-hidden="true">›</span>
        </article>'''
    return replace_once(
        text, old, new,
        "Organização v2: adicionar affordance discreto à fila",
        already='class="organization-queue-arrow"',
    )

def patch_tracking_js(text: str) -> str:
    old = '''        <span>${starButton(item)}</span>
        <strong>${escapeHtml(item.title || "Obra sem título")}</strong>
      </article>'''
    new = '''        <span>${starButton(item)}</span>
        <strong title="${escapeHtml(item.title || "Obra sem título")}">${escapeHtml(item.title || "Obra sem título")}</strong>
        <span class="tracking-queue-arrow" aria-hidden="true">›</span>
      </article>'''
    return replace_once(
        text, old, new,
        "Acompanhamento: adequar item da fila ao padrão Cápsulas leves",
        already='class="tracking-queue-arrow"',
    )

def patch_notion_js(text: str) -> str:
    old = '''      <input type="checkbox" data-notion-sync-choice data-notion-sync-work-id="${escapeHtml(String(workId))}" ${selectable ? "" : "disabled"}>
      <span>
        <strong>${escapeHtml(title)}</strong>
        <small>${escapeHtml(listStatus)} · ID ${escapeHtml(String(workId || "--"))}</small>
      </span>
    </label>'''
    new = '''      <input type="checkbox" data-notion-sync-choice data-notion-sync-work-id="${escapeHtml(String(workId))}" ${selectable ? "" : "disabled"}>
      <strong title="${escapeHtml(title)}">${escapeHtml(title)}</strong>
      <span class="sync-notion-queue-arrow" aria-hidden="true">›</span>
    </label>'''
    return replace_once(
        text, old, new,
        "Sincronizar Notion: remover status/ID da fila",
        already='class="sync-notion-queue-arrow"',
    )

def patch_organization_css(text: str) -> str:
    block = r'''
/* QUEUE_CAPSULES_STANDARD_20260827
   Organização v2 — fila mostra somente checkbox + nome + affordance. */
.organization-item-list {
  gap: 7px;
}
.organization-list-item {
  grid-template-columns: 16px minmax(0, 1fr) 22px;
  gap: 10px;
  min-height: 48px;
  padding: 0 10px;
  border: 1px solid transparent;
  border-radius: 11px;
  background: #fffcfd;
  box-shadow: none;
  transform: translateX(0);
  transition: transform .16s ease, border-color .16s ease, background .16s ease, box-shadow .16s ease;
}
.organization-list-item h4 {
  min-width: 0;
  margin: 0;
  overflow: hidden;
  color: var(--text);
  font-size: 13px;
  font-weight: 600;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.organization-queue-arrow {
  color: transparent;
  font-size: 18px;
  line-height: 1;
  text-align: right;
  transform: translateX(-3px);
  transition: color .16s ease, transform .16s ease;
}
.organization-list-item:hover {
  border-color: var(--rose-border);
  background: var(--panel);
  box-shadow: none;
  transform: translateX(2px);
}
.organization-list-item:hover .organization-queue-arrow,
.organization-list-item[aria-current="true"] .organization-queue-arrow {
  color: var(--rose);
  transform: translateX(0);
}
.organization-list-item[aria-current="true"],
.organization-list-item[aria-current="true"]:hover {
  border-color: var(--rose);
  background: var(--panel);
  box-shadow: 0 7px 18px rgba(169, 77, 107, .08);
}
.organization-list-item.selected:not([aria-current="true"]) {
  border-color: transparent;
  background: #fffcfd;
  box-shadow: none;
}
.organization-list-item.selected:not([aria-current="true"]):hover {
  border-color: var(--rose-border);
  background: var(--panel);
}
'''
    return append_once(
        text, "QUEUE_CAPSULES_STANDARD_20260827",
        block, "Organização v2: aplicar Cápsulas leves",
    )

def patch_tracking_css(text: str) -> str:
    block = r'''
/* QUEUE_CAPSULES_STANDARD_20260827
   Acompanhamento — favorito é interação; todo metadado permanece no detalhe. */
.tracking-work-items {
  gap: 7px;
}
.tracking-work-item {
  grid-template-columns: auto minmax(0, 1fr) 22px;
  gap: 9px;
  min-height: 48px;
  padding: 0 10px;
  border: 1px solid transparent;
  border-radius: 11px;
  background: #fffcfd;
  box-shadow: none;
  transform: translateX(0);
  transition: transform .16s ease, border-color .16s ease, background .16s ease, box-shadow .16s ease;
}
.tracking-work-item strong {
  min-width: 0;
  font-weight: 600;
}
.tracking-queue-arrow {
  color: transparent;
  font-size: 18px;
  line-height: 1;
  text-align: right;
  transform: translateX(-3px);
  transition: color .16s ease, transform .16s ease;
}
.tracking-work-item:hover {
  border-color: var(--rose-border);
  background: var(--panel);
  transform: translateX(2px);
}
.tracking-work-item:hover .tracking-queue-arrow,
.tracking-work-item.active .tracking-queue-arrow {
  color: var(--rose);
  transform: translateX(0);
}
.tracking-work-item.active {
  border-color: var(--rose);
  background: var(--panel);
  box-shadow: 0 7px 18px rgba(169, 77, 107, .08);
}
'''
    return append_once(
        text, "QUEUE_CAPSULES_STANDARD_20260827",
        block, "Acompanhamento: aplicar Cápsulas leves",
    )

def patch_flows_css(text: str) -> str:
    block = r'''
/* QUEUE_CAPSULES_STANDARD_20260827
   Sync Notion — fila mostra somente checkbox + nome + affordance.
   Status/ID continuam disponíveis no painel de detalhe via data-* existente. */
.sync-notion-candidate-list {
  gap: 7px;
}
.sync-notion-candidate {
  grid-template-columns: 18px minmax(0, 1fr) 22px;
  align-items: center;
  gap: 10px;
  min-height: 48px;
  padding: 0 10px;
  border: 1px solid transparent;
  border-radius: 11px;
  background: #fffcfd;
  box-shadow: none;
  transform: translateX(0);
  transition: transform .16s ease, border-color .16s ease, background .16s ease, box-shadow .16s ease;
}
.sync-notion-candidate > strong {
  min-width: 0;
  overflow: hidden;
  color: var(--text);
  font-size: 14px;
  font-weight: 600;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.sync-notion-queue-arrow {
  color: transparent;
  font-size: 18px;
  line-height: 1;
  text-align: right;
  transform: translateX(-3px);
  transition: color .16s ease, transform .16s ease;
}
.sync-notion-candidate:hover {
  border-color: var(--rose-border);
  background: var(--panel);
  transform: translateX(2px);
}
.sync-notion-candidate:hover .sync-notion-queue-arrow,
.sync-notion-candidate.is-selected .sync-notion-queue-arrow {
  color: var(--rose);
  transform: translateX(0);
}
.sync-notion-candidate.is-selected {
  border-color: var(--rose);
  background: var(--panel);
  box-shadow: 0 7px 18px rgba(169, 77, 107, .08);
}
.sync-notion-candidate small {
  display: none;
}
'''
    return append_once(
        text, "QUEUE_CAPSULES_STANDARD_20260827",
        block, "Sincronizar Notion: aplicar Cápsulas leves",
    )

def verify(updated: dict[str, str]) -> None:
    checks = [
        ("docs", "QUEUE_CAPSULES_STANDARD_20260827"),
        ("docs", "Cápsulas leves"),
        ("organization_js", "organization-queue-arrow"),
        ("organization_css", "QUEUE_CAPSULES_STANDARD_20260827"),
        ("tracking_js", "tracking-queue-arrow"),
        ("tracking_css", "QUEUE_CAPSULES_STANDARD_20260827"),
        ("notion_js", "sync-notion-queue-arrow"),
        ("flows_css", "QUEUE_CAPSULES_STANDARD_20260827"),
    ]
    missing = [
        f"{key}: {needle}"
        for key, needle in checks
        if needle not in updated[key]
    ]
    if missing:
        raise PatchError("Validação estrutural falhou: " + "; ".join(missing))
    if '<small>${escapeHtml(listStatus)} · ID ${escapeHtml(String(workId || "--"))}</small>' in updated["notion_js"]:
        raise PatchError("Validação falhou: status/ID ainda aparece na fila do Sync Notion.")
    print("[OK] Validação estrutural concluída.")

def main() -> int:
    try:
        original = {name: read(path) for name, path in FILES.items()}
        updated = dict(original)

        updated["docs"] = patch_docs(updated["docs"])
        updated["organization_js"] = patch_organization_js(updated["organization_js"])
        updated["organization_css"] = patch_organization_css(updated["organization_css"])
        updated["tracking_js"] = patch_tracking_js(updated["tracking_js"])
        updated["tracking_css"] = patch_tracking_css(updated["tracking_css"])
        updated["notion_js"] = patch_notion_js(updated["notion_js"])
        updated["flows_css"] = patch_flows_css(updated["flows_css"])

        verify(updated)

        changed = [FILES[name] for name in FILES if updated[name] != original[name]]
        if not changed:
            print("[OK] Projeto já contém todos os ajustes.")
            return 0

        backup(changed)
        print(f"[OK] Backup criado em: {BACKUP_ROOT}")

        for name, path in FILES.items():
            if updated[name] != original[name]:
                path.write_text(updated[name], encoding="utf-8")
                print(f"[OK] Atualizado: {path.relative_to(ROOT)}")

        print("")
        print("Padronização de filas aplicada com sucesso.")
        print("")
        print("Validações recomendadas:")
        print("  node --check web/js/pages/organizationPage.js")
        print("  node --check web/js/pages/trackingPage.js")
        print("  node --check web/js/flows/syncNotionPanel.js")
        print("  python -m unittest discover -s tests -p 'test_release_monitor*.py' -v")
        return 0

    except PatchError as exc:
        print(f"[ERRO] {exc}")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
