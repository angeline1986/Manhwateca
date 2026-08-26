MANHWATECA — PACOTE DE AJUSTES ACOMPANHAMENTO
Data: 26/08/2026

Escopo:
- Acompanhamento alinhado ao padrão espacial de Fluxos / Buscar candidatos.
- Page container da tela ativa com 16px de padding.
- Conteúdo operacional centralizado com largura máxima de 1180px.
- Espaço entre as duas grandes seções reduzido e controlado em 16px.
- Lançamentos recentes: paginação client-side de 5 itens por página.
- Busca, janela, favoritas e não visualizados resetam a paginação para a página 1.
- Botões Anterior/Próxima respeitam os limites.
- Coluna Grupo removida somente da tabela de Acompanhamento.
- Colspan e larguras da tabela ajustados para 4 colunas.
- Novo docs/frontend_page_standard.md documentando o padrão para futuras páginas.

Como aplicar:
1. Extraia este ZIP.
2. Copie apply_updates.py para a raiz do projeto Manhwateca (ou execute apontando o terminal para a raiz onde o script estiver).
3. Na raiz do projeto, execute:

   python apply_updates.py

O script cria backup automático em:
reports/patch_backups/acompanhamento_paginacao_padrao_20260826_<timestamp>/

Arquivos alterados pelo script:
- web/index.html
- web/js/app.js
- web/js/pages/trackingPage.js
- web/css/pages/releases.css
- docs/frontend_page_standard.md (novo/atualizado)

Não altera:
- backend/API
- banco/schema/migrations
- monitor de releases
- outras páginas
- docs/arquitetura.md

Observação importante:
O patch procura a coluna Grupo dentro do bloco #page-tracking, e não globalmente no index.html. Isso evita o erro de patch anterior causado por múltiplas ocorrências de um trecho semelhante.
