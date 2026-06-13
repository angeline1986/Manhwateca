import os
import sys


USE_COLOR = sys.stdout.isatty() and "NO_COLOR" not in os.environ
TITLE_COLOR = "\033[1;36m" if USE_COLOR else ""
LOCAL_COLOR = "\033[1;36m" if USE_COLOR else ""
API_COLOR = "\033[1;33m" if USE_COLOR else ""
NOTION_COLOR = "\033[1;35m" if USE_COLOR else ""
AUTOMATION_COLOR = "\033[1;32m" if USE_COLOR else ""
EXIT_COLOR = "\033[1;31m" if USE_COLOR else ""
RESET_COLOR = "\033[0m" if USE_COLOR else ""

BANNER = """
📖 MANHWATECA | Gestão e Sincronização
📂 Catálogo: data/mangas.json
────────────────────────────────────────────────
"""

MENU = f"""
📋 ESCOLHA UMA OPÇÃO:

  {LOCAL_COLOR}[ ETAPA 1: ORGANIZAÇÃO LOCAL ]{RESET_COLOR}

  {LOCAL_COLOR}1. 📄 Padronização e Auditoria{RESET_COLOR}
     Analisa pastas, capítulos e capas.

  {LOCAL_COLOR}2. 🔤 Organização Estrutural{RESET_COLOR}
     Organiza as obras em grupos alfabéticos.

  {AUTOMATION_COLOR}[ ETAPA 2: CATALOGAR BIBLIOTECA ]{RESET_COLOR}

  {AUTOMATION_COLOR}3. 📚 Catalogar Biblioteca{RESET_COLOR}
     Lê o Drive e atualiza data/mangas.json.

  {API_COLOR}[ ETAPA 3: ENRIQUECER DADOS ]{RESET_COLOR}

  {API_COLOR}4. 🔎 MangaUpdates: Localizar IDs{RESET_COLOR}
     Busca IDs e atualiza buscaIds.json.

  {API_COLOR}5. 🌐 MangaUpdates: Dados e CSV{RESET_COLOR}
     Usa dados salvos ou consulta novos detalhes na API.

  {NOTION_COLOR}[ ETAPA 4: SINCRONIZAR COM NOTION ]{RESET_COLOR}

  {NOTION_COLOR}6. 🔄 Sincronizar Catálogo{RESET_COLOR}
     Simula, importa ou atualiza páginas no Notion.

  {NOTION_COLOR}7. 📥 Atualizar Metadados{RESET_COLOR}
     Atualiza páginas existentes usando o CSV.

  {AUTOMATION_COLOR}[ AUTOMAÇÃO E SUPORTE ]{RESET_COLOR}

  {AUTOMATION_COLOR}8. 🚀 Executar Fluxo Completo{RESET_COLOR}
     Gera relatórios, cataloga e simula a sincronização.

  {AUTOMATION_COLOR}9. 🧹 Executar Testes{RESET_COLOR}
     Verifica automaticamente as principais regras do projeto.

  {EXIT_COLOR}0. ❌ Sair{RESET_COLOR}
"""
