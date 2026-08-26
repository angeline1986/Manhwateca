MANHWATECA — AJUSTES ACOMPANHAMENTO
26/08/2026

Base revisada: branch main de
https://github.com/angeline1986/Manhwateca

Este pacote faz somente três ajustes:

1. Remove a coluna GRUPO da tabela de Lançamentos da página Acompanhamento.
   A tabela passa a ser:
   OBRA | CAPÍTULO | LANÇAMENTO | SITUAÇÃO

2. Adiciona paginação local de 5 lançamentos por página.
   A paginação respeita os filtros já existentes:
   janela de dias, busca, favoritas e não visualizados.
   Ao trocar um filtro, volta para a página 1.

3. Corrige o enquadramento externo da página Acompanhamento para copiar
   o padrão já estabelecido em Organização:
   page-container com 16px;
   conteúdo com largura máxima de 1180px;
   centralização automática.

Arquivos alterados:
- web/index.html
- web/js/pages/trackingPage.js
- web/css/pages/releases.css

Não altera backend, banco, migrations, ReleaseMonitor, favoritas, histórico
individual, slider, Dashboard ou Organização.

COMO APLICAR

Na raiz do Manhwateca:

  git status

Depois:

  python /caminho/do/pacote/apply_updates.py

Exemplo:

  python ~/Downloads/manhwateca_acompanhamento_tabela_paginacao_layout_20260826/apply_updates.py

O script cria backup automático em:
reports/patch_backups/acompanhamento_tabela_<data_hora>/

VALIDAÇÃO

  node --check web/js/pages/trackingPage.js
  git diff --check
  ./start_manhwateca.command

No navegador:
- confirme que GRUPO sumiu;
- confirme no máximo 5 linhas por página;
- confirme anterior/próxima;
- teste busca e filtros com mais de 5 resultados;
- confirme que trocar filtro volta à página 1;
- compare posição da página com Organização.

O patch é defensivo: se o código local divergir dos trechos revisados,
ele para sem tentar adivinhar alterações.
