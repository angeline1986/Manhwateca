from pathlib import Path

root = Path(__file__).resolve().parent
org_path = root / "web/js/pages/organizationPage.js"
sidebar_path = root / "web/js/layout/sidebar.js"

if not org_path.is_file() or not sidebar_path.is_file():
    raise SystemExit(
        "Execute apply_patch.py na raiz do repositório Manhwateca. "
        "Esperados: web/js/pages/organizationPage.js e web/js/layout/sidebar.js"
    )

org = org_path.read_text(encoding="utf-8")
sidebar = sidebar_path.read_text(encoding="utf-8")


def replace_js_function(source, signature, replacement):
    start = source.find(signature)
    if start < 0:
        raise RuntimeError(f"Função não encontrada: {signature}")

    brace = source.find("{", start)
    if brace < 0:
        raise RuntimeError(f"Abertura da função não encontrada: {signature}")

    depth = 0
    quote = None
    escaped = False
    i = brace

    while i < len(source):
        ch = source[i]

        if quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = None
            i += 1
            continue

        if ch in ('"', "'", "`"):
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                return source[:start] + replacement + source[end:]

        i += 1

    raise RuntimeError(f"Fechamento da função não encontrado: {signature}")


new_update_topbar = '''  function updateTopbar(config) {
    const eyebrow = document.getElementById("pageEyebrow");
    const title = document.getElementById("pageTitle");
    const subtitle = document.getElementById("pageSubtitle");
    const staticStatus = document.querySelector(".organization-topbar-status");

    if (eyebrow) eyebrow.textContent = `ORGANIZAÇÃO / ${config.title.toUpperCase()}`;
    if (title) title.textContent = "Organizar biblioteca local";
    if (subtitle) subtitle.textContent = config.subtitle;
    if (staticStatus) staticStatus.hidden = true;
  }'''

org = replace_js_function(
    org,
    "  function updateTopbar(config)",
    new_update_topbar,
)

for line in [
    '        <span class="organization-stage-status">${escapeHtml(config.status || "Prévia local")}</span>\n',
    '        <span class="organization-stage-status">Somente leitura</span>\n',
    '        <span class="organization-stage-status">Pronto para aplicar</span>\n',
    '        <span class="organization-stage-status">Prévia local</span>\n',
    '        <span class="organization-stage-status">Decisão manual</span>\n',
]:
    org = org.replace(line, "")

if "manhwateca:organization-legacy" not in org:
    marker = '  window.addEventListener("manhwateca:organization-subtab", event => {'
    pos = org.find(marker)
    if pos < 0:
        marker = "  return { renderCatalogPending };"
        pos = org.find(marker)
    if pos < 0:
        raise RuntimeError("Ponto de inserção do modo legado não encontrado.")

    legacy_code = '''  function showLegacyOrganization() {
    organizationSubtab = null;
    selectedIndex = 0;
    organizationCheckedKeys = new Set();
    setOrganizationMode(false);
    restoreTopbar();
  }

  window.addEventListener("manhwateca:organization-legacy", () => {
    showLegacyOrganization();
  });

'''
    org = org[:pos] + legacy_code + org[pos:]

if "manhwateca:organization-legacy" not in sidebar:
    marker = "  return { closeSidebar, setSidebarCollapsed };"
    pos = sidebar.find(marker)
    if pos < 0:
        raise RuntimeError("Retorno de initSidebar() não encontrado.")

    sidebar_code = '''  const legacyOrganizationButton =
    document.querySelector('[data-page="organization"]');

  legacyOrganizationButton?.addEventListener("click", () => {
    setContext(null);

    document.querySelectorAll("[data-sidebar-organization-subtab]").forEach(button => {
      button.classList.remove("active");
    });

    window.dispatchEvent(
      new CustomEvent("manhwateca:organization-legacy")
    );
  });

'''
    sidebar = sidebar[:pos] + sidebar_code + sidebar[pos:]

required_org = [
    "function updateTopbar(config)",
    "manhwateca:organization-legacy",
    "setOrganizationMode(false)",
    "restoreTopbar()",
    "validate_chapters",
    "review_pending",
]
required_sidebar = [
    'data-page="organization"',
    "manhwateca:organization-legacy",
]

missing_org = [item for item in required_org if item not in org]
missing_sidebar = [item for item in required_sidebar if item not in sidebar]

if missing_org or missing_sidebar:
    raise RuntimeError(
        "Validação do patch falhou antes da gravação. "
        f"organizationPage={missing_org}; sidebar={missing_sidebar}"
    )

start = org.find("  function updateTopbar(config)")
end = org.find("  function restoreTopbar", start)
if end < 0:
    raise RuntimeError("restoreTopbar não encontrada após updateTopbar.")

if "config.status" in org[start:end]:
    raise RuntimeError("updateTopbar ainda contém config.status.")

org_path.write_text(org, encoding="utf-8")
sidebar_path.write_text(sidebar, encoding="utf-8")

print("Patch aplicado com sucesso.")
print("Arquivos alterados:")
print("  web/js/pages/organizationPage.js")
print("  web/js/layout/sidebar.js")
