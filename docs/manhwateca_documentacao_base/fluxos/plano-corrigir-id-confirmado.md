# Plano: Corrigir ID confirmado

## Contexto

Foi identificado um caso em que uma obra local tinha um ID MangaUpdates confirmado, mas o ID pertencia a outra obra.

Exemplo observado:

- Obra local: `Mad for love`
- ID salvo: `57487635157`
- Obra real desse ID: `Record of Mad Love`
- ID correto informado: `56302347523`
- Título retornado pelo ID correto: `Tuojiang`
- Alias relevante: `Mad For Love`

Esse tipo de erro não é resolvido pela etapa `Atualizar metadados`, porque essa etapa assume que o `work_code` já está correto. Quando o ID está errado, o fluxo consulta a obra errada no MangaUpdates, persiste metadados errados ou incompletos e pode sincronizar dados incorretos com o Notion.

## Objetivo

Criar uma funcionalidade controlada chamada **Corrigir ID confirmado** para permitir corrigir, com validação e auditoria, um ID MangaUpdates que já foi salvo no PostgreSQL.

A funcionalidade deve corrigir a associação da obra e invalidar os dados técnicos derivados do ID antigo. Ela não deve reconstruir metadados completos. A reconstrução deve continuar concentrada na etapa oficial **Atualizar metadados**.

## Não Objetivos

- Não automatizar correções de ID sem confirmação humana.
- Não corrigir dados diretamente pela etapa `Atualizar metadados`.
- Não duplicar a lógica de atualização de metadados dentro de `Corrigir ID confirmado`.
- Não permitir sobrescrever ID quando ele já estiver atribuído a outra obra sem bloqueio explícito.
- Não sincronizar automaticamente com o Notion após a correção.
- Não alterar campos editoriais/pessoais do Notion.
- Não usar JSON/CSV como fonte de verdade.

## Problema Atual

O fluxo oficial possui caminhos para:

- buscar candidatos;
- revisar pendências;
- aplicar decisões;
- confirmar ID MangaUpdates;
- atualizar metadados usando o ID confirmado.

Mas não existe um caminho oficial para:

> "Este ID já foi confirmado, mas depois descobri que está errado."

Depois que `work_code` é salvo, a obra deixa de aparecer no fluxo normal de revisão de IDs. Se o ID estiver errado, `Atualizar metadados` apenas repete a consulta contra a obra incorreta.

## Local Recomendado na UI

A funcionalidade deve ficar na etapa **Revisar pendências**, em uma seção específica:

```text
Corrigir ID confirmado
```

Motivo:

- a correção é uma decisão humana de correspondência entre obra local e MangaUpdates;
- não pertence à atualização de metadados, que pressupõe ID correto;
- não pertence à sincronização Notion, que deve consumir dados já confiáveis do PostgreSQL.

## Fluxo de Produto Proposto

### Fase 1 — Diagnóstico e seleção da obra

Objetivo:

- permitir localizar uma obra que já possui `work_code`;
- mostrar o ID atual e os metadados derivados dele.

Interface esperada:

```text
Corrigir ID confirmado

Buscar obra:
[ Mad for love ]

Resultado:
Mad for love
ID atual: 57487635157
Título atual no MangaUpdates: Record of Mad Love
URL atual: ...
```

Validações:

- a obra precisa existir no PostgreSQL;
- a obra precisa ter `work_code`;
- a tela deve indicar claramente que o ID atual já está confirmado.

Fora do escopo desta fase:

- aplicar correção;
- consultar Notion;
- alterar PostgreSQL.

### Fase 2 — Validação do novo ID

Objetivo:

- permitir informar um novo ID MangaUpdates;
- consultar a API MangaUpdates em modo leitura;
- apresentar um preview antes de qualquer persistência.

Interface esperada:

```text
Novo ID MangaUpdates:
[ 56302347523 ] [Validar ID]

Preview:
Título retornado: Tuojiang
URL: https://www.mangaupdates.com/series/pv4ypdv/tuojiang
Capa: https://cdn.mangaupdates.com/image/i455202.jpg
Formato: Manhua
Aliases:
- Fou d'amour
- Mad For Love
- Thoát Cương
- Tuōjiāng
```

Validações:

- o novo ID precisa existir no MangaUpdates;
- o novo ID não pode estar atribuído a outra obra;
- se estiver atribuído a outra obra, bloquear com mensagem clara;
- se a API falhar, não persistir nada.

Fora do escopo desta fase:

- atualizar PostgreSQL;
- atualizar Notion.

### Fase 3 — Aplicação segura da correção

Objetivo:

- trocar o ID confirmado;
- invalidar metadados técnicos derivados do ID antigo;
- preservar campos editoriais/pessoais;
- registrar auditoria.

Campos a atualizar:

- `work_code`;
- status local necessário para que a obra volte ao fluxo de metadados pendentes;
- status local do Notion para indicar que a sincronização precisa ser revisada posteriormente, usando valores já existentes no projeto.

Campos derivados do MangaUpdates a invalidar ou limpar:

- `mangaupdates_url`;
- `cover_url`;
- `format`;
- `latest_mangaupdates_chapter`;
- temas/categorias técnicas derivadas do ID antigo;
- `alternative_title`, apenas quando estiver comprovadamente contaminado por dado da obra antiga.

A etapa não deve preencher esses campos com os dados do novo ID. Ela deve deixar a obra em estado consistente de **metadados pendentes de reconstrução**, para que a etapa **Atualizar metadados** faça a consulta oficial ao MangaUpdates e reconstrua os dados técnicos.

Campos a preservar:

- título local;
- campos editoriais/pessoais;
- estado de leitura;
- nota;
- interesse;
- picância;
- campos manuais do Notion.

Regra para alias:

- preservar alias real já existente;
- remover alias derivado da obra errada quando comprovadamente contaminado;
- não adicionar alias do novo ID nesta etapa;
- deixar novos aliases para a etapa **Atualizar metadados**;
- nunca criar alias fictício no formato `ID <numero>`.

Efeito no Notion local:

- não chamar API do Notion;
- não aplicar sync automaticamente;
- marcar o estado local como pendente/revisável usando status já existente no projeto;
- não atualizar `notion_last_synced_at`;
- não marcar como `synced`.

Auditoria:

- registrar evento informando:
  - obra;
  - ID antigo;
  - título retornado pelo ID antigo, quando disponível;
  - ID novo;
  - título retornado pelo ID novo;
  - campos técnicos invalidados;
  - origem: `Corrigir ID confirmado`.

Fluxo revisado:

```text
Corrigir ID confirmado
↓
Validar novo ID
↓
Aplicar correção do work_code
↓
Invalidar/Limpar metadados derivados do ID anterior
↓
Marcar obra como pendente para Atualizar metadados
↓
Atualizar metadados (fluxo oficial existente)
↓
Sincronizar Notion (manual, quando desejado)
```

### Fase 4 — Integração com etapas seguintes

Objetivo:

- garantir que, após corrigir o ID, a obra siga naturalmente pelo fluxo oficial.

Comportamento esperado:

```text
Corrigir ID confirmado
↓
Atualizar metadados, se ainda houver pendência técnica
↓
Sincronizar Notion, manualmente
```

Regras:

- após corrigir o ID, a obra deve aparecer em `Atualizar metadados`;
- `Atualizar metadados` deve reconstruir URL, capa, formato, capítulos, aliases e demais dados técnicos;
- se dados técnicos foram alterados, `Sincronizar Notion` deve considerar a obra elegível;
- nenhuma sincronização Notion deve ser disparada automaticamente nesta fase.

## Contratos Técnicos Prováveis

### Endpoint de preview

```http
POST /api/mangaupdates/confirmed-id/preview
```

Payload:

```json
{
  "work_id": 254,
  "new_work_code": "56302347523"
}
```

Resposta:

```json
{
  "work": {
    "id": 254,
    "title": "Mad for love",
    "current_work_code": "57487635157"
  },
  "current": {
    "title": "Record of Mad Love",
    "url": "https://www.mangaupdates.com/series/qeqnj6d/record-of-mad-love"
  },
  "proposed": {
    "work_code": "56302347523",
    "title": "Tuojiang",
    "url": "https://www.mangaupdates.com/series/pv4ypdv/tuojiang",
    "cover_url": "https://cdn.mangaupdates.com/image/i455202.jpg",
    "format": "Manhua",
    "aliases": ["Fou d'amour", "Mad For Love", "Thoát Cương", "Tuōjiāng"]
  },
  "can_apply": true,
  "blockers": []
}
```

### Endpoint de aplicação

```http
POST /api/mangaupdates/confirmed-id/apply
```

Payload:

```json
{
  "work_id": 254,
  "expected_current_work_code": "57487635157",
  "new_work_code": "56302347523",
  "confirmed": true
}
```

Resposta:

```json
{
  "applied": true,
  "work_id": 254,
  "old_work_code": "57487635157",
  "new_work_code": "56302347523",
  "updated_fields": [
    "work_code",
    "notion_sync_status"
  ],
  "invalidated_fields": [
    "mangaupdates_url",
    "cover_url",
    "format",
    "latest_mangaupdates_chapter",
    "alternative_title"
  ],
  "metadata_status": "pending",
  "notion_sync_status": "pending"
}
```

## Arquivos Prováveis

Backend:

- `manhwateca/database/manga_repository.py`
- módulo web novo ou existente para endpoints MangaUpdates;
- `manhwateca/webapp/post_routes.py`
- `manhwateca/mangaupdates_service/details.py`, se for necessário reaproveitar preview;
- testes de repository;
- testes de endpoint.

Frontend:

- `web/js/flows/pendingReviewPanel.js`
- `web/js/flows/flowsClickHandler.js`
- `web/js/pages/flowsPage.js`
- CSS da tela de fluxos, apenas se necessário.

Testes:

- `tests/test_database.py`
- testes web de MangaUpdates;
- testes JS com `node --check`;
- validação CDP da UI.

## Regras de Segurança

- Nunca aplicar correção sem preview.
- Nunca aplicar se o novo ID já estiver atribuído a outra obra.
- Nunca apagar campos editoriais.
- Nunca chamar Notion durante a correção.
- Nunca marcar como `synced` após corrigir ID.
- Nunca atualizar `notion_last_synced_at` sem sync real com Notion.
- Nunca criar alias fictício `ID <numero>`.
- Nunca usar JSON/CSV como fonte operacional.

## Testes Necessários

Repository:

- corrige `work_code` por `work_id`;
- bloqueia novo ID já atribuído a outra obra;
- limpa/invalida metadados técnicos derivados do ID antigo;
- não preenche metadados técnicos do novo ID;
- preserva campos editoriais;
- preserva título local;
- não atualiza `notion_last_synced_at`;
- marca status Notion como pendente/revisável usando status existente;
- registra evento/auditoria.

Endpoint:

- preview de ID válido;
- preview de ID inexistente;
- preview com colisão;
- apply exige confirmação explícita;
- apply recusa payload divergente;
- apply não consulta Notion;
- apply não usa JSON/CSV.

Frontend:

- seção aparece em `Revisar pendências`;
- busca obra com ID já confirmado;
- preview mostra ID atual e ID proposto;
- bloqueios são visíveis;
- botão de aplicar fica desabilitado até validação;
- após aplicar, UI orienta próxima etapa.

## Riscos

- Corrigir ID pode invalidar metadados já sincronizados com Notion.
- Alias contaminado pode ser difícil de distinguir de alias manual real.
- Obra pode ter sido sincronizada no Notion com dados da obra errada.
- Se a correção for aplicada sem auditar, fica difícil explicar o histórico.

## Recomendação de Execução

Implementar de forma escalonada:

1. Preview somente leitura.
2. Validação de colisão e bloqueios.
3. Aplicação segura no PostgreSQL.
4. Integração visual em `Revisar pendências`.
5. Validação CDP.
6. Só depois avaliar efeitos no Notion via fluxo oficial normal.

## Status

Em implementação controlada.

### Status consolidado até 2026-07-25

Concluído:

- plano funcional registrado em Markdown;
- endpoint de preview criado;
- preview valida ID novo em modo leitura;
- preview bloqueia ID igual ao atual;
- preview bloqueia ID já atribuído a outra obra;
- preview retorna erro claro para ID inexistente ou falha do MangaUpdates;
- endpoint de aplicação criado;
- repository corrige `work_code` por `work_id`;
- repository bloqueia colisão de ID já atribuído a outra obra;
- aplicação invalida metadados derivados do ID antigo;
- aplicação marca `notion_sync_status` como `pending`;
- aplicação registra evento `mangaupdates_confirmed_id_corrected`;
- aplicação não chama Notion;
- aplicação não reconstrói metadados técnicos;
- UI mínima criada em `Revisar pendências`;
- endpoint de candidatos confirmado criado para buscar obras já vinculadas por título, ID local ou ID MangaUpdates;
- UI passou a selecionar a obra por busca, em vez de exigir digitação manual do `work_id`;
- testes backend adicionados;
- testes do endpoint de candidatos adicionados;
- teste HTTP garante que o endpoint de candidatos retorna objeto JSON direto, não tupla serializada;
- validação CDP confirmou que o painel aparece em `Revisar pendências`.
- validação CDP confirmou busca por `Mad for love`, seleção da obra e botão de preview habilitado sem campo manual de `work_id`.
- troca de busca ou obra selecionada invalida o preview anterior;
- alteração do novo ID invalida o preview anterior e desabilita a aplicação até nova validação.
- endpoint de aplicação passou a exigir `expected_current_work_code`;
- aplicação bloqueia `stale_preview` quando o ID atual no PostgreSQL mudou após o preview;
- aplicação revalida o novo ID no MangaUpdates antes de persistir;
- aplicação revalida colisão de ID antes e durante a operação de persistência;
- repository relê a obra com bloqueio transacional antes de atualizar;
- repository executa rollback quando a aplicação falha antes do commit;
- testes cobrem preview obsoleto, colisão tardia, falha do MangaUpdates e rollback de auditoria.
- testes cobrem rollback quando falha o `UPDATE` único que troca `work_code`, invalida metadados e marca status pendente;
- testes cobrem rollback quando falha a limpeza de temas após o `UPDATE`;
- `work_code`, metadados derivados e `notion_sync_status` são alterados na mesma instrução SQL, sem commit intermediário.

Validado por preview no caso real `Mad for love`:

- ID atual identificado: `57487635157`;
- obra retornada pelo ID atual: `Record of Mad Love`;
- novo ID validado: `56302347523`;
- obra retornada pelo novo ID: `Tuojiang`;
- alias relevante identificado: `Mad For Love`;
- preview confirmou que o ID antigo era `Record of Mad Love`;
- preview confirmou que o ID novo é `Tuojiang`;
- nenhuma correção foi aplicada à obra real nesta etapa;
- aplicação real permanece pendente após commit seletivo e revisão final.

Pendente:

- melhorar a experiência visual do preview;

### Validação integrada controlada em 2026-07-25

Concluído em cenário controlado:

- aplicação executada pela UI;
- preview válido usado antes da aplicação;
- payload de aplicação incluiu `expected_current_work_code`;
- backend bloqueou reaplicação com preview obsoleto;
- persistência foi transacional;
- metadados derivados do ID antigo foram invalidados;
- temas derivados do vínculo antigo foram removidos;
- campos pessoais/editoriais foram preservados;
- `notion_sync_status` foi marcado como `pending`;
- `notion_last_synced_at` foi preservado;
- evento de auditoria foi criado uma única vez;
- UI exibiu sucesso e orientou seguir para `Atualizar metadados`;
- UI removeu o preview anterior e não manteve o botão de aplicação disponível;
- nenhuma sincronização Notion foi executada.

Cenário usado:

- obra controlada: `ZZZ Teste Corrigir ID Confirmado E2E`;
- `work_id`: `271`;
- ID antigo: `57487635157`;
- ID novo: `78044981927`;
- título do ID antigo: `Record of Mad Love`;
- título do ID novo: `Romance in the City`.

Estado comprovado após a aplicação:

- `work_code = 78044981927`;
- `mangaupdates_url = NULL`;
- `cover_url = NULL`;
- `format = NULL`;
- `latest_mangaupdates_chapter = NULL`;
- `alternative_title = NULL`;
- `notion_sync_status = pending`;
- `notion_last_synced_at` preservado;
- temas derivados removidos;
- campos pessoais/editoriais preservados.

Auditoria comprovada:

- evento: `mangaupdates_confirmed_id_corrected`;
- `old_work_code = 57487635157`;
- `new_work_code = 78044981927`;
- `source = Corrigir ID confirmado`;
- apenas um evento de sucesso foi criado para a aplicação.

Reaplicação obsoleta:

- tentativa com `expected_current_work_code = 57487635157`;
- resposta: `409`;
- blocker: `stale_preview`;
- `actual_current_work_code = 78044981927`;
- nenhum segundo evento de sucesso foi criado.

Evidência visual:

- screenshot: `/tmp/manhwateca-corrigir-id-e2e-pos-sucesso.png`;
- sucesso exibido na UI;
- instrução para seguir para `Atualizar metadados` exibida.

Validação executada:

- `74 passed, 2 skipped`;
- `py_compile` OK;
- `node --check` OK.

Status final desta etapa:

- Fase 1 — Busca e seleção: concluída;
- Fase 2 — Preview somente leitura: concluída;
- Proteção contra preview obsoleto: concluída;
- Aplicação transacional: concluída;
- Rollback integral: concluído;
- Validação integrada controlada: concluída;
- Estado visual pós-sucesso: concluído;
- Ausência de sync automático com Notion: validada;
- Correção da obra real `Mad for love`: pendente;
- Commit seletivo: pendente.
