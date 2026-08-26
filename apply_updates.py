#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parent
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_ROOT = ROOT / "reports" / "patch_backups" / f"acompanhamento_paginacao_v2_{STAMP}"

FILES = {
    "index": ROOT / "web" / "index.html",
    "tracking_js": ROOT / "web" / "js" / "pages" / "trackingPage.js",
    "releases_css": ROOT / "web" / "css" / "pages" / "releases.css",
    "repository": ROOT / "manhwateca" / "release_monitor" / "repository.py",
    "docs": ROOT / "docs" / "frontend_page_standard.md",
}


class PatchError(RuntimeError):
    pass


def read(path: Path) -> str:
    if not path.is_file():
        raise PatchError(f"Arquivo não encontrado: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def backup(paths: list[Path]) -> None:
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    for path in paths:
        rel = path.relative_to(ROOT)
        target = BACKUP_ROOT / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def replace_once(text: str, old: str, new: str, label: str, *, allow_already: str | None = None) -> str:
    if allow_already and allow_already in text:
        print(f"[SKIP] {label}: ajuste já presente.")
        return text
    count = text.count(old)
    if count != 1:
        raise PatchError(
            f"{label}: trecho esperado encontrado {count} vez(es). "
            "Patch interrompido para não alterar código inesperado."
        )
    print(f"[OK] {label}")
    return text.replace(old, new, 1)


def replace_between(text: str, start: str, end: str, replacement: str, label: str, *, already: str | None = None) -> str:
    if already and already in text:
        print(f"[SKIP] {label}: ajuste já presente.")
        return text
    start_pos = text.find(start)
    if start_pos < 0:
        raise PatchError(f"{label}: início do trecho não encontrado.")
    end_pos = text.find(end, start_pos)
    if end_pos < 0:
        raise PatchError(f"{label}: fim do trecho não encontrado.")
    print(f"[OK] {label}")
    return text[:start_pos] + replacement + text[end_pos:]


def patch_index(text: str) -> str:
    old = '''            <div class="tracking-pagination" id="trackingReleasePagination" aria-label="Paginação de lançamentos">
              <button class="secondary-action" id="trackingReleasePrev" type="button">Anterior</button>
              <span class="tracking-pagination-status" aria-live="polite">
                Página <strong id="trackingReleasePageCurrent">1</strong> de
                <strong id="trackingReleasePageTotal">1</strong>
                <small id="trackingReleasePageRange">0 itens</small>
              </span>
              <button class="secondary-action" id="trackingReleaseNext" type="button">Próxima</button>
            </div>'''
    new = '''            <div class="flow-pager tracking-release-pager"
                 id="trackingReleasePagination"
                 aria-label="Paginação de lançamentos"
                 aria-live="polite"></div>'''
    return replace_once(
        text, old, new,
        "Usar paginação padrão de Buscar candidatos em Lançamentos recentes",
        allow_already='class="flow-pager tracking-release-pager"',
    )


def patch_tracking_js(text: str) -> str:
    text = replace_once(
        text,
        '<article><span>ÚLTIMO LANÇAMENTO</span><strong>${escapeHtml(latestReleaseLabel(item))}</strong></article>',
        '<article><span>ÚLTIMO LANÇAMENTO</span><strong>${escapeHtml(latestReleaseLabel(item, history))}</strong></article>',
        "Usar histórico carregado como fallback do Último lançamento",
        allow_already="latestReleaseLabel(item, history)",
    )

    start = "  function renderReleasePagination(totalItems, totalPages, start, visibleCount) {"
    end = "  function renderWorks() {"
    replacement = '''  function renderReleasePagination(totalItems, totalPages) {
    if (!elements.pagination) return;
    elements.pagination.hidden = totalItems === 0 || totalPages <= 1;
    if (elements.pagination.hidden) {
      elements.pagination.innerHTML = "";
      return;
    }
    elements.pagination.innerHTML = `
      <button class="flow-page-link" type="button"
              ${releasePage <= 1 ? "disabled" : ""}
              data-tracking-release-page="${releasePage - 1}"
              aria-label="Página anterior">‹</button>
      ${releasePageButtons(releasePage, totalPages)}
      <button class="flow-page-link" type="button"
              ${releasePage >= totalPages ? "disabled" : ""}
              data-tracking-release-page="${releasePage + 1}"
              aria-label="Próxima página">›</button>
    `;
  }

  function releasePageButtons(page, pages) {
    const startPage = Math.max(1, Math.min(page - 1, pages - 2));
    const endPage = Math.min(pages, startPage + 2);
    return Array.from({ length: endPage - startPage + 1 }, (_, index) => startPage + index)
      .map(number => `
        <button type="button"
                class="flow-page-link ${number === page ? "active" : ""}"
                data-tracking-release-page="${number}">${number}</button>
      `)
      .join("");
  }

'''
    text = replace_between(
        text, start, end, replacement,
        "Renderizar paginação com flow-pager/flow-page-link",
        already="function releasePageButtons(page, pages)",
    )

    text = replace_once(
        text,
        "    renderReleasePagination(items.length, totalPages, start, visibleItems.length);",
        "    renderReleasePagination(items.length, totalPages);",
        "Simplificar chamada da paginação",
        allow_already="    renderReleasePagination(items.length, totalPages);",
    )

    old_events = '''  elements.pagePrev?.addEventListener("click", () => {
    if (releasePage <= 1) return;
    releasePage -= 1;
    renderReleaseTable();
  });
  elements.pageNext?.addEventListener("click", () => {
    releasePage += 1;
    renderReleaseTable();
  });
'''
    new_events = '''  elements.pagination?.addEventListener("click", event => {
    const button = event.target.closest("[data-tracking-release-page]");
    if (!button || button.disabled) return;
    const nextPage = Number(button.dataset.trackingReleasePage);
    if (!Number.isFinite(nextPage) || nextPage < 1) return;
    releasePage = nextPage;
    renderReleaseTable();
  });
'''
    text = replace_once(
        text, old_events, new_events,
        "Usar delegação de eventos no pager padrão",
        allow_already='event.target.closest("[data-tracking-release-page]")',
    )

    old_func = '''function latestReleaseLabel(item) {
  if (!item.latest_release_chapter && !item.latest_release_date) return "Sem lançamento registrado";
  const chapter = item.latest_release_chapter ? `cap ${item.latest_release_chapter}` : "capítulo não informado";
  const date = dateOnly(item.latest_release_date);
  return `${chapter} · ${date}`;
}
'''
    new_func = '''function latestReleaseLabel(item, releaseHistory = []) {
  const rows = releaseHistory
    .filter(row => Number(row.manga_id) === Number(item.manga_id))
    .sort((left, right) => String(right.release_date || "").localeCompare(String(left.release_date || "")));
  const fallback = rows[0] || {};
  const chapterValue = item.latest_release_chapter || fallback.chapter;
  const dateValue = item.latest_release_date || fallback.release_date;
  if (!chapterValue && !dateValue) return "Sem lançamento registrado";
  const chapter = chapterValue ? `cap ${chapterValue}` : "cap não informado";
  const date = dateOnly(dateValue);
  return `${chapter} · ${date}`;
}
'''
    text = replace_once(
        text, old_func, new_func,
        "Adicionar fallback seguro ao Último lançamento",
        allow_already="function latestReleaseLabel(item, releaseHistory = [])",
    )
    return text


def patch_css(text: str) -> str:
    old_name = '''.tracking-work-item strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}'''
    new_name = '''.tracking-work-item strong {
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}'''
    text = replace_once(
        text, old_name, new_name,
        "Reduzir peso dos nomes na Fila de obras",
        allow_already=".tracking-work-item strong {\n  font-weight: 500;",
    )

    old_star = '''.tracking-star {
  background: transparent !important;
  border: 0;
  color: var(--rose-dark) !important;
  cursor: pointer;
  font-size: 22px;
  line-height: 1;
  padding: 2px !important;
  transform: none !important;
}'''
    new_star = '''.tracking-star {
  background: transparent !important;
  border: 0;
  color: var(--rose-dark) !important;
  cursor: pointer;
  font-size: 22px;
  font-weight: 400;
  line-height: 1;
  padding: 2px !important;
  transform: none !important;
}'''
    text = replace_once(
        text, old_star, new_star,
        "Usar peso regular nas estrelas de favorito",
        allow_already="font-weight: 400;\n  line-height: 1;",
    )

    start = ".tracking-pagination {"
    if start in text:
        start_pos = text.find(start)
        marker = ".tracking-pagination .secondary-action:disabled {"
        marker_pos = text.find(marker, start_pos)
        if marker_pos < 0:
            raise PatchError("Remover paginação antiga: bloco disabled não encontrado.")
        close_pos = text.find("}\n", marker_pos)
        if close_pos < 0:
            raise PatchError("Remover paginação antiga: fechamento não encontrado.")
        close_pos += 2
        text = text[:start_pos] + text[close_pos:]
        print("[OK] Remover CSS do microcomponente de paginação anterior")
    else:
        print("[SKIP] Remover CSS do microcomponente de paginação anterior: já ausente.")

    canonical_css = '''
/* Acompanhamento reutiliza exatamente o componente de paginação de Fluxos/Buscar candidatos. */
#page-tracking .tracking-release-pager {
  margin-left: auto;
  margin-top: 0;
}
'''
    if "#page-tracking .tracking-release-pager" not in text:
        anchor = "#page-tracking > .panel + .panel {\n  margin-top: 16px;\n}\n"
        if anchor not in text:
            raise PatchError("Inserir ajuste do pager: âncora do layout de Acompanhamento não encontrada.")
        text = text.replace(anchor, anchor + canonical_css, 1)
        print("[OK] Reutilizar flow-pager no Acompanhamento")
    else:
        print("[SKIP] Reutilizar flow-pager no Acompanhamento: ajuste já presente.")
    return text


def patch_repository(text: str) -> str:
    old = '''            LEFT JOIN LATERAL (
                SELECT r.chapter, r.release_date, r.release_group
                FROM external_releases r
                WHERE r.manga_id = m.id
                ORDER BY r.release_date DESC, r.first_seen_at DESC, r.id DESC
                LIMIT 1
            ) latest ON TRUE'''
    new = '''            LEFT JOIN LATERAL (
                SELECT releases.chapter, releases.release_date, releases.release_group
                FROM (
                    SELECT
                        r.chapter,
                        r.release_date,
                        r.release_group,
                        r.first_seen_at AS seen_at,
                        r.id
                    FROM external_releases r
                    WHERE r.manga_id = m.id

                    UNION ALL

                    SELECT
                        mr.chapter,
                        mr.release_date,
                        mr.release_group,
                        mr.first_seen_at AS seen_at,
                        mr.id
                    FROM mangaupdates_releases mr
                    WHERE mr.manga_id = m.id
                ) releases
                ORDER BY releases.release_date DESC NULLS LAST,
                         releases.seen_at DESC NULLS LAST,
                         releases.id DESC
                LIMIT 1
            ) latest ON TRUE'''
    return replace_once(
        text, old, new,
        "Buscar Último lançamento nas duas fontes persistidas",
        allow_already="FROM mangaupdates_releases mr\n                    WHERE mr.manga_id = m.id",
    )


def patch_docs(text: str) -> str:
    start = "## 5. Paginação\n"
    end = "## 6. JavaScript por página\n"
    replacement = '''## 5. Paginação

O componente canônico de paginação para páginas internas é o mesmo usado em
**Fluxos > Jornada operacional > Buscar candidatos**.

### Contrato visual obrigatório

- reutilize `.flow-pager` como contêiner;
- reutilize `.flow-page-link` em todas as ações;
- use `‹` e `›` para anterior/próxima;
- mostre até **3 números de página** por vez;
- a página atual deve usar `.active`, com o sublinhado Rose já definido em `flows.css`;
- desabilite os extremos com `disabled`;
- não crie uma segunda aparência com botões “Anterior / Próxima”, contador
  “Página X de Y” ou nova paleta quando o padrão de Fluxos atender à tela.

Estrutura de referência:

```html
<div class="flow-pager">
  <button class="flow-page-link" aria-label="Página anterior">‹</button>
  <button class="flow-page-link active">1</button>
  <button class="flow-page-link">2</button>
  <button class="flow-page-link">3</button>
  <button class="flow-page-link" aria-label="Próxima página">›</button>
</div>
```

Para paginação client-side:

- mantenha `currentPage` e `pageSize` no módulo da página;
- ao alterar busca ou filtros, retorne para a página 1;
- limite `currentPage` ao total de páginas após qualquer mudança nos dados;
- para listas pequenas, esconda o pager quando houver somente uma página;
- use a mesma janela de até três números adotada por Buscar candidatos.

Quando a quantidade de dados for grande ou o endpoint já oferecer paginação real,
prefira paginação no backend.

'''
    text = replace_between(
        text, start, end, replacement,
        "Documentar paginação canônica de Buscar candidatos",
        already="### Contrato visual obrigatório",
    )

    old_example = (
        "A correção de Acompanhamento de 26/08/2026 segue este padrão: envelope de 16px, "
        "largura operacional de 1180px, seções com espaçamento controlado, tabela de quatro "
        "colunas coerentes e paginação client-side de cinco lançamentos por página."
    )
    new_example = (
        "A página Acompanhamento segue este padrão: envelope de 16px, largura operacional "
        "de 1180px, seções com espaçamento controlado, tabela de quatro colunas coerentes "
        "e paginação client-side de cinco lançamentos por página usando o componente "
        "canônico `flow-pager` / `flow-page-link` de Buscar candidatos."
    )
    if old_example in text:
        text = text.replace(old_example, new_example, 1)
        print("[OK] Atualizar exemplo de Acompanhamento na documentação")
    elif new_example in text:
        print("[SKIP] Atualizar exemplo de Acompanhamento na documentação: já atualizado.")
    else:
        raise PatchError("Atualizar exemplo de Acompanhamento: parágrafo esperado não encontrado.")
    return text


def verify(contents: dict[str, str]) -> None:
    checks = [
        ('class="flow-pager tracking-release-pager"', contents["index"], "HTML usa o pager padrão"),
        ('data-tracking-release-page=', contents["tracking_js"], "JS renderiza links de página"),
        ('function releasePageButtons(page, pages)', contents["tracking_js"], "JS limita números da paginação"),
        ('latestReleaseLabel(item, history)', contents["tracking_js"], "Detalhe usa fallback de histórico"),
        ('font-weight: 500;', contents["releases_css"], "Fila de obras não usa negrito forte"),
        ('#page-tracking .tracking-release-pager', contents["releases_css"], "Pager escopado ao Acompanhamento"),
        ('FROM mangaupdates_releases mr', contents["repository"], "Consulta inclui histórico MangaUpdates"),
        ('### Contrato visual obrigatório', contents["docs"], "Padrão de paginação documentado"),
    ]
    missing = [label for needle, haystack, label in checks if needle not in haystack]
    if missing:
        raise PatchError("Validação final falhou: " + "; ".join(missing))
    if 'id="trackingReleasePrev"' in contents["index"] or 'id="trackingReleaseNext"' in contents["index"]:
        raise PatchError("Validação final falhou: paginação antiga ainda existe no HTML.")
    print("[OK] Validação estrutural concluída.")


def main() -> int:
    try:
        original = {name: read(path) for name, path in FILES.items()}
        updated = dict(original)
        updated["index"] = patch_index(updated["index"])
        updated["tracking_js"] = patch_tracking_js(updated["tracking_js"])
        updated["releases_css"] = patch_css(updated["releases_css"])
        updated["repository"] = patch_repository(updated["repository"])
        updated["docs"] = patch_docs(updated["docs"])
        verify(updated)

        changed_paths = [FILES[name] for name in FILES if updated[name] != original[name]]
        if not changed_paths:
            print("[OK] Nenhuma alteração necessária; projeto já está atualizado.")
            return 0

        backup(changed_paths)
        print(f"[OK] Backup criado em: {BACKUP_ROOT}")
        for name, path in FILES.items():
            if updated[name] != original[name]:
                write(path, updated[name])
                print(f"[OK] Atualizado: {path.relative_to(ROOT)}")

        print("\nAjustes aplicados com sucesso.")
        print("Arquivos alterados:")
        for path in changed_paths:
            print(f"  - {path.relative_to(ROOT)}")
        print("\nValidações recomendadas:")
        print("  node --check web/js/pages/trackingPage.js")
        print("  python -m py_compile manhwateca/release_monitor/repository.py")
        print("  python -m unittest discover -s tests")
        return 0
    except PatchError as error:
        print(f"[ERRO] {error}")
        return 1
    except Exception as error:
        print(f"[ERRO] Falha inesperada: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
