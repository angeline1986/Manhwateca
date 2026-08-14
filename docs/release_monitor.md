# Monitor de lançamentos

O Release Monitor consulta fontes externas de capítulos, normaliza os
itens como `ExternalRelease` e mantém o histórico genérico em
PostgreSQL. A página `Dashboard > Visão geral` consome
`external_releases` para os cards e a lista de capítulos disponíveis.

```text
Release Monitor
    |
    +-- MangaUpdates -> provider/executor
    |
    +-- MangaDex     -> provider/executor incremental
    |
    v
ExternalRelease
    |
    v
external_releases
    |
    v
Dashboard
```

As referências externas por obra ficam em `manga_external_refs`:

```text
Obra local
    |
    +-- MangaUpdates external ref
    |
    +-- MangaDex external ref
```

Obras com `mangas.work_code` confirmado ainda são monitoradas
automaticamente pelo caminho legado MangaUpdates. A tabela
`release_monitor_subscriptions` funciona como override: registro
ausente usa a regra automática, `enabled=true` força monitoramento e
`enabled=false` exclui explicitamente a obra.

## API MangaUpdates

Contrato validado em 2026-08-06:

- Base oficial: `https://api.mangaupdates.com/v1`.
- Endpoint de releases: `GET /releases/days`, descrito como `ListReleasesByDay`.
- Validação real controlada retornou `total_hits`, `page`, `per_page` e `results`; cada item veio encapsulado em `record`.
- Use `include_metadata=true` em `GET /releases/days?page=1&include_metadata=true`. Com esse parâmetro, a resposta pública validada trouxe `record.chapter`, `record.release_date`, `record.id` e `metadata.series.series_id`, que é usado para o matching com `mangas.work_code`.
- `POST /releases/search` também respondeu sem autenticação na validação controlada e retornou `record` + `metadata.series.series_id` com `include_metadata=true`, mas o monitor continua usando `/releases/days` como caminho principal.
- `GET /series/{series_id}/rss` retornou XML para a série testada, mas o feed estava sem itens de release naquele momento; RSS permanece apenas diagnóstico, não solução principal.
- Endpoints auxiliares já usados pelo projeto: `POST /series/search` e `GET /series/{id}`.
- Paginação: parâmetros `page` e `perpage`, seguindo o padrão já usado no cliente do projeto.
- Autenticação: o cliente atual não injeta token; a API pública pode impor limites por origem.
- HTTP 429: o cliente central respeita `Retry-After` quando fornecido e aplica backoff exponencial como fallback.

A resposta externa é convertida para `ExternalRelease` antes de chegar ao serviço. O parser aceita variações comuns de campo (`series_id`/`seriesId`, `release_date`/`date`, `group_name`/`group`) e preserva o identificador externo como texto para isolar o restante do sistema do JSON bruto.

O MangaUpdates registra releases presentes na base dele. Isso ajuda a descobrir capítulos disponíveis, mas não garante cobertura completa de todos os capítulos oficiais publicados nas plataformas originais.

## API MangaDex

O cliente MangaDex fica em `manhwateca/mangadex_service` e cobre busca,
detalhes, cover art, feed de capítulos e paginação `limit`/`offset`.
O Release Monitor não chama endpoints MangaDex diretamente: o executor
usa `process_manga(...)`, que percorre o feed incrementalmente,
normaliza os capítulos e persiste em `external_releases`.

O estado incremental MangaDex é guardado em
`manga_external_refs.metadata.release_monitor`, com
`last_checked_at` e `latest_release_published_at`. A execução para ao
encontrar release já conhecida, ao esgotar o feed ou ao atingir o limite
de segurança.

`translatedLanguage` é preservado no campo `language`. O monitor não
filtra idioma e não aplica regra funcional baseada em idioma neste
ponto.

## Tabelas

- `release_monitor_subscriptions`: override por obra, com `enabled`, modo e datas de última verificação/sucesso/erro. Ausência de registro não impede monitoramento quando a obra possui `work_code`.
- `manga_external_refs`: referências externas por provider, como IDs MangaUpdates e UUIDs MangaDex, com metadados opcionais por integração.
- `external_releases`: histórico genérico de releases por provider, com capítulo, volume, idioma, grupo quando disponível, payload bruto, `first_seen_at`, `last_seen_at` e `viewed_at`. É a fonte atual das leituras do Dashboard.
- `mangaupdates_releases`: histórico legado de releases MangaUpdates, ainda alimentado por escrita dupla para compatibilidade e rollback.
- `release_monitor_runs`: auditoria de cada execução, métricas e status (`running`, `success`, `partial_success`, `failed`).

## Períodos

O fuso é sempre `America/Sao_Paulo`.

- Hoje: data corrente nesse fuso.
- Semana: segunda-feira a domingo da semana corrente.
- Mês: primeiro ao último dia do mês corrente.

`chapter_count` representa registros de capítulos persistidos em `external_releases` para o período. `release_count` é mantido no contrato com o mesmo valor para compatibilidade.

`release_date` é a data de lançamento normalizada a partir do provider.
Para MangaUpdates, vem do payload de release. Para MangaDex, vem de
`publishAt`. `first_seen_at` é quando a Manhwateca detectou a release
pela primeira vez. `last_seen_at` é atualizado quando a mesma release
reaparece em nova execução. Uma release publicada ontem e detectada hoje
mantém `release_date` de ontem e `first_seen_at` de hoje.

## Deduplicação

A deduplicação genérica em `external_releases` prioriza
`(provider, external_release_id)`, quando o ID externo da release existe.
Sem esse ID, usa:

- `provider`;
- `external_series_id`;
- `release_date`;
- `chapter` normalizado;
- `release_group` normalizado;
- `volume` normalizado.

O upsert preserva `first_seen_at` e `viewed_at`, atualiza
`last_seen_at` e pode atualizar `raw_payload`.

No caminho legado MangaUpdates, `mangaupdates_releases` mantém sua
deduplicação própria com `mangaupdates_series_id` para rollback.

## Providers

`ReleaseMonitorService` coordena a execução, períodos, métricas e
consolidação de status. Ele conhece executores/providers, mas não
conhece os endpoints HTTP específicos.

- MangaUpdates: `MangaUpdatesReleaseProvider` consulta páginas de
  releases, normaliza para `ExternalRelease` e o executor aplica a
  janela temporal do monitor. O resultado é gravado em
  `mangaupdates_releases` e em `external_releases`.
- MangaDex: `MangaDexMonitorExecutor` reutiliza `process_manga(...)`.
  O executor consulta obras com referência MangaDex, usa checkpoint por
  obra e grava apenas em `external_releases`.
- Provider comparison: `ProviderComparisonService` compara MangaUpdates
  e MangaDex de forma read-only, usando refs externas e fallback
  `work_code` quando necessário. Ele não grava releases nem altera
  checkpoints.

## Endpoints

- `GET /api/dashboard/releases-summary`
- `GET /api/releases?period=today|week|month&search=&page=&per_page=&unseen_only=&manga_id=`
- `GET /api/releases/subscriptions`
- `GET /api/releases/status`
- `POST /api/releases/check`
- `POST /api/releases/subscriptions/update`
- `POST /api/releases/mark-viewed`

`POST /api/releases/check` dispara a task `release_check` e responde `202` quando iniciada. Se já houver tarefa incompatível, retorna estado equivalente a `already_running`.

## Execução Manual

Antes da primeira execução em um banco novo, aplique as migrations pelo runner oficial:

```bash
python -m manhwateca.database.migrate
```

Pelo terminal:

```bash
python scripts/check_releases.py
```

Pelo Dashboard, use o botão `Verificar agora`.

## Execução Automática

Use um agendador externo, sem loop permanente no servidor web. Exemplos:

```cron
15 * * * * cd /caminho/Manhwateca && . .venv/bin/activate && python scripts/check_releases.py
```

Em `launchd`, configure o mesmo comando com `WorkingDirectory` apontando para o repositório e `DATABASE_URL` disponível no ambiente.

## Validação no Dashboard

Abra `Dashboard > Visão geral` e confira a seção `Capítulos disponíveis`.

- O cabeçalho mostra a última verificação ou `Verificação em andamento...`.
- Os cards `Capítulos disponíveis no mês`, `Capítulos disponíveis na semana` e `Capítulos disponíveis hoje` refletem os contadores do endpoint `GET /api/dashboard/releases-summary`.
- Hoje é o período inicial. Clicar nos cards ou nos filtros `Hoje`, `Esta semana` e `Este mês` atualiza a lista via `GET /api/releases?period=...`.
- A busca por título e o filtro `Somente não visualizados` atuam sobre a lista do período selecionado.

## Exclusão de Obras

Para remover uma obra específica do monitoramento sem apagar o `work_code`, registre ou atualize a assinatura com `enabled=false` em `release_monitor_subscriptions`. Pela API:

```bash
curl -X POST http://127.0.0.1:8000/api/releases/subscriptions/update \
  -H 'Content-Type: application/json' \
  -d '{"manga_id": 123, "enabled": false, "monitor_mode": "releases"}'
```

Para voltar ao monitoramento explícito, use `enabled=true`. Para voltar ao modo automático, remova a assinatura da obra.

## Limitações

Os testes automatizados usam clientes falsos e relógio controlado. A
validação real controlada depende de rede, disponibilidade/limites das
APIs públicas e `DATABASE_URL` disponível no ambiente. Quando não é
possível validar dados reais, o fallback `work_code`, a tabela
`mangaupdates_releases` e a escrita dupla MangaUpdates permanecem por
compatibilidade.
