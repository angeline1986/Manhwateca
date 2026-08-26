#!/usr/bin/env python3
from __future__ import annotations

import shutil
import sys
from datetime import datetime
from pathlib import Path

PATCH_NAME = "acompanhamento_paginacao_padrao_20260826"


def fail(message: str) -> None:
    raise RuntimeError(message)


def read(path: Path) -> str:
    if not path.exists():
        fail(f"Arquivo não encontrado: {path}")
    return path.read_text(encoding="utf-8")


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def replace_once(content: str, old: str, new: str, label: str) -> str:
    count = content.count(old)
    if count != 1:
        fail(f"{label}: trecho esperado encontrado {count} vez(es). Patch interrompido para não alterar código inesperado.")
    return content.replace(old, new, 1)


def replace_between(content: str, start: str, end: str, new_block: str, label: str) -> str:
    start_idx = content.find(start)
    if start_idx < 0:
        fail(f"{label}: início do bloco não encontrado.")
    end_idx = content.find(end, start_idx)
    if end_idx < 0:
        fail(f"{label}: fim do bloco não encontrado.")
    return content[:start_idx] + new_block + content[end_idx:]


def patch_tracking_html(content: str) -> str:
    start = '        <section class="page" id="page-tracking">'
    end = '        <section class="page" id="page-library">'
    start_idx = content.find(start)
    end_idx = content.find(end, start_idx)
    if start_idx < 0 or end_idx < 0:
        fail("Acompanhamento HTML: bloco #page-tracking não encontrado.")

    block = content[start_idx:end_idx]

    # Remove Grupo somente da tabela de Acompanhamento — não toca em outras tabelas.
    group_header = '                    <th>Grupo</th>\n'
    count = block.count(group_header)
    if count == 1:
        block = block.replace(group_header, "", 1)
    elif count == 0:
        # Permite reaplicar em repositório onde a coluna já tenha sido removida.
        pass
    else:
        fail(f"Acompanhamento HTML: cabeçalho Grupo encontrado {count} vezes dentro de #page-tracking.")

    pagination_anchor = '''                <tbody id="trackingReleaseList"></tbody>\n              </table>\n            </div>\n'''
    pagination_markup = '''                <tbody id="trackingReleaseList"></tbody>\n              </table>\n            </div>\n            <div class="tracking-pagination" id="trackingReleasePagination" aria-label="Paginação de lançamentos">\n              <button class="secondary-action" id="trackingReleasePrev" type="button">Anterior</button>\n              <span class="tracking-pagination-status" aria-live="polite">\n                Página <strong id="trackingReleasePageCurrent">1</strong> de\n                <strong id="trackingReleasePageTotal">1</strong>\n                <small id="trackingReleasePageRange">0 itens</small>\n              </span>\n              <button class="secondary-action" id="trackingReleaseNext" type="button">Próxima</button>\n            </div>\n'''
    if 'id="trackingReleasePagination"' not in block:
        block = replace_once(block, pagination_anchor, pagination_markup, "Adicionar paginação de Lançamentos recentes")

    return content[:start_idx] + block + content[end_idx:]


def patch_app_js(content: str) -> str:
    if 'trackingReleasePagination = byId("trackingReleasePagination")' not in content:
        old = '''const trackingFeedback = byId("trackingFeedback"), trackingReleaseList = byId("trackingReleaseList");\n'''
        new = '''const trackingFeedback = byId("trackingFeedback"), trackingReleaseList = byId("trackingReleaseList");\nconst trackingReleasePagination = byId("trackingReleasePagination");\nconst trackingReleasePrev = byId("trackingReleasePrev"), trackingReleaseNext = byId("trackingReleaseNext");\nconst trackingReleasePageCurrent = byId("trackingReleasePageCurrent"), trackingReleasePageTotal = byId("trackingReleasePageTotal");\nconst trackingReleasePageRange = byId("trackingReleasePageRange");\n'''
        content = replace_once(content, old, new, "Registrar elementos de paginação em app.js")

    if 'pagination: trackingReleasePagination' not in content:
        old = '''  feedback: trackingFeedback,\n  releaseList: trackingReleaseList,\n  worksCount: trackingWorksCount,\n'''
        new = '''  feedback: trackingFeedback,\n  releaseList: trackingReleaseList,\n  pagination: trackingReleasePagination,\n  pagePrev: trackingReleasePrev,\n  pageNext: trackingReleaseNext,\n  pageCurrent: trackingReleasePageCurrent,\n  pageTotal: trackingReleasePageTotal,\n  pageRange: trackingReleasePageRange,\n  worksCount: trackingWorksCount,\n'''
        content = replace_once(content, old, new, "Passar paginação para trackingPage")
    return content


def patch_tracking_js(content: str) -> str:
    if "const RELEASE_PAGE_SIZE = 5;" not in content:
        content = replace_once(
            content,
            "const DAY_OPTIONS = [1, 7, 15, 30, 45, 60];\n",
            "const DAY_OPTIONS = [1, 7, 15, 30, 45, 60];\nconst RELEASE_PAGE_SIZE = 5;\n",
            "Definir tamanho da página",
        )

    if "let releasePage = 1;" not in content:
        content = replace_once(
            content,
            "  let releases = [];\n",
            "  let releases = [];\n  let releasePage = 1;\n",
            "Criar estado da paginação",
        )

    function_start = "  function renderReleaseTable() {\n"
    function_end = "  function renderWorks() {\n"
    new_function = '''  function renderReleaseTable() {\n    const favoriteIds = favoriteMangaIds();\n    const onlyFavorites = Boolean(elements.favoritesOnly?.checked);\n    const items = onlyFavorites\n      ? releases.filter(item => favoriteIds.has(Number(item.manga_id)))\n      : releases;\n    const totalPages = Math.max(1, Math.ceil(items.length / RELEASE_PAGE_SIZE));\n    releasePage = Math.min(Math.max(1, releasePage), totalPages);\n    const start = (releasePage - 1) * RELEASE_PAGE_SIZE;\n    const visibleItems = items.slice(start, start + RELEASE_PAGE_SIZE);\n\n    renderReleasePagination(items.length, totalPages, start, visibleItems.length);\n\n    if (!items.length) {\n      elements.releaseList.innerHTML = '<tr><td colspan="4">Nenhum capítulo encontrado nesta janela.</td></tr>';\n      return;\n    }\n    elements.releaseList.innerHTML = visibleItems.map(item => `\n      <tr>\n        <td>${escapeHtml(item.title || "")}</td>\n        <td>${escapeHtml(item.chapter || "")}</td>\n        <td>${escapeHtml(dateOnly(item.release_date))}</td>\n        <td><span class="state ${item.viewed_at ? "ok" : "warn"}">${escapeHtml(item.status)}</span></td>\n      </tr>\n    `).join("");\n  }\n  function renderReleasePagination(totalItems, totalPages, start, visibleCount) {\n    if (!elements.pagination) return;\n    elements.pagination.hidden = totalItems === 0;\n    if (elements.pageCurrent) elements.pageCurrent.textContent = String(releasePage);\n    if (elements.pageTotal) elements.pageTotal.textContent = String(totalPages);\n    if (elements.pageRange) {\n      const first = totalItems ? start + 1 : 0;\n      const last = totalItems ? start + visibleCount : 0;\n      elements.pageRange.textContent = totalItems ? `${first}–${last} de ${totalItems}` : "0 itens";\n    }\n    if (elements.pagePrev) elements.pagePrev.disabled = releasePage <= 1;\n    if (elements.pageNext) elements.pageNext.disabled = releasePage >= totalPages;\n  }\n'''
    if function_start not in content or function_end not in content:
        fail("trackingPage.js: função renderReleaseTable/renderWorks não encontrada.")
    start_idx = content.find(function_start)
    end_idx = content.find(function_end, start_idx)
    current_block = content[start_idx:end_idx]
    if "renderReleasePagination" not in current_block:
        content = content[:start_idx] + new_function + content[end_idx:]
    else:
        # Se já aplicado, apenas garante colspan correto.
        content = content.replace('colspan="5">Nenhum capítulo encontrado nesta janela.', 'colspan="4">Nenhum capítulo encontrado nesta janela.')

    old_events = '''  elements.daysSlider?.addEventListener("input", () => {\n    days = DAY_OPTIONS[Number(elements.daysSlider.value)] || 15;\n    loadReleases();\n  });\n  elements.releaseSearch?.addEventListener("input", () => loadReleases());\n  elements.favoritesOnly?.addEventListener("change", renderReleaseTable);\n  elements.unseenOnly?.addEventListener("change", () => loadReleases());\n'''
    new_events = '''  elements.daysSlider?.addEventListener("input", () => {\n    days = DAY_OPTIONS[Number(elements.daysSlider.value)] || 15;\n    releasePage = 1;\n    loadReleases();\n  });\n  elements.releaseSearch?.addEventListener("input", () => {\n    releasePage = 1;\n    loadReleases();\n  });\n  elements.favoritesOnly?.addEventListener("change", () => {\n    releasePage = 1;\n    renderReleaseTable();\n  });\n  elements.unseenOnly?.addEventListener("change", () => {\n    releasePage = 1;\n    loadReleases();\n  });\n  elements.pagePrev?.addEventListener("click", () => {\n    if (releasePage <= 1) return;\n    releasePage -= 1;\n    renderReleaseTable();\n  });\n  elements.pageNext?.addEventListener("click", () => {\n    releasePage += 1;\n    renderReleaseTable();\n  });\n'''
    if 'elements.pagePrev?.addEventListener("click"' not in content:
        content = replace_once(content, old_events, new_events, "Adicionar eventos da paginação")
    return content


def patch_releases_css(content: str) -> str:
    layout_marker = "/* TRACKING_PAGE_STANDARD_20260826 */"
    if layout_marker not in content:
        addition = '''\n\n/* TRACKING_PAGE_STANDARD_20260826\n   Mantém Acompanhamento no mesmo envelope espacial das páginas operacionais de Fluxos. */\n.page-container:has(#page-tracking.active) {\n  padding: 16px;\n}\n\n#page-tracking {\n  width: min(1180px, 100%);\n  margin-right: auto;\n  margin-left: auto;\n}\n\n#page-tracking > .panel + .panel {\n  margin-top: 16px;\n}\n\n.tracking-pagination {\n  align-items: center;\n  display: flex;\n  gap: 12px;\n  justify-content: flex-end;\n  padding-top: 2px;\n}\n\n.tracking-pagination[hidden] {\n  display: none;\n}\n\n.tracking-pagination-status {\n  align-items: center;\n  color: var(--muted);\n  display: inline-flex;\n  flex-wrap: wrap;\n  gap: 4px;\n  justify-content: center;\n  min-width: 190px;\n  font-size: 12px;\n  font-weight: 800;\n}\n\n.tracking-pagination-status strong {\n  color: var(--text);\n}\n\n.tracking-pagination-status small {\n  color: var(--muted);\n  margin-left: 6px;\n  font-size: 11px;\n  font-weight: 750;\n}\n\n.tracking-pagination .secondary-action:disabled {\n  cursor: default;\n  opacity: .45;\n  transform: none !important;\n}\n'''
        content = content.rstrip() + addition + "\n"

    # Corrige especificamente as larguras da tabela de Acompanhamento para 4 colunas.
    start = ".tracking-releases-panel .release-table th:nth-child(1),\n"
    end = ".tracking-workspace {\n"
    if start not in content or end not in content:
        fail("releases.css: bloco de larguras da tabela de Acompanhamento não encontrado.")
    start_idx = content.find(start)
    end_idx = content.find(end, start_idx)
    new_widths = '''.tracking-releases-panel .release-table th:nth-child(1),\n.tracking-releases-panel .release-table td:nth-child(1) {\n  width: 48%;\n}\n\n.tracking-releases-panel .release-table th:nth-child(2),\n.tracking-releases-panel .release-table td:nth-child(2) {\n  width: 12%;\n}\n\n.tracking-releases-panel .release-table th:nth-child(3),\n.tracking-releases-panel .release-table td:nth-child(3) {\n  width: 20%;\n}\n\n.tracking-releases-panel .release-table th:nth-child(4),\n.tracking-releases-panel .release-table td:nth-child(4) {\n  width: 20%;\n}\n\n'''
    content = content[:start_idx] + new_widths + content[end_idx:]
    return content


def frontend_standard_doc() -> str:
    return '''# Padrão de criação de páginas — Manhwateca\n\nEste documento registra o contrato visual mínimo para novas páginas internas da interface web. O objetivo é impedir que cada tela crie um micro-layout próprio e acabe divergindo em posição, largura, espaçamento e componentes.\n\n## 1. Referência principal\n\nPara páginas operacionais internas, **Fluxos / Buscar candidatos** é a referência de composição e espaçamento. Antes de criar CSS novo, reutilize tokens, componentes e estruturas já existentes em `web/css/` e `web/js/`.\n\n## 2. Envelope da página\n\n- Use a estrutura existente `workspace > topbar + .page-container > .page`.\n- Não altere `.page-container` global para corrigir apenas uma página. Prefira regra escopada pelo ID da página ativa.\n- Para páginas que devem seguir o padrão compacto de Fluxos, use `padding: 16px` no `.page-container` somente quando aquela página estiver ativa.\n- Quando o conteúdo principal for operacional, use largura máxima de referência de **1180px** e centralização horizontal.\n- Evite valores próprios de margem superior que afastem o primeiro painel da topbar.\n\nExemplo:\n\n```css\n.page-container:has(#page-exemplo.active) {\n  padding: 16px;\n}\n\n#page-exemplo {\n  width: min(1180px, 100%);\n  margin-right: auto;\n  margin-left: auto;\n}\n```\n\n## 3. Painéis e seções\n\n- Reutilize `.panel`, `.section-heading`, `.eyebrow`, `.primary-action`, `.secondary-action`, badges, estados e inputs existentes.\n- Não recrie visualmente um componente que já existe.\n- Defina o espaço entre painéis no escopo da página, sem alterar `.page > .panel + .panel` global.\n- Use `16px` como referência de espaçamento compacto entre grandes seções operacionais, salvo necessidade real do fluxo.\n\n## 4. Tabelas e listas\n\n- Reutilize os componentes de tabela existentes antes de criar uma variante.\n- Cabeçalho e corpo devem sempre ter a mesma quantidade de colunas.\n- Estados vazios devem usar `colspan` compatível com a quantidade atual de colunas.\n- Se uma lista puder crescer além do espaço confortável de leitura, adote paginação ou limite visual explícito.\n\n## 5. Paginação\n\nPara paginação client-side:\n\n- mantenha `currentPage` e `pageSize` no módulo da página;\n- ao alterar busca ou filtros, retorne para a página 1;\n- limite `currentPage` ao total de páginas após qualquer mudança nos dados;\n- desabilite Anterior/Próxima nos extremos;\n- mostre página atual, total de páginas e intervalo de registros;\n- use os botões/componentes existentes, sem criar nova paleta.\n\nQuando a quantidade de dados for grande ou o endpoint já oferecer paginação real, prefira paginação no backend.\n\n## 6. JavaScript por página\n\n- Mantenha a lógica específica em `web/js/pages/<pagina>Page.js`.\n- Registre elementos DOM em `web/js/app.js` e passe-os para o módulo da página.\n- Evite seletores globais quando um ID ou elemento injetado puder manter o escopo explícito.\n- Filtros e paginação devem ser estado da própria página, sem alterar contratos de API sem necessidade.\n\n## 7. CSS por página\n\n- Regras específicas ficam em `web/css/pages/`.\n- Não use uma correção global para resolver diferença visual de uma única tela.\n- Antes de adicionar cor, sombra, raio ou espaçamento novo, procure o token/componente equivalente já existente.\n- A paleta Rose Edition atual deve ser preservada.\n\n## 8. Checklist antes de concluir uma página\n\n- [ ] Primeiro painel está alinhado com a topbar como as páginas de referência.\n- [ ] Largura e centralização seguem o padrão operacional.\n- [ ] Espaçamento entre grandes seções é consistente.\n- [ ] Foram reutilizados componentes existentes.\n- [ ] Tabelas têm cabeçalho, corpo e `colspan` coerentes.\n- [ ] Listas longas possuem paginação/limite apropriado.\n- [ ] Filtros resetam a paginação quando necessário.\n- [ ] Não foram adicionadas cores ou componentes redundantes.\n- [ ] CSS e JS estão escopados à página.\n- [ ] A página foi conferida em viewport desktop e reduzido.\n\n## 9. Página Acompanhamento como exemplo\n\nA correção de Acompanhamento de 26/08/2026 segue este padrão: envelope de 16px, largura operacional de 1180px, seções com espaçamento controlado, tabela de quatro colunas coerentes e paginação client-side de cinco lançamentos por página.\n'''


def validate(files: dict[Path, str]) -> None:
    index = files[Path("web/index.html")]
    app = files[Path("web/js/app.js")]
    tracking = files[Path("web/js/pages/trackingPage.js")]
    css = files[Path("web/css/pages/releases.css")]

    tracking_block = index[index.find('id="page-tracking"'):index.find('id="page-library"')]
    checks = [
        (tracking_block.count("<th>Grupo</th>") == 0, "Coluna Grupo ainda existe em Acompanhamento"),
        ('id="trackingReleasePagination"' in tracking_block, "Paginação não foi adicionada ao HTML"),
        ('colspan="4"' in tracking, "Estado vazio não usa colspan=4"),
        ("const RELEASE_PAGE_SIZE = 5;" in tracking, "Page size não é 5"),
        ('elements.pagePrev?.addEventListener("click"' in tracking, "Evento Anterior ausente"),
        ('elements.pageNext?.addEventListener("click"' in tracking, "Evento Próxima ausente"),
        ('pagination: trackingReleasePagination' in app, "Elementos da paginação não foram ligados no app.js"),
        ('.page-container:has(#page-tracking.active)' in css, "Envelope compacto de Acompanhamento ausente"),
        ('width: min(1180px, 100%);' in css, "Largura operacional de Acompanhamento ausente"),
    ]
    errors = [message for ok, message in checks if not ok]
    if errors:
        fail("Validação falhou: " + "; ".join(errors))


def main() -> int:
    root = Path.cwd()
    required = [
        Path("web/index.html"),
        Path("web/js/app.js"),
        Path("web/js/pages/trackingPage.js"),
        Path("web/css/pages/releases.css"),
    ]
    for relative in required:
        if not (root / relative).exists():
            print(f"[ERRO] Execute este script na raiz do projeto Manhwateca. Ausente: {relative}")
            return 2

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = root / "reports" / "patch_backups" / f"{PATCH_NAME}_{timestamp}"
    backup_root.mkdir(parents=True, exist_ok=False)
    print(f"[OK] Backup criado em: {backup_root}")

    originals: dict[Path, str] = {}
    patched: dict[Path, str] = {}

    try:
        for relative in required:
            source = root / relative
            originals[relative] = read(source)
            backup = backup_root / relative
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, backup)

        patched[Path("web/index.html")] = patch_tracking_html(originals[Path("web/index.html")])
        patched[Path("web/js/app.js")] = patch_app_js(originals[Path("web/js/app.js")])
        patched[Path("web/js/pages/trackingPage.js")] = patch_tracking_js(originals[Path("web/js/pages/trackingPage.js")])
        patched[Path("web/css/pages/releases.css")] = patch_releases_css(originals[Path("web/css/pages/releases.css")])

        validate(patched)

        for relative, content in patched.items():
            write(root / relative, content)

        doc_path = root / "docs" / "frontend_page_standard.md"
        if doc_path.exists():
            backup_doc = backup_root / "docs" / "frontend_page_standard.md"
            backup_doc.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(doc_path, backup_doc)
        write(doc_path, frontend_standard_doc())

        print("[OK] Acompanhamento alinhado ao envelope operacional (16px / 1180px).")
        print("[OK] Lançamentos recentes paginados em 5 itens por página.")
        print("[OK] Coluna Grupo removida somente da tabela de Acompanhamento.")
        print("[OK] Filtros resetam paginação para a página 1.")
        print("[OK] docs/frontend_page_standard.md criado/atualizado.")
        print("[OK] Patch aplicado com sucesso.")
        return 0
    except Exception as exc:
        print(f"[ERRO] {exc}")
        print("[INFO] Nenhum arquivo do projeto foi gravado após falha de validação, ou use o backup acima para restauração.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
