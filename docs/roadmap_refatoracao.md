# Roadmap de Refatoração do Núcleo

## Objetivo

Reorganizar o projeto em módulos menores, coesos e reutilizáveis, preparando o
núcleo para a futura aplicação web sem alterar o comportamento atual.

A refatoração deve preservar integralmente:

- os comandos executados pelo terminal;
- as opções e subopções de `scripts/menu.py`;
- argumentos de linha de comando;
- arquivos JSON, CSV e HTML gerados;
- caminhos utilizados por documentação e integrações;
- regras de organização, catalogação, MangaUpdates e Notion;
- confirmações antes de ações destrutivas;
- retomada de lotes e caches;
- testes automatizados existentes.

## Regra principal

Cada milestone deve terminar com o sistema funcional.

Não será permitido iniciar o milestone seguinte quando:

- algum teste estiver falhando;
- algum comando público tiver mudado;
- um relatório estiver diferente sem justificativa;
- uma simulação produzir resultados divergentes;
- houver regressão no menu do terminal.

## Política de tamanho

Arquivos com mais de 170 linhas devem ser avaliados para desmembramento.

O limite de 170 linhas é um sinal de revisão, não uma divisão automática.
Um arquivo poderá permanecer maior somente quando:

- possuir uma responsabilidade única e clara;
- a divisão gerar dependências artificiais;
- as funções forem fortemente relacionadas;
- houver justificativa registrada no código ou na revisão.

Ao desmembrar, cada módulo deverá representar uma responsabilidade concreta,
como busca, parsing, planejamento, execução, persistência ou apresentação.

## Situação atual

Os maiores scripts são:

| Script | Linhas aproximadas |
| ------ | -----------------: |
| `scripts/rename_files.py` | 1165 |
| `scripts/organize.py` | 1083 |
| `scripts/mangaupdates.py` | 961 |
| `scripts/id_review.py` | 688 |
| `scripts/menu.py` | 446 |
| `scripts/sync.py` | 426 |
| `scripts/utils.py` | 351 |
| `scripts/notion_csv.py` | 226 |
| `scripts/scan.py` | 208 |

Esses números indicam mistura de responsabilidades, especialmente quando o
mesmo arquivo contém regra de negócio, acesso externo, persistência, HTML e
interface de terminal.

## Arquitetura proposta

```text
Manhwateca/
├── manhwateca/
│   ├── __init__.py
│   ├── catalog/
│   ├── mangaupdates_service/
│   ├── notion_sync/
│   ├── library_organizer/
│   ├── file_normalizer/
│   ├── reporting/
│   └── shared/
├── scripts/
│   ├── menu.py
│   ├── scan.py
│   ├── mangaupdates.py
│   ├── id_review.py
│   ├── sync.py
│   ├── notion_csv.py
│   ├── organize.py
│   └── rename_files.py
├── tests/
├── config/
├── data/
└── reports/
```

Os arquivos em `scripts/` permanecerão como fachadas de linha de comando.
Eles deverão:

1. interpretar os argumentos;
2. validar parâmetros básicos;
3. chamar o serviço correspondente;
4. formatar a saída para o terminal;
5. retornar o código de saída apropriado.

As regras de negócio ficarão no pacote `manhwateca/`.

## Convenção de nomes

Para evitar colisões entre arquivo e pacote:

```text
scripts/mangaupdates.py
manhwateca/mangaupdates_service/
```

Outros exemplos:

```text
scripts/sync.py
manhwateca/notion_sync/

scripts/organize.py
manhwateca/library_organizer/

scripts/rename_files.py
manhwateca/file_normalizer/
```

Os scripts atuais não serão renomeados durante a refatoração. Isso preserva o
menu, a documentação e comandos já conhecidos.

## Contratos de compatibilidade

Antes de mover código, devem ser registrados os contratos públicos.

### Comandos

Exemplos que devem continuar funcionando:

```bash
python scripts/menu.py
python scripts/scan.py
python scripts/organize.py
python scripts/organize.py --apply
python scripts/rename_files.py
python scripts/rename_files.py --apply
python scripts/mangaupdates.py --fill-ids ...
python scripts/id_review.py
python scripts/sync.py --simulate-batch
python scripts/sync.py --apply-batch
python scripts/sync.py --update-existing
python scripts/notion_csv.py
python scripts/notion_csv.py --apply
```

### Arquivos

Os caminhos abaixo deverão permanecer estáveis:

```text
data/mangas.json
data/mangaupdates.json
data/mangaupdates_progress.json
reports/audits/
reports/integrations/buscaIds.json
reports/integrations/manhwateca_import.csv
reports/integrations/notion_import_status.json
reports/logs/
reports/reviews/
```

### Saídas

Devem ser preservados:

- códigos de saída;
- mensagens importantes usadas pelo menu;
- resumos de simulação;
- bloqueios de conflito e duplicidade;
- criação automática das pastas de relatórios;
- formatos dos arquivos persistidos.

## Estratégia de migração

Cada função deverá seguir esta sequência:

1. Criar ou ampliar testes do comportamento atual.
2. Copiar a função para o módulo de destino.
3. Alterar o script para importar a nova função.
4. Remover a implementação antiga.
5. Executar testes unitários do domínio.
6. Executar a suíte completa.
7. Executar comandos de simulação.
8. Comparar artefatos antes e depois.
9. Fazer um commit exclusivo do milestone.

Não mover múltiplos domínios no mesmo commit.

## Política econômica de testes

Durante a refatoração, a validação será proporcional ao risco para evitar
trabalho e consumo desnecessários:

- executar primeiro somente os testes relacionados ao módulo alterado;
- criar poucos testes de caracterização para regras críticas ainda sem
  cobertura;
- usar fixtures e mocks em vez de chamadas reais ao MangaUpdates e ao Notion;
- executar smoke tests apenas em modo de simulação;
- rodar a suíte completa ao concluir cada milestone, não após cada pequena
  extração;
- não buscar cobertura de 100% neste momento;
- não criar snapshots extensos quando uma comparação estrutural menor for
  suficiente.

Uma alteração documental não exige a execução da suíte. Uma extração interna
sem mudança de comportamento exige os testes do domínio afetado. Mudanças em
contratos compartilhados, formatos persistidos ou integrações exigem a suíte
completa ao final do milestone.

## Milestone 0: Baseline e proteção contra regressões

### Objetivo

Registrar o comportamento atual antes da reorganização.

### Atividades

- Listar todos os comandos públicos.
- Registrar argumentos e códigos de saída.
- Mapear arquivos lidos e gravados por cada script.
- Criar fixtures pequenas de biblioteca.
- Criar snapshots estruturais dos relatórios.
- Cobrir funções ainda sem testes.
- Registrar a contagem inicial da suíte.
- Criar uma matriz de dependências entre scripts.

### Entregáveis

```text
docs/contratos_cli.md
tests/fixtures/
tests/integration/
```

### Critérios de aceite

- Os comandos críticos possuem ao menos um teste ou smoke test documentado.
- A suíte completa está verde.
- Simulações de organização, renomeação e Notion estão documentadas.
- Nenhum arquivo de produção foi reorganizado ainda.

## Milestone 1: Pacote base e utilitários compartilhados

**Status:** concluído em 12 de junho de 2026.

Foram criados os módulos compartilhados de caminhos, títulos, capítulos,
intervalos, classificação de tamanho, mídia e duplicidades. O arquivo
`scripts/utils.py` permanece como fachada para os imports antigos.

Validação focada executada:

- 10 testes de utilidades;
- 7 testes de organização;
- 25 testes de padronização de arquivos;
- compilação dos módulos extraídos;
- carregamento dos comandos `organize.py --help` e
  `rename_files.py --help`.

### Objetivo

Criar a estrutura `manhwateca/` e mover funções realmente compartilhadas.

### Estrutura

```text
manhwateca/
├── __init__.py
└── shared/
    ├── __init__.py
    ├── paths.py
    ├── json_files.py
    ├── titles.py
    ├── chapters.py
    └── ranges.py
```

### Origem provável

```text
scripts/utils.py
scripts/report_utils.py
```

### Responsabilidades

- normalização Unicode;
- aliases e títulos canônicos;
- leitura e escrita atômica de JSON;
- variáveis de ambiente e caminhos;
- parsing de capítulos;
- compactação de intervalos.

### Compatibilidade

`scripts/utils.py` poderá permanecer temporariamente como módulo de
compatibilidade, reexportando as funções:

```python
from manhwateca.shared.chapters import scan_chapters
```

### Critérios de aceite

- Imports antigos continuam funcionando.
- Nenhuma regra muda.
- `scripts/scan.py`, `organize.py` e `rename_files.py` continuam funcionais.
- Arquivos do pacote ficam preferencialmente abaixo de 170 linhas.

## Milestone 2: Catalogação

**Status:** concluído em 12 de junho de 2026.

O comando `scripts/scan.py` foi mantido como fachada pública. Descoberta de
pastas, leitura do cache externo, montagem das obras e persistência do catálogo
foram movidas para `manhwateca/catalog/`.

Foram adicionados quatro testes focados para descoberta, progresso de leitura,
divergência com MangaUpdates e gravação do catálogo.

### Objetivo

Separar descoberta de pastas, análise de capítulos e montagem do catálogo.

### Estrutura

```text
manhwateca/catalog/
├── __init__.py
├── discovery.py
├── scanner.py
├── progress.py
├── sizing.py
├── external_data.py
└── repository.py
```

### Distribuição

- `discovery.py`: localizar pastas de obras.
- `scanner.py`: coordenar a varredura.
- `progress.py`: último lido e próximo a ler.
- `sizing.py`: Curto, Médio, Grande e Longo.
- `external_data.py`: incorporar cache MangaUpdates.
- `repository.py`: salvar `data/mangas.json`.

### Fachada

```text
scripts/scan.py
```

Deverá apenas configurar argumentos, chamar o scanner e imprimir o resumo.

### Critérios de aceite

- As mesmas obras são detectadas.
- Contagens e classificações permanecem iguais.
- `data/mangas.json` mantém o mesmo formato.
- `python scripts/scan.py` permanece funcional.

## Milestone 3: MangaUpdates Service

**Status:** concluído em 12 de junho de 2026.

Extrações concluídas:

- `client.py`: comunicação HTTP, retentativas e limite de requisições;
- `repository.py`: leitura e escrita JSON;
- `matching.py`: normalização, ranking e confirmação automática;
- `details.py`: transformação da ficha da API.
- `candidates.py`: busca, filtros e atualização de `buscaIds.json`;
- `csv_export.py`: montagem e gravação da base CSV;
- `csv_update.py`: atualização incremental sem apagar campos editoriais;
- `cache.py`: retomada, consulta de detalhes e cache local;
- `parser.py` e `cli.py`: argumentos, validação e apresentação do terminal;
- `candidate_workflows.py`: processamento em lotes e retomada de candidatos.

O script público continua expondo os nomes antigos para preservar o menu, os
comandos existentes e os mocks dos testes.

`scripts/mangaupdates.py` permanece acima da meta preferencial de 170 linhas
porque funciona como fachada de compatibilidade. Seus wrappers mantêm pontos
de substituição usados pelos testes e pelas chamadas atuais. A lógica de
negócio foi removida do arquivo; reduzir apenas a contagem exigiria esconder
dependências ou quebrar os mocks existentes.

### Objetivo

Dividir `scripts/mangaupdates.py` por responsabilidade.

### Estrutura

```text
manhwateca/mangaupdates_service/
├── __init__.py
├── client.py
├── models.py
├── search.py
├── ranking.py
├── matching.py
├── candidates.py
├── details.py
├── cache.py
├── csv_export.py
├── progress.py
└── service.py
```

### Distribuição

- `client.py`: HTTP, delay e erros da API.
- `search.py`: chamadas ao endpoint de busca.
- `ranking.py`: score e ordenação.
- `matching.py`: confirmação automática e aliases.
- `candidates.py`: atualização de `buscaIds.json`.
- `details.py`: consulta de ficha por ID.
- `cache.py`: `data/mangaupdates.json`.
- `csv_export.py`: geração e atualização do CSV.
- `progress.py`: retomada e lotes.
- `service.py`: casos de uso consumidos por CLI e web.

### Fachada

```text
scripts/mangaupdates.py
```

Todos os argumentos atuais deverão permanecer disponíveis.

### Critérios de aceite

- Busca, score, filtro BL e IDs manuais não mudam.
- Delay e tamanho dos lotes são preservados.
- Cache e retomada continuam funcionando.
- O CSV permanece compatível.
- Nenhum módulo do serviço concentra API, CSV e matching ao mesmo tempo.

## Milestone 4: Revisão de IDs e relatórios

**Status:** concluído em 12 de junho de 2026.

Extrações concluídas:

- `review/decisions.py`: validação, aplicação e backup das decisões;
- `review/data.py`: consolidação de aliases, CSV e cache;
- `review/rendering.py`: renderização dos cartões de candidatos;
- `review/parser.py`: argumentos do comando;
- `review/service.py`: geração do arquivo e fluxo do terminal;
- `review/report.py`: documento HTML autocontido da revisão.

`scripts/id_review.py` permanece como fachada pública de 14 linhas.

`review/report.py` ultrapassa 170 linhas por conter o HTML, CSS e JavaScript
autocontidos do relatório. A exceção é intencional: separar esses trechos
exigiria um sistema de templates e ativos externos, alterando a portabilidade
do relatório. Essa melhoria poderá ser avaliada no milestone compartilhado de
relatórios.

### Objetivo

Separar o domínio de decisões da renderização HTML.

### Estrutura

```text
manhwateca/mangaupdates_service/review/
├── __init__.py
├── decisions.py
├── consolidation.py
├── importer.py
└── report.py
```

### Distribuição

- `decisions.py`: modelo e validação.
- `consolidation.py`: aliases, confirmados e pendentes.
- `importer.py`: backup e aplicação.
- `report.py`: HTML, CSS e JavaScript.

### Fachada

```text
scripts/id_review.py
```

### Critérios de aceite

- O relatório mantém filtros e seleção manual.
- Obras confirmadas não reaparecem.
- Exportação e importação continuam compatíveis.
- Backups continuam sendo criados.
- O HTML gerado permanece funcional no navegador.

## Milestone 5: Organização da biblioteca

**Status:** concluído em 12 de junho de 2026.

Extrações concluídas:

- `library_organizer/grouping.py`: grupos alfabéticos e origem atual;
- `library_organizer/discovery.py`: detecção de obras e pastas vazias;
- `library_organizer/planning.py`: plano, conflitos e estados;
- `library_organizer/execution.py`: movimentação segura e histórico;
- `library_organizer/parser.py`: argumentos do comando;
- `library_organizer/workflow.py`: relatório autocontido e orquestração.

Os wrappers em `scripts/organize.py` preservam `MANGA_ROOT`, `DRY_RUN` e
`HISTORY_PATH`, permitindo que os testes e comandos existentes continuem
substituindo essas configurações. A fachada pública possui 18 linhas.

`workflow.py` permanece acima de 170 linhas porque aproximadamente 560 linhas
pertencem ao HTML, CSS e JavaScript autocontidos do relatório. A separação
desses ativos será tratada no milestone compartilhado de relatórios, evitando
introduzir agora um sistema de templates diferente para cada relatório.

### Objetivo

Dividir `scripts/organize.py`.

### Estrutura

```text
manhwateca/library_organizer/
├── __init__.py
├── discovery.py
├── grouping.py
├── planner.py
├── conflicts.py
├── duplicates.py
├── executor.py
├── history.py
└── report.py
```

### Distribuição

- descoberta de obras;
- definição do grupo alfabético;
- criação do plano;
- conflitos;
- duplicidades;
- movimentação segura;
- histórico JSONL;
- relatório HTML.

### Fachada

```text
scripts/organize.py
```

### Critérios de aceite

- Preview e aplicação produzem o mesmo plano.
- Conflitos continuam bloqueando a aplicação.
- Duplicidades continuam bloqueando a organização.
- Movimentações ausentes são tratadas sem perda de dados.
- Histórico permanece no mesmo formato.

## Milestone 6: Normalização de arquivos

**Status:** concluído em 12 de junho de 2026.

O comando `scripts/rename_files.py` foi reduzido a uma fachada de 18 linhas.
As regras de nomenclatura, agrupamento, planejamento, conflitos, duplicidades
e execução segura foram movidas para `manhwateca/file_normalizer/`.

O gerador HTML permanece temporariamente em `workflow.py`, junto da
coordenação do comando. Assim como no organizador, este arquivo é uma exceção
documentada ao limite de 170 linhas porque contém um relatório HTML
autossuficiente. A próxima evolução poderá mover esse template sem alterar as
regras já isoladas.

Foram preservados os patches históricos de `MANGA_ROOT` e `DRY_RUN`, além das
25 regras testadas de nomes, capas, conflitos e renomeações Unicode.

### Objetivo

Dividir `scripts/rename_files.py`.

### Estrutura

```text
manhwateca/file_normalizer/
├── __init__.py
├── parser.py
├── titles.py
├── chapters.py
├── covers.py
├── planner.py
├── conflicts.py
├── executor.py
└── report.py
```

### Distribuição

- parsing de nomes;
- normalização de título;
- intervalos e side stories;
- padronização de capas;
- plano de renomeação;
- conflitos;
- execução;
- relatório HTML.

### Fachada

```text
scripts/rename_files.py
```

### Critérios de aceite

- Todas as regras de nomes permanecem iguais.
- Preview e aplicação continuam separados.
- Capas continuam protegidas contra múltiplas imagens.
- Renomeações Unicode continuam seguras.
- Nenhum arquivo é sobrescrito em conflito.

## Milestone 7: Sincronização com Notion

**Status:** concluído em 12 de junho de 2026.

Os comandos `scripts/sync.py` e `scripts/notion_csv.py` foram reduzidos a
fachadas de 16 linhas. A sincronização foi dividida em módulos para matching,
paginação, propriedades do catálogo, propriedades do CSV, serviços,
repositórios e persistência do status.

Todos os módulos de `manhwateca/notion_sync/` ficaram abaixo de 170 linhas.
Foram preservadas as políticas distintas dos dois fluxos: o catálogo pode
criar páginas em lotes, enquanto o CSV atualiza apenas páginas existentes e
não apaga campos editoriais vazios.

Os 21 testes focados de sincronização e CSV foram mantidos sem chamadas reais
ao Notion.

### Objetivo

Separar cliente, matching, propriedades, lotes e persistência.

### Estrutura

```text
manhwateca/notion_sync/
├── __init__.py
├── client.py
├── schema.py
├── matching.py
├── properties.py
├── catalog_sync.py
├── metadata_sync.py
├── batches.py
└── status_repository.py
```

### Distribuição

- `client.py`: acesso ao Notion.
- `schema.py`: nomes e tipos das propriedades.
- `matching.py`: nome oficial, local e aliases.
- `properties.py`: payloads sem apagar campos editoriais.
- `catalog_sync.py`: criação e atualização do catálogo.
- `metadata_sync.py`: atualização usando CSV.
- `batches.py`: lotes de 25.
- `status_repository.py`: log de importação.

### Fachadas

```text
scripts/sync.py
scripts/notion_csv.py
```

### Critérios de aceite

- Simulação e aplicação continuam disponíveis.
- Lotes não criam duplicatas.
- Aliases e campos editoriais não são apagados.
- Nomes equivalentes continuam sendo reconhecidos.
- O esquema atual do Notion é validado.

## Milestone 8: Relatórios compartilhados

**Status:** concluído em 12 de junho de 2026.

Foi criado `manhwateca/reporting/` com estilos compartilhados, componentes,
montagem da página e escrita de arquivos. `scripts/report_utils.py` permanece
como fachada compatível para o relatório de capítulos.

A escrita comum passou a ser usada também pelos relatórios de organização,
renomeação e revisão de IDs. O conteúdo e o CSS específicos desses relatórios
continuam em seus próprios domínios, evitando uma migração visual ampla nesta
etapa.

Foram adicionados três testes mínimos para escape de conteúdo, preservação do
corpo específico e criação automática dos diretórios.

### Objetivo

Padronizar geração de HTML sem misturar regra de negócio.

### Estrutura

```text
manhwateca/reporting/
├── __init__.py
├── html.py
├── styles.py
├── components.py
└── files.py
```

### Escopo

- cabeçalhos;
- cards;
- tabelas;
- badges;
- filtros;
- criação de diretórios;
- escrita de arquivos.

### Limite

O conteúdo específico de cada relatório permanece no domínio correspondente.
O pacote compartilhado não deverá conhecer regras de MangaUpdates, capítulos
ou Notion.

### Critérios de aceite

- Relatórios continuam abrindo localmente.
- CSS comum não altera informações exibidas.
- Cada relatório mantém testes mínimos de conteúdo.

## Milestone 9: Menu e camada de aplicação

**Status:** concluído em 12 de junho de 2026.

O comando `scripts/menu.py` foi reduzido a uma fachada de 19 linhas. Cores e
textos, catálogo de comandos, persistência de notas, confirmações, operações,
submenus e laço principal foram separados em `manhwateca/application/`.

Todos os módulos da camada de aplicação ficaram abaixo de 170 linhas. As
funções públicas antigas continuam expostas pelo workflow para preservar os
testes e integrações existentes.

Os 25 testes do menu confirmam que as mesmas opções, comandos, confirmações e
interrupção na primeira falha continuam funcionando.

### Objetivo

Reduzir `scripts/menu.py` a apresentação e navegação.

### Estrutura

```text
manhwateca/application/
├── __init__.py
├── commands.py
├── confirmations.py
├── results.py
└── workflows.py
```

### Distribuição

- `commands.py`: catálogo de comandos disponíveis.
- `confirmations.py`: confirmações numéricas.
- `results.py`: resultado padronizado.
- `workflows.py`: fluxo completo e sequências.

### Fachada

```text
scripts/menu.py
```

### Critérios de aceite

- Ordem, cores e textos do menu permanecem consistentes.
- Todas as opções continuam chamando as mesmas operações.
- Confirmações destrutivas permanecem obrigatórias.
- O fluxo completo para na primeira falha.

## Milestone 10: Limpeza e documentação

**Status:** concluído em 12 de junho de 2026.

Foram removidas as implementações duplicadas que ainda existiam no workflow
de normalização e os imports internos do antigo `scripts/utils.py`.
`chapter_audit.py` e `import_catalog_metadata.py` também passaram a ser
fachadas para módulos importáveis do catálogo.

O README agora apresenta a estrutura modular, e `docs/arquitetura.md`
documenta responsabilidades, dependências, extensão por novas integrações e
as poucas exceções justificadas ao limite de 170 linhas.

### Objetivo

Remover compatibilidades temporárias e documentar a arquitetura final.

### Atividades

- Remover funções duplicadas.
- Remover imports de compatibilidade não utilizados.
- Verificar módulos acima de 170 linhas.
- Atualizar README e roadmaps.
- Criar mapa de dependências.
- Documentar como adicionar uma nova integração.
- Confirmar que `scripts/` contém somente fachadas.

### Critérios de aceite

- Nenhuma regra existe em dois lugares.
- Não há import circular.
- Scripts públicos continuam com os mesmos nomes.
- A aplicação web poderá importar serviços sem executar subprocessos.
- A suíte completa permanece verde.

## Validação obrigatória por milestone

### Testes automatizados

```bash
python -m unittest discover -s tests
```

### Comandos locais

```bash
python scripts/scan.py
python scripts/organize.py
python scripts/rename_files.py
python scripts/id_review.py
```

### Integrações em simulação

```bash
python scripts/sync.py --simulate-batch --batch-size 25
python scripts/notion_csv.py
```

MangaUpdates deverá usar cache, fixtures ou lotes pequenos para evitar
requisições desnecessárias durante a validação.

### Comparações

- quantidade de obras;
- planos de movimentação;
- planos de renomeação;
- conflitos e duplicidades;
- cabeçalhos e linhas do CSV;
- contagens dos relatórios;
- páginas encontradas no Notion;
- criações, atualizações e pendências.

## Estratégia de commits

Cada milestone deverá resultar em um commit próprio.

Exemplos:

```text
refactor: cria pacote compartilhado
refactor: modulariza catalogação
refactor: extrai serviço MangaUpdates
refactor: separa revisão de IDs
refactor: modulariza organização da biblioteca
refactor: modulariza normalização de arquivos
refactor: separa sincronização com Notion
refactor: simplifica menu do terminal
```

Não misturar no mesmo commit:

- refatoração estrutural;
- mudança de regra;
- alteração visual;
- migração de dados;
- nova funcionalidade.

## Riscos principais

### Imports e execução direta

Executar:

```bash
python scripts/arquivo.py
```

tem comportamento de import diferente de executar um pacote. Os scripts
deverão adicionar a raiz do projeto de forma controlada ou o projeto deverá
ser instalável em modo editável.

### Colisões de nomes

Evitar:

```text
scripts/mangaupdates.py
scripts/mangaupdates/
```

Preferir:

```text
scripts/mangaupdates.py
manhwateca/mangaupdates_service/
```

### Dependências circulares

Domínios não devem importar fachadas de `scripts/`.

Fluxo permitido:

```text
scripts → application/services → shared
```

Fluxo proibido:

```text
shared → scripts
service A ↔ service B
```

### Mudanças acidentais de comportamento

Ao mover código, não aproveitar para melhorar regras. Melhorias funcionais
devem ser feitas depois, em commits separados.

## Relação com a aplicação web

Este roadmap deve ser concluído antes dos milestones principais de
`docs/roadmap_aplicacao_web.md`.

Após a refatoração:

```text
Terminal ─┐
          ├── manhwateca/application e services
Web API ──┘
```

O terminal e a aplicação web usarão as mesmas funções, evitando regras
duplicadas e resultados divergentes.

## Primeiro passo recomendado

Executar somente o Milestone 0.

Antes de mover qualquer função:

1. registrar os contratos dos comandos;
2. ampliar testes de integração;
3. criar fixtures pequenas;
4. salvar resultados de referência;
5. confirmar a suíte completa.

Essa preparação reduz o risco de uma refatoração silenciosamente alterar
arquivos da biblioteca ou dados do Notion.

## Fase 2 planejada: Advisor de fluxo e estados acionáveis

**Status:** planejado. Não implementar neste momento.

Após o uso real da interface web, ficou claro que o núcleo modular já reduziu
duplicação técnica, mas ainda falta uma camada explícita para orientar a
usuária sobre o próximo passo correto.

O problema principal não é mais somente código duplicado. O problema atual é
que diferentes telas e comandos calculam pendências de formas diferentes:

- o comando pode dizer `Para revisão: 27`;
- a tela de revisão pode mostrar `A revisar: 0`;
- uma obra com `Status: Não encontrada` pode parecer pendente;
- uma ação pode continuar disponível mesmo quando não muda mais o estado;
- o histórico técnico pode virar o único feedback após uma execução.

Essa fase deve criar uma fonte única de verdade para estados e recomendações,
antes de novos ajustes visuais ou novas automações.

### Objetivo

Criar uma camada de orientação que leia os arquivos existentes, classifique o
estado real de cada fluxo e exponha ações recomendadas para terminal e web.

Essa camada deve responder perguntas como:

- existe algo realmente pesquisável no MangaUpdates?
- existe algo revisável na tela de IDs?
- existe ID confirmado sem detalhes?
- existe dado pronto para exportar ao CSV?
- existe obra no Drive fora do catálogo?
- existe página faltando no Notion?
- existe ação que deve ficar bloqueada porque não produzirá mudança?

### Componente proposto

```text
manhwateca/workflow_advisor/
├── __init__.py
├── mangaupdates_state.py
├── notion_state.py
├── catalog_state.py
└── recommendations.py
```

Responsabilidades:

- ler arquivos de estado atuais;
- classificar itens em estados acionáveis;
- gerar contadores consistentes;
- gerar recomendações com destino claro na interface;
- informar quando uma ação deve ser bloqueada ou desabilitada;
- ser usado pela interface web, pelo menu terminal e pelo painel de pendências.

### Estados mínimos do MangaUpdates

O primeiro domínio a entrar nessa fase deve ser o MangaUpdates, porque é onde
o loop de ação ficou mais evidente.

Estados sugeridos por obra:

```text
nao_pesquisada
nao_encontrada
revisao_acionavel
revisao_nao_acionavel
confirmada_sem_detalhes
detalhes_em_cache
pronta_para_csv
csv_atualizado
fora_do_catalogo
```

Regras importantes:

- `Não encontrada` não pode ser contada como pendente de lote.
- `Revisar` no JSON bruto não significa necessariamente item visível na tela.
- Uma ação só deve ser sugerida se houver item que ela possa alterar.
- Se a próxima ação for manual, a recomendação deve indicar a seção exata.

### Estados mínimos do Notion

Estados sugeridos:

```text
catalogo_desatualizado
obra_nao_catalogada
pagina_ausente
pagina_criada
metadados_pendentes
metadados_sincronizados
duplicada_no_notion
ausente_no_notion
```

Regras importantes:

- simular não deve ser apresentado como solução final;
- importar lote só deve aparecer quando a simulação indicar páginas ausentes;
- atualizar metadados só deve aparecer quando houver diff real;
- duplicidades devem bloquear aplicação e apontar para revisão.

### Entregáveis planejados

1. Criar inventário de estados do MangaUpdates.
2. Substituir contadores divergentes da web pelo inventário.
3. Desabilitar ações sem efeito, exibindo o motivo.
4. Atualizar `pending_actions.py` para usar recomendações do advisor.
5. Atualizar o histórico de tarefas para mostrar próximo passo vindo do advisor,
   não do `stdout`.
6. Estender o mesmo modelo para Notion.
7. Expor recomendações no menu terminal.
8. Atualizar README e `docs/arquitetura.md` após a estabilização.

### Critérios de aceite

- A mesma pendência não pode aparecer com números diferentes em telas distintas.
- Nenhum botão deve sugerir uma ação que não altera estado algum.
- Toda mensagem de ação deve indicar o destino exato: página, seção e ação.
- O histórico técnico deve continuar disponível, mas não ser a orientação
  principal.
- O terminal e a web devem usar a mesma classificação de estados.
- Testes devem cobrir pelo menos os estados críticos:
  - `Não encontrada`;
  - `Revisar` não acionável;
  - `Revisar` acionável;
  - confirmado sem detalhes;
  - pronto para CSV;
  - Notion com páginas pendentes;
  - Notion sem alterações.

### Fora do escopo inicial

- redesenhar a interface inteira;
- mudar formato dos arquivos JSON sem migração;
- alterar regras de matching do MangaUpdates;
- automatizar decisões manuais;
- remover o menu terminal.

### Sequência recomendada

1. Implementar somente `mangaupdates_state.py`.
2. Trocar a tela MangaUpdates para consumir esse estado.
3. Ajustar ações web para usar `enabled`, `disabled_reason` e `next_action`.
4. Atualizar o painel de pendências.
5. Só então levar o mesmo padrão para Notion.
