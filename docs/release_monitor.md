# Monitor de lançamentos MangaUpdates

O monitor consulta lançamentos recentes do MangaUpdates, associa cada release a uma obra local pelo ID confirmado (`release.series_id -> mangas.work_code -> mangas.id`) e mantém histórico em PostgreSQL. A página `Dashboard > Visão geral` consome esse histórico para os cards e a lista de lançamentos.

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

A resposta externa é convertida para `ExternalRelease` antes de chegar ao serviço. O parser aceita variações comuns de campo (`series_id`/`seriesId`, `release_date`/`date`, `group_name`/`group`) para isolar o restante do sistema do JSON bruto.

## Tabelas

- `release_monitor_subscriptions`: assinatura explícita por obra, com `enabled`, modo e datas de última verificação/sucesso/erro.
- `mangaupdates_releases`: histórico de releases, com capítulo e volume textuais, `source_payload` em JSONB, `first_seen_at`, `last_seen_at` e `viewed_at`.
- `release_monitor_runs`: auditoria de cada execução, métricas e status (`running`, `success`, `partial_success`, `failed`).

## Períodos

O fuso é sempre `America/Sao_Paulo`.

- Hoje: data corrente nesse fuso.
- Semana: segunda-feira a domingo da semana corrente.
- Mês: primeiro ao último dia do mês corrente.

`release_date` é a data informada pelo MangaUpdates. `first_seen_at` é quando a Manhwateca detectou a release pela primeira vez. Uma release publicada ontem e detectada hoje mantém `release_date` de ontem e `first_seen_at` de hoje.

## Deduplicação

A deduplicação prioriza `external_release_id`, quando presente. Sem esse ID, usa:

- `mangaupdates_series_id`;
- `release_date`;
- `chapter` normalizado;
- `release_group` normalizado;
- `volume` normalizado.

O upsert preserva `first_seen_at` e `viewed_at`, atualiza `last_seen_at` e pode atualizar `source_payload`.

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

## Limitações

Os testes automatizados usam cliente falso e relógio controlado. A validação real controlada depende de rede e disponibilidade/limites da API pública do MangaUpdates.
