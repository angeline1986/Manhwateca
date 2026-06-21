# Relatorio de Integracao Operacional PostgreSQL

Data: 2026-06-21

## Diagnostico tecnico

A fase de modelagem esta encerrada. O estado atual do projeto e de migracao
operacional: a estrutura PostgreSQL ja existe e deve ser usada como fonte
principal sempre que possivel, mantendo JSON e CSV apenas como compatibilidade
temporaria.

Fonte principal:

- PostgreSQL

Fonte secundaria:

- Notion

Legado:

- JSON
- CSV

Fila de decisoes:

- `decision_queue`

Views principais:

- `vw_mangas`
- `vw_next_reads`
- `vw_stats`

## Auditoria dos artefatos legados

| Artefato | Leitura atual | Escrita atual | Informacao armazenada | Equivalente PostgreSQL |
| --- | --- | --- | --- | --- |
| `data/mangas.json` | Web fallback, auditorias, sync legado, relatorios | Scanner | Catalogo tecnico local gerado a partir do Drive | `mangas`, `themes`, `manga_themes`, `vw_mangas` |
| `data/mangaupdates.json` | Scanner, MangaUpdates, CSV update | MangaUpdates details/cache | Cache de detalhes consultados por ID | campos em `mangas` e temas relacionados |
| `reports/integrations/buscaIds.json` | MangaUpdates, revisao manual, web | Busca de IDs, importacao de decisoes | Candidatos, IDs confirmados e revisoes | `decision_queue` + campos `work_code`/MangaUpdates em `mangas` |
| `reports/integrations/manhwateca_import.csv` | Notion metadata fallback, editorial legado | MangaUpdates CSV/export, editorial | Base enriquecida para publicar metadados no Notion | `vw_mangas` e `MangaRepository` |
| `config/catalog_metadata.json` | Scanner/editorial/MangaUpdates | Editorial | Correcoes editoriais locais | campos editoriais em `mangas` e temas |
| `reports/integrations/notion_import_status.json` | Web Notion/status | Sync catalogo -> Notion | Estado da importacao em lote | `notion_page_id`, `notion_sync_status`, `sync_events` |
| `reports/integrations/notion_csv_status.json` | Web Notion/status | Sync metadata -> Notion | Resultado da atualizacao por CSV | `sync_events` |

## O que foi encontrado

1. O scanner ja gera `data/mangas.json`, mas tambem tenta salvar no PostgreSQL
   quando `DATABASE_URL` esta disponivel.
2. A gravacao do scanner no PostgreSQL passa por `MangaRepository`, que preserva
   campos manuais e atualiza somente dados tecnicos do catalogo.
3. O painel da web ja consegue usar `active_catalog_source`, portanto o
   catalogo visual pode ler PostgreSQL e cair para JSON.
4. O sync de metadados do Notion ja usa modo `auto`, tentando PostgreSQL antes
   do CSV legado.
5. O sync de catalogo do Notion ainda usava `json` como fonte padrao.
6. MangaUpdates ainda depende de `buscaIds.json` para compatibilidade, mas a
   `decision_queue` ainda nao estava sendo usada por um fluxo real.
7. A importacao de decisoes de IDs ainda atualizava apenas o staging JSON.

## O que foi alterado

### Decision queue em fluxo real

MangaUpdates agora usa `decision_queue` em dois pontos:

1. Quando a busca de IDs encontra candidatos duvidosos, uma decisao do tipo
   `mangaupdates_match` e gravada ou atualizada na fila.
2. Quando uma decisao exportada pela revisao manual e importada, a decisao
   correspondente e marcada como resolvida na fila.

O JSON `buscaIds.json` continua sendo atualizado para compatibilidade com a
interface e os comandos existentes.

### Repository layer

Foram adicionadas operacoes genericas no `MangaRepository` para:

- enfileirar decisoes em `decision_queue`;
- resolver decisoes existentes;
- adaptar-se a nomes de colunas ja existentes na tabela sem exigir nova
  migration.

Nenhuma tabela nova foi criada.

### Editorial

O dashboard editorial passou a tentar PostgreSQL primeiro via `MangaRepository`
e cair para CSV legado apenas quando o banco estiver indisponivel.

### Sync catalogo -> Notion

O `catalog_workflow` passou a usar `--catalog-source auto` por padrao:

1. tenta ler `vw_mangas` via PostgreSQL;
2. se o banco nao estiver configurado ou indisponivel, usa `data/mangas.json`
   como fallback legado;
3. `--catalog-source json` continua disponivel para testes e compatibilidade.

## O que ainda depende de JSON

- Busca e revisao de IDs MangaUpdates ainda mantem
  `reports/integrations/buscaIds.json`.
- Cache de detalhes MangaUpdates ainda usa `data/mangaupdates.json`.
- Auditorias e relatorios locais ainda usam `data/mangas.json`.
- Alguns indicadores web ainda leem arquivos de status em `reports/`.

## O que ainda depende de CSV

- O fluxo de exportacao/enriquecimento MangaUpdates ainda escreve
  `reports/integrations/manhwateca_import.csv`.
- O fluxo CSV -> Notion continua disponivel como fallback e compatibilidade.
- Algumas telas e testes ainda validam o caminho CSV legado.

## O que ja usa PostgreSQL

- `MangaRepository.list_mangas()` via `vw_mangas`.
- `MangaRepository.list_next_reads()` via `vw_next_reads`.
- Scanner salva no banco quando disponivel.
- Web catalogo usa banco quando disponivel.
- Status MangaUpdates usa banco quando disponivel.
- Sync catalogo -> Notion agora tenta banco por padrao.
- Sync metadata -> Notion ja tenta banco por padrao.
- Campos de sync Notion usam `notion_page_id`, `notion_sync_status` e
  `sync_events`.
- `decision_queue` agora recebe decisoes reais de MangaUpdates.

## Arquivos alterados

- `manhwateca/catalog/editorial.py`
- `manhwateca/database/manga_repository.py`
- `manhwateca/mangaupdates_service/candidate_workflows.py`
- `manhwateca/mangaupdates_service/compatibility.py`
- `manhwateca/mangaupdates_service/review/decisions.py`
- `manhwateca/mangaupdates_service/review/report.py`
- `manhwateca/notion_sync/catalog_workflow.py`
- `tests/test_database.py`
- `tests/test_id_review.py`
- `tests/test_mangaupdates.py`
- `tests/test_sync.py`

## Riscos identificados

1. `decision_queue` agora e usada, mas a UI ainda mostra a revisao a partir do
   staging JSON. O proximo corte deve fazer a tela ler a fila diretamente.
2. `data/mangaupdates.json` ainda e o cache principal de detalhes externos.
3. `manhwateca_import.csv` ainda e necessario para compatibilidade e conferencia.
4. Campos editoriais ja podem ir para PostgreSQL, mas alguns fluxos ainda
   preservam CSV/JSON para nao quebrar a operacao atual.
5. A remocao completa de legado ainda nao deve acontecer.

## Atualizacao operacional

Em 2026-06-21, a tela web de revisao MangaUpdates passou a consultar
`decision_queue` como fonte primaria quando houver decisoes pendentes do tipo
`mangaupdates_match`.

Compatibilidade preservada:

- se o banco estiver indisponivel, a tela continua lendo `buscaIds.json`;
- se a fila estiver vazia, a tela ainda cai para `buscaIds.json`, evitando
  esconder decisoes antigas ainda nao migradas para a fila.

Isso inicia o corte:

```text
decision_queue
-> revisao MangaUpdates na web
-> buscaIds.json como fallback temporario
```

A aplicacao das decisoes tambem passou a usar a fila quando houver pendencias:

```text
decision_queue
-> decisao humana
-> work_code em mangas
-> decision_queue resolvida
-> buscaIds.json espelhado quando existir
```

## Pendencias restantes

1. Fazer o export/import legado de decisoes ser substituido por fluxo direto da
   web, sem exigir arquivo JSON baixado pelo navegador.
2. Migrar o cache MangaUpdates de `data/mangaupdates.json` para campos do banco
   ja existentes sempre que possivel.
3. Reduzir dependencia de `manhwateca_import.csv` nos fluxos de Notion.
4. Revisar indicadores web que ainda usam arquivos `reports/` como fonte
   principal.

## Arquivos que podem ser removidos futuramente

Somente depois de cada fluxo correspondente estar banco-primeiro:

| Arquivo | Condicao para remocao |
| --- | --- |
| `reports/integrations/buscaIds.json` | Revisao de IDs lendo e escrevendo `decision_queue`. |
| `data/mangaupdates.json` | Detalhes MangaUpdates persistidos no PostgreSQL. |
| `reports/integrations/manhwateca_import.csv` | Notion metadata lendo direto de `vw_mangas`/repository. |
| `data/mangas.json` | Auditorias, web e sync sem dependencia obrigatoria do JSON. |
| `config/catalog_metadata.json` | Editorial completamente persistido em `mangas` e temas. |

## Proximo corte seguro do legado

O proximo corte seguro e focar em MangaUpdates:

```text
MangaUpdates
-> decision_queue
-> revisao manual
-> PostgreSQL
-> JSON apenas como espelho temporario
```

Esse corte e seguro porque `decision_queue` ja existe, ja esta indexada e agora
ja recebe decisoes reais. O objetivo da proxima etapa deve ser fazer a interface
de revisao deixar de depender do `buscaIds.json` como fonte principal.

## Percentual estimado de migracao

- Modelagem PostgreSQL: 95%
- Infraestrutura PostgreSQL: 90%
- Integracao operacional: 78%
- Desacoplamento JSON/CSV: 50%

Estimativa geral: 78% da migracao operacional concluida.
