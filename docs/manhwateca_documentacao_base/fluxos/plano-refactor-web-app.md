# Plano de refactor do frontend web

## Objetivo

Reduzir o arquivo `web/js/app.js` para um bootstrap de inicializacao, roteamento e composicao de modulos, sem alterar comportamento funcional existente.

O refactor deve preservar:

- chamadas atuais de API;
- navegacao entre paginas;
- execucao de tarefas;
- fluxos oficiais via `/api/flows/...`;
- telas de biblioteca, MangaUpdates, Notion, organizacao e visao geral;
- mensagens, feedbacks, filtros, paginacao e estados visuais existentes.

## Regra principal

Cada milestone deve mover codigo para arquivos menores sem mudar regra de negocio.

Quando uma regra precisar mudar, isso deve virar uma entrega separada, fora deste refactor.

## Arquitetura alvo

```text
web/js
├── app.js
├── router.js
├── layout
│   └── sidebar.js
├── api
│   ├── client.js
│   ├── flowsApi.js
│   ├── libraryApi.js
│   ├── mangaupdatesApi.js
│   ├── notionApi.js
│   └── tasksApi.js
├── components
│   ├── emptyState.js
│   ├── modal.js
│   ├── pagination.js
│   ├── statusBadge.js
│   └── toast.js
├── pages
│   ├── overviewPage.js
│   ├── flowsPage.js
│   ├── libraryPage.js
│   ├── mangaupdatesPage.js
│   ├── notionPage.js
│   ├── organizationPage.js
│   └── editorialPage.js
├── tasks
│   ├── pendingActions.js
│   ├── taskRunner.js
│   └── taskToast.js
├── state
│   └── appState.js
└── utils
    ├── dom.js
    ├── format.js
    └── html.js
```

## Estado desejado do `app.js`

O `app.js` deve ficar responsavel apenas por:

- importar modulos;
- capturar elementos raiz do DOM ou delegar essa captura;
- inicializar layout;
- inicializar router;
- inicializar paginas;
- conectar dependencias entre modulos;
- disparar carregamentos iniciais.

Meta de tamanho:

- ideal: 120 a 250 linhas;
- aceitavel na primeira conclusao: ate 350 linhas;
- nao aceitavel: manter regras completas de pagina dentro de `app.js`.

## Milestone 1 — Router e layout

Status: concluida

### Escopo

Mover para `web/js/router.js`:

- `showPage`;
- leitura inicial do `location.hash`;
- atualizacao de titulo, subtitulo e eyebrow;
- ativacao de botoes `[data-page]`;
- navegacao programatica entre paginas.

Mover para `web/js/layout/sidebar.js`:

- estado collapsed da sidebar;
- persistencia em `localStorage`;
- `menuToggle`;
- `sidebarToggle`;
- fechamento da sidebar ao trocar de pagina.

### Criterios de aceite

- Navegacao por menu continua funcionando.
- Navegacao por hash continua funcionando.
- Sidebar recolhida continua persistindo apos reload.
- Menu mobile continua abrindo e fechando.
- `app.js` nao contem mais logica interna de sidebar.

### Validacao

```bash
node --check web/js/app.js
node --check web/js/router.js
node --check web/js/layout/sidebar.js
```

### Resultado

- `showPage` movido para `web/js/router.js`.
- Leitura inicial de `location.hash` movida para `web/js/router.js`.
- Listeners de `[data-page]` movidos para `web/js/router.js`.
- Controle de sidebar movido para `web/js/layout/sidebar.js`.
- Persistencia de sidebar recolhida mantida em `localStorage`.
- Fechamento da sidebar ao trocar de pagina conectado via `onPageChange`.

## Milestone 2 — Tarefas e execucoes

Status: concluida

### Escopo

Mover para `web/js/tasks/taskRunner.js`:

- `confirmTask`;
- `startTask`;
- `renderTask`;
- `renderTaskMetrics`;
- `taskNextStep`;
- `taskCompletionSummary`;
- `loadTasks`;
- listeners do historico de tarefas.

Mover para `web/js/tasks/taskToast.js`:

- `updateTaskToast`;
- exibicao de progresso;
- link para resultado;
- botao de acompanhamento.

Mover para `web/js/tasks/pendingActions.js`:

- `handlePendingClick`;
- `pendingRequiresConfirmation`;
- integracao com navegacao e tarefas.

### Criterios de aceite

- Acoes continuam iniciando tarefas.
- Confirmacoes continuam aparecendo quando necessario.
- Toast de tarefa continua atualizando.
- Historico de tarefas continua renderizando.
- Progresso e links de relatorio continuam funcionando.
- Atualizacoes de pendencias continuam sendo recarregadas apos tarefas.

### Validacao

```bash
node --check web/js/tasks/taskRunner.js
node --check web/js/tasks/taskToast.js
node --check web/js/tasks/pendingActions.js
node --check web/js/app.js
```

### Resultado

- `confirmTask`, `startTask`, `renderTask`, `renderTaskMetrics`, `taskNextStep`, `taskCompletionSummary` e `loadTasks` movidos para `web/js/tasks/taskRunner.js`.
- Atualizacao do toast de tarefas movida para `web/js/tasks/taskToast.js`.
- Clique em pendencias e regra `pendingRequiresConfirmation` movidos para `web/js/tasks/pendingActions.js`.
- `app.js` passou a receber apenas `startTask`, `loadTasks` e `goToNextStep` do modulo de tarefas.
- Recargas apos tarefas continuam injetadas por callbacks, sem acoplamento circular entre paginas.

## Milestone 3 — LibraryPage

Status: concluida

### Escopo

Mover para `web/js/pages/libraryPage.js`:

- `loadCatalog`;
- `renderCatalog`;
- `summaryCard`;
- `renderChanges`;
- `explainIssue`;
- busca no catalogo;
- clique em itens do catalogo;
- reconciliacao/catalogacao pontual quando estiver relacionada a biblioteca.

### Criterios de aceite

- Catalogo carrega normalmente.
- Busca continua filtrando.
- Cards de obra continuam iguais.
- Botoes de problema/detalhes continuam funcionando.
- Nenhuma chamada de catalogo fica solta em `app.js`.

### Validacao

```bash
node --check web/js/pages/libraryPage.js
node --check web/js/app.js
```

### Resultado

- `loadCatalog`, `renderCatalog`, `renderChanges` e `explainIssue` movidos para `web/js/pages/libraryPage.js`.
- Busca do catalogo e clique nos alertas de obra movidos para `web/js/pages/libraryPage.js`.
- `summaryCard` movido para `web/js/components/summaryCard.js`, pois e usado por varias paginas.
- `app.js` passou a receber apenas `loadCatalog` da pagina de Biblioteca.
- Pendencias de catalogacao da tela de Organizacao permaneceram no `app.js` temporariamente, pois pertencem a Milestone 6.

## Milestone 4 — MangaUpdatesPage

Status: concluida

### Escopo

Mover para `web/js/pages/mangaupdatesPage.js`:

- `loadIdReview`;
- `loadMangaUpdatesStatus`;
- `reviewMarkup`;
- `renderReview`;
- `renderReviewSummary`;
- `candidateCard`;
- `cacheList`;
- decisoes de IDs;
- busca direta na API;
- traducao;
- aplicacao de decisoes.

### Criterios de aceite

- Revisao de IDs continua carregando.
- Busca por candidatos continua funcionando.
- Decisoes continuam sendo armazenadas antes de aplicar.
- Aplicacao de decisoes continua chamando a API correta.
- Status/cache do MangaUpdates continua renderizando.
- Nada desta pagina depende de logica interna de `app.js`.

### Validacao

```bash
node --check web/js/pages/mangaupdatesPage.js
node --check web/js/app.js
```

### Resultado

- Revisao de IDs movida para `web/js/pages/mangaupdatesPage.js`.
- Busca direta na API MangaUpdates movida para `web/js/pages/mangaupdatesPage.js`.
- Traducao de descricoes movida para `web/js/pages/mangaupdatesPage.js`.
- Aplicacao de decisoes movida para `web/js/pages/mangaupdatesPage.js`.
- Status/cache MangaUpdates movido para `web/js/pages/mangaupdatesPage.js`.
- Areas espelhadas da Organizacao para revisao de IDs continuam atendidas pelo mesmo modulo.
- `app.js` passou a receber apenas `loadIdReview` e `loadMangaUpdatesStatus`.

## Milestone 5 — NotionPage

Status: concluida

### Escopo

Mover para `web/js/pages/notionPage.js`:

- `loadNotionStatus`;
- `notionList`;
- `renderNotionSyncStatus`;
- `updateNotionActionAvailability`;
- `loadMetadataStatus`;
- `renderMetadataUpdates`;
- `renderSyncStateSummary`;
- listeners de refresh.

### Criterios de aceite

- Status do Notion continua carregando.
- Listas de pendencias continuam renderizando.
- Estado de sincronizacao continua correto.
- Metadados continuam carregando.
- Acoes dependentes do Notion continuam habilitando/desabilitando corretamente.

### Validacao

```bash
node --check web/js/pages/notionPage.js
node --check web/js/app.js
```

### Resultado

- `loadNotionStatus`, `notionList`, `renderNotionSyncStatus` e `updateNotionActionAvailability` movidos para `web/js/pages/notionPage.js`.
- `loadMetadataStatus`, `renderMetadataUpdates` e `renderSyncStateSummary` movidos para `web/js/pages/notionPage.js`.
- Clique no status de sincronizacao do Notion movido para `web/js/pages/notionPage.js`.
- Estado `notionUncataloged` e `notionStatusStale` encapsulado em `NotionPage`.
- `app.js` passou a receber apenas `loadNotionStatus`, `loadMetadataStatus` e `getNotionUncataloged`.
- Pendencias de catalogacao da Organizacao permaneceram no `app.js` temporariamente, pois pertencem a Milestone 6.

## Milestone 6 — OrganizationPage

Status: concluida

### Escopo

Mover para `web/js/pages/organizationPage.js`:

- pendencias de catalogacao da organizacao;
- paginacao de pendencias;
- filtros/listeners especificos da tela de organizacao;
- integracao com acoes antigas de organizacao sem alterar o fluxo antigo.

### Criterios de aceite

- Organizacao antiga continua acessivel.
- Pendencias da organizacao continuam paginando.
- Acoes de organizacao continuam passando pelo sistema de tarefas.
- Tela de Fluxos continua sem itens 1 e 2.

### Validacao

```bash
node --check web/js/pages/organizationPage.js
node --check web/js/app.js
```

### Resultado

- Pendencias de catalogacao da Organizacao movidas para `web/js/pages/organizationPage.js`.
- Paginacao de pendencias movida para `web/js/pages/organizationPage.js`.
- Acao de catalogar uma obra individual movida para `web/js/pages/organizationPage.js`.
- Refresh/reconciliacao de aliases movidos para `web/js/pages/organizationPage.js`.
- Botao de catalogacao em massa conectado dentro de `OrganizationPage`.
- `NotionPage` passou a enviar dados de obras nao catalogadas para `OrganizationPage` por callback.
- `app.js` nao contem mais logica interna de pendencias de catalogacao.

## Milestone 7 — EditorialPage

Status: concluida

### Escopo

Mover para `web/js/pages/editorialPage.js`:

- `loadEditorial`;
- `renderEditorial`;
- `editorialCard`;
- `matchesEditorialFilter`;
- `optionTags`;
- filtros;
- busca;
- submit de alteracoes editoriais.

### Criterios de aceite

- Dados editoriais continuam carregando.
- Filtros continuam funcionando.
- Busca continua funcionando.
- Salvamento continua chamando a API correta.
- Feedback visual continua aparecendo.

### Validacao

```bash
node --check web/js/pages/editorialPage.js
node --check web/js/app.js
```

### Resultado

- `loadEditorial`, `renderEditorial`, `editorialCard`, `matchesEditorialFilter` e `optionTags` movidos para `web/js/pages/editorialPage.js`.
- Filtros, busca e submit editorial movidos para `web/js/pages/editorialPage.js`.
- Salvamento editorial continua recarregando o catalogo por callback `onSaved`.
- `app.js` passou a receber apenas `loadEditorial`.

## Milestone 8 — App.js final

Status: concluida

### Escopo

Remover do `app.js` qualquer funcao que ainda represente regra de pagina.

O arquivo final deve conter apenas:

- imports;
- inicializacao de modulos;
- wiring entre paginas, router e tasks;
- carregamento inicial.

### Criterios de aceite

- `app.js` abaixo de 350 linhas.
- Nenhuma funcao grande de renderizacao permanece em `app.js`.
- Nenhum listener complexo permanece em `app.js`.
- Todas as paginas possuem modulo proprio.
- Todas as tarefas possuem modulo proprio.

### Validacao

```bash
node --check web/js/app.js
for file in web/js/api/*.js web/js/components/*.js web/js/pages/*.js web/js/tasks/*.js web/js/layout/*.js web/js/state/*.js web/js/utils/*.js web/js/router.js; do
  node --check "$file" || exit 1
done
```

### Resultado

- Renderizacao e listeners de acoes movidos para `web/js/pages/actionsPage.js`.
- Formulario de observacao editorial movido para `web/js/pages/editorialPage.js`.
- `app.js` ficou responsavel apenas por imports, captura de elementos, inicializacao de modulos e carregamento inicial.
- `app.js` ficou abaixo de 350 linhas.

## Checkpoints obrigatorios por milestone

Antes de cada milestone:

```bash
git status --short web
wc -l web/js/app.js
```

Depois de cada milestone:

```bash
node --check web/js/app.js
for file in web/js/api/*.js web/js/components/*.js web/js/pages/*.js web/js/state/*.js web/js/utils/*.js; do
  node --check "$file" || exit 1
done
wc -l web/js/app.js
git diff --stat -- web
```

## Regras para evitar perda de codigo

- Mover uma area por vez.
- Depois de mover, remover do `app.js` apenas o codigo ja coberto pelo novo modulo.
- Nao renomear comportamento e extrair codigo na mesma etapa quando isso aumentar risco.
- Manter nomes de funcoes equivalentes durante a extracao.
- Evitar alterar HTML junto com extracao JS, exceto quando estritamente necessario.
- Nao alterar backend durante este refactor.
- Nao alterar contratos de API durante este refactor.
- Nao alterar regras de Fluxos durante este refactor.
- Nao misturar mudancas visuais de CSS com extracao de JS, exceto imports/paths necessarios.

## Ordem recomendada de commits

1. `refactor: extract web router and sidebar`
2. `refactor: extract web task modules`
3. `refactor: extract library page module`
4. `refactor: extract mangaupdates page module`
5. `refactor: extract notion page module`
6. `refactor: extract organization page module`
7. `refactor: extract editorial page module`
8. `refactor: reduce web app bootstrap`

## Definicao de pronto

O refactor sera considerado concluido quando:

- `web/js/app.js` estiver abaixo de 350 linhas;
- todas as paginas tiverem modulo dedicado;
- tarefas estiverem fora de `app.js`;
- layout e router estiverem fora de `app.js`;
- todos os arquivos JS passarem em `node --check`;
- a navegacao e os fluxos principais continuarem funcionando manualmente no navegador.
