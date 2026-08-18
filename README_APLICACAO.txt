MANHWATECA — PACOTE ORGANIZAÇÃO / LAYOUT APROVADO
==================================================

Base analisada:
https://github.com/angeline1986/Manhwateca (branch main)

Objetivo
--------
Aplicar às telas do menu Organização o padrão visual aprovado nas referências
fornecidas, sem criar uma Organização paralela e sem alterar backend/API/router.

Arquivos do pacote
------------------
- web/js/pages/organizationPage.js
- web/css/pages/organization.css

Telas contempladas
------------------
1. Rastrear biblioteca
   - layout amplo
   - cabeçalho interno + status
   - snapshot/progresso em etapas
   - barra de próxima ação

2. Revisar estrutura
   - Split Panel
   - fila compacta à esquerda
   - detalhe rico à direita
   - dados provenientes de catalogPendingItems

3. Padronizar nomes
   - mesmo Split Panel
   - dados/ação da etapa rename_preview

4. Organizar pastas
   - mesmo Split Panel
   - dados/ação da etapa organization_preview

5. Validar capítulos
   - mesmo Split Panel
   - dados/ação da etapa chapter_audit

6. Revisar pendências
   - mesmo Split Panel
   - usa as pendências já renderizadas pelo sistema

7. Aplicar organização
   - layout amplo
   - resumo de impacto
   - checklist
   - ações apply_renaming / apply_organization com confirmação

Acordos visuais preservados
---------------------------
- Mesma identidade Rose Edition existente.
- Nenhuma nova paleta.
- Reuso das cores e cores semânticas já presentes no CSS atual do projeto.
- Não altera sidebar.
- Não altera navegação.
- Não cria nova rota.
- Não cria nova página em index.html.
- Busca sem label externo.
- Linha de filtros: [ filtro ] [ quantidade ] [ checkbox ].
- Checkbox compacto sem o texto "Selecionar visíveis"; mantém title/aria-label.
- Itens da fila mostram somente o identificador principal.
- Painel direito concentra status, contexto, diagnóstico e ações.

Escopo técnico
--------------
NÃO contém alterações em:
- manhwateca/
- tests/
- web/index.html
- web/js/app.js
- web/js/router.js
- web/js/layout/sidebar.js
- web/js/api/

Como aplicar
------------
1. Confirme que seu working tree está limpo ou faça backup das alterações locais.
2. Extraia este ZIP na raiz do repositório Manhwateca, preservando as pastas.
3. Revise o diff antes de qualquer commit:

   git diff -- web/js/pages/organizationPage.js
   git diff -- web/css/pages/organization.css
   git diff --check

4. Rode as validações do projeto.
5. Abra cada subtab do menu Organização e valide visualmente antes de commit/push.

Validação feita no pacote
-------------------------
- node --check web/js/pages/organizationPage.js: OK
- nenhum arquivo de backend/API/router incluído

Observação importante
---------------------
Os números e detalhes que não existem na interface atual não foram inventados.
O layout mantém a riqueza visual da referência, mas usa os estados e ações que o
frontend atual consegue representar.


| Funcionalidade antiga                       | Backend/ação existente                                         | Nova tela mais adequada                         | Reuso                                  |
| ------------------------------------------- | -------------------------------------------------------------- | ----------------------------------------------- | -------------------------------------- |
| **Catalogar biblioteca**                    | `catalog_scan` → `scripts/scan.py`                             | **Rastrear biblioteca**                         | **Alto**                               |
| **Obras Fora do Catálogo**                  | `/api/catalog`, `catalog_single_work()`, `catalogPendingItems` | **Rastrear biblioteca** + **Revisar estrutura** | **Alto**                               |
| **Organização de Pastas — Preview**         | `organization_preview` → `scripts/organize.py`                 | **Organizar pastas**                            | **Muito alto**                         |
| **Organização de Pastas — Aplicar**         | `apply_organization` → `scripts/organize.py --apply`           | **Aplicar organização**                         | **Muito alto**                         |
| **Padronização — Preview**                  | `rename_preview` → `scripts/rename_files.py`                   | **Padronizar nomes**                            | **Muito alto**                         |
| **Padronização — Aplicar**                  | `apply_renaming` → `scripts/rename_files.py --apply`           | **Aplicar organização**                         | **Muito alto**                         |
| **Auditoria de capítulos**                  | `chapter_audit` → `scripts/chapter_audit.py`                   | **Validar capítulos**                           | **Muito alto**                         |
| **Registrar ajuste da revisão**             | `POST /api/review-notes` → `save_review_note()`                | **Revisar pendências**                          | **Médio**                              |
| **Pendências acionáveis**                   | `/api/pending` → `pending_payload()`                           | **Revisar pendências**                          | **Alto**, mas mistura domínios         |
| **Correspondências pendentes MangaUpdates** | `decision_queue`, endpoints `/api/mangaupdates/decisions/*`    | **Não deveria ser núcleo de Organização local** | **Baixo para as novas páginas locais** |
| **Catalogar Tudo / Catalogar obra**         | `catalog_scan` / `/api/catalog/catalog-one`                    | **Rastrear biblioteca**                         | **Alto**                               |
