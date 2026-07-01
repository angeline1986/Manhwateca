Sim --- essa tela precisa de bem mais detalhe porque é a etapa mais
crítica do fluxo. Ela não é só uma lista: é uma **mesa de decisão**.

Abaixo está uma versão mais completa e implementável.

# 02 --- Tela: Correspondências Pendentes

## Conceito da Tela

A tela **Correspondências Pendentes** deve funcionar como uma área de
revisão manual das obras que tiveram resultado incerto na busca do
MangaUpdates.

Ela existe para impedir que o sistema grave automaticamente um
`mangaupdates_id` errado no PostgreSQL.

O usuário deve conseguir:

-   ver a obra local que precisa de decisão;
-   comparar os candidatos encontrados;
-   entender por que a decisão ficou pendente;
-   escolher o candidato correto;
-   informar um ID manualmente;
-   ignorar temporariamente;
-   marcar a decisão como pronta para aplicação.

------------------------------------------------------------------------

# 1. Funcionamento da Tela

## Fluxo principal

``` text
Usuária acessa Correspondências Pendentes
→ sistema lista obras com decisão pendente
→ usuária seleciona uma obra
→ sistema exibe detalhes e candidatos
→ usuária escolhe uma decisão
→ sistema salva a decisão temporária
→ item fica pronto para "Aplicar decisões"
```

## A tela não deve gravar diretamente o ID final

Nesta etapa, a decisão deve ser salva apenas em uma fila intermediária.

``` text
Correspondências Pendentes
→ salva decisão temporária
→ NÃO atualiza ainda a tabela principal de obras
```

A gravação definitiva acontece somente na etapa seguinte:

``` text
Aplicar decisões
→ valida duplicidade
→ grava mangaupdates_id
→ registra log
→ remove da fila
```

------------------------------------------------------------------------

# 2. Layout Recomendado

## Estrutura geral

``` text
┌──────────────────────────────────────────────────────────────┐
│ Correspondências Pendentes                                   │
│ Revise candidatos encontrados ou informe o ID manualmente.   │
│                                                              │
│ KPIs / filtros                                               │
│                                                              │
│ ┌──────────────────────┐ ┌─────────────────────────────────┐ │
│ │ Lista de obras        │ │ Painel de decisão               │ │
│ │ pendentes             │ │                                 │ │
│ │                      │ │ Obra local                      │ │
│ │ - Obra A             │ │ Motivo da pendência             │ │
│ │ - Obra B             │ │ Candidatos encontrados          │ │
│ │ - Obra C             │ │ Campo de ID manual              │ │
│ │                      │ │ Ações                           │ │
│ └──────────────────────┘ └─────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

## Distribuição recomendada

  ------------------------------------------------------------------------
  Área              Função
  ----------------- ------------------------------------------------------
  Header            Nome da etapa e descrição objetiva

  KPIs compactos    Quantidade de ambíguos, baixa confiança, sem resultado

  Filtros           Buscar obra, filtrar por motivo/status

  Lista lateral     Obras que precisam de decisão

  Painel principal  Detalhes da obra selecionada

  Rodapé da decisão Botões de ação
  ------------------------------------------------------------------------

------------------------------------------------------------------------

# 3. Layout Detalhado da Página

## 3.1 Header

``` text
Correspondências Pendentes
Escolha o candidato correto ou informe manualmente o ID do MangaUpdates.
```

Abaixo do título, usar um resumo horizontal discreto:

``` text
12 pendentes · 7 ambíguas · 3 baixa confiança · 2 sem resultado · 4 prontas para aplicar
```

## 3.2 Filtros

Filtros recomendados:

``` text
[ Buscar obra pendente... ]

[ Todas ] [ Ambíguas ] [ Baixa confiança ] [ Sem resultado ] [ ID manual ] [ Prontas ]
```

## 3.3 Lista de obras pendentes

Cada item da lista deve mostrar:

``` text
Nome da obra local
Motivo da pendência
Quantidade de candidatos
Status da decisão
```

Exemplo:

``` text
Armadilha de Açúcar
Ambígua · 3 candidatos
Aguardando decisão
```

Status visuais:

  Status                 Exibição
  ---------------------- ----------------------------
  `PENDING_REVIEW`       Aguardando decisão
  `MANUAL_ID_REQUIRED`   Exige ID manual
  `SELECTED`             Decisão marcada
  `IGNORED`              Ignorada temporariamente
  `BLOCKED_DUPLICATE`    ID possivelmente duplicado

------------------------------------------------------------------------

# 4. Painel de Decisão

Quando a usuária clica em uma obra, abrir painel com:

## 4.1 Identificação local

``` text
Obra local
Armadilha de Açúcar

Título normalizado
armadilha de acucar

Aliases locais
- Sugar Trap
- Armadilha Açúcar
```

## 4.2 Motivo da pendência

Exemplo:

``` text
Motivo
A busca encontrou 3 candidatos com confiança próxima.
```

Outros motivos possíveis:

  Motivo             Explicação
  ------------------ --------------------------------------------------
  `AMBIGUOUS`        Mais de um candidato plausível
  `LOW_CONFIDENCE`   Melhor candidato abaixo da confiança mínima
  `NO_RESULT`        API não retornou candidato útil
  `ALIAS_DETECTED`   Nome da pasta parece ser alias de obra existente
  `DUPLICATE_RISK`   ID sugerido já aparece em outra obra

------------------------------------------------------------------------

# 5. Decisões Possíveis

A tela deve permitir exatamente estas decisões:

## Decisão 1 --- Escolher candidato encontrado

Uso:

``` text
Selecionar quando um dos candidatos retornados pela API é claramente a obra correta.
```

Campos salvos:

``` ts
{
  decisionType: "SELECT_CANDIDATE",
  selectedCandidateId: "12345",
  manualMangaupdatesId: null,
  ignoredReason: null
}
```

## Decisão 2 --- Informar ID manual

Uso:

``` text
Quando a API não encontrou resultado ou retornou candidatos errados.
```

Campos salvos:

``` ts
{
  decisionType: "MANUAL_ID",
  selectedCandidateId: null,
  manualMangaupdatesId: "98765",
  ignoredReason: null
}
```

Validações:

-   ID deve ser numérico ou seguir o formato aceito pelo MangaUpdates;
-   ID não pode estar vazio;
-   ID não pode estar vinculado a outra obra, exceto se confirmado
    manualmente;
-   idealmente validar se o ID existe na API antes de permitir aplicar.

## Decisão 3 --- Ignorar temporariamente

Uso:

``` text
Quando a usuária não quer decidir agora.
```

Campos salvos:

``` ts
{
  decisionType: "IGNORE_TEMPORARILY",
  ignoredReason: "Não tenho certeza ainda",
  ignoredUntil: null
}
```

Comportamento:

-   item sai da prioridade;
-   continua acessível no filtro "Ignoradas";
-   pode ser reaberto depois.

## Decisão 4 --- Marcar como sem correspondência

Uso:

``` text
Quando a obra não existe no MangaUpdates.
```

Campos salvos:

``` ts
{
  decisionType: "NO_MATCH",
  selectedCandidateId: null,
  manualMangaupdatesId: null,
  noMatchConfirmed: true
}
```

Comportamento:

-   evita que a mesma obra volte sempre para pendência;
-   pode ser revisada futuramente.

------------------------------------------------------------------------

# 6. Candidatos

Cada candidato deve mostrar:

``` text
Título MangaUpdates
ID externo
Score de confiança
Tipo/status da obra
Ano, se disponível
URL
Botão selecionar
```

Exemplo visual:

``` text
○ Sugar Trap
  ID: 12345
  Confiança: 87%
  Status: Ongoing
  [Abrir MangaUpdates]

○ Sugar Trap Novel
  ID: 67890
  Confiança: 74%
  Status: Completed
  [Abrir MangaUpdates]
```

## Recomendação visual

-   candidato recomendado pode ter badge "Mais provável";
-   confiança abaixo de 70% deve aparecer como risco;
-   candidatos com título muito diferente devem aparecer em ordem menor;
-   candidato já usado por outra obra deve ter alerta.

------------------------------------------------------------------------

# 7. Botões da Tela

  ----------------------------------------------------------------------------
  Botão               Quando aparece         Tipo       Efeito
  ------------------- ---------------------- ---------- ----------------------
  Selecionar          Em cada candidato      Síncrono   Marca candidato como
  candidato                                             escolhido

  Salvar ID manual    Quando campo manual    Síncrono   Salva ID na fila
                      preenchido                        

  Ignorar por         Sempre                 Síncrono   Move para ignorados
  enquanto                                              

  Marcar sem          Quando não há          Síncrono   Define `NO_MATCH`
  correspondência     resultado útil                    

  Limpar decisão      Quando já existe       Síncrono   Volta para pendente
                      decisão salva                     

  Próxima pendência   Após salvar decisão    Síncrono   Avança para próximo
                                                        item
  ----------------------------------------------------------------------------

------------------------------------------------------------------------

# 8. Estados da Decisão

``` ts
export enum PendingDecisionStatus {
  PENDING_REVIEW = "PENDING_REVIEW",
  SELECTED_CANDIDATE = "SELECTED_CANDIDATE",
  MANUAL_ID_SELECTED = "MANUAL_ID_SELECTED",
  NO_MATCH = "NO_MATCH",
  IGNORED = "IGNORED",
  BLOCKED_DUPLICATE = "BLOCKED_DUPLICATE",
  READY_TO_APPLY = "READY_TO_APPLY"
}
```

## Transições

``` text
PENDING_REVIEW
  → SELECTED_CANDIDATE
  → READY_TO_APPLY

PENDING_REVIEW
  → MANUAL_ID_SELECTED
  → READY_TO_APPLY

PENDING_REVIEW
  → NO_MATCH

PENDING_REVIEW
  → IGNORED

READY_TO_APPLY
  → Aplicar decisões
```

------------------------------------------------------------------------

# 9. Mapeamento de Dados

``` ts
export interface PendingDecisionRow {
  queueId: string;
  mangaId: string;

  localTitle: string;
  normalizedTitle: string;
  alternativeTitles: string[];

  reason: PendingReason;
  decisionStatus: PendingDecisionStatus;

  candidates: MangaUpdatesCandidate[];

  selectedCandidateId: string | null;
  manualMangaupdatesId: string | null;

  duplicateWarning: DuplicateWarning | null;
  ignoredReason: string | null;

  confidence: number | null;
  createdAt: string;
  updatedAt: string;
}
```

``` ts
export interface MangaUpdatesCandidate {
  candidateId: string;
  mangaupdatesId: string;
  title: string;
  url: string;
  confidence: number;
  matchReason: string[];
  year: number | null;
  status: string | null;
  type: string | null;
  isRecommended: boolean;
  alreadyLinkedToMangaId: string | null;
}
```

``` ts
export interface DuplicateWarning {
  mangaupdatesId: string;
  linkedMangaId: string;
  linkedMangaTitle: string;
  severity: "warning" | "blocker";
}
```

``` ts
export enum PendingReason {
  AMBIGUOUS = "AMBIGUOUS",
  LOW_CONFIDENCE = "LOW_CONFIDENCE",
  NO_RESULT = "NO_RESULT",
  ALIAS_DETECTED = "ALIAS_DETECTED",
  DUPLICATE_RISK = "DUPLICATE_RISK"
}
```

------------------------------------------------------------------------

# 10. Origem dos Dados

``` sql
SELECT
  q.id AS queue_id,
  q.manga_id,
  m.title AS local_title,
  m.normalized_title,
  m.alternative_titles,
  q.reason,
  q.decision_status,
  q.selected_candidate_id,
  q.manual_mangaupdates_id,
  q.confidence,
  q.ignored_reason,
  q.created_at,
  q.updated_at
FROM mangaupdates_decision_queue q
JOIN mangas m ON m.id = q.manga_id
WHERE q.applied_at IS NULL
  AND q.decision_status IN (
    'PENDING_REVIEW',
    'SELECTED_CANDIDATE',
    'MANUAL_ID_SELECTED',
    'IGNORED',
    'NO_MATCH',
    'BLOCKED_DUPLICATE',
    'READY_TO_APPLY'
  );
```

------------------------------------------------------------------------

# 11. Ordenação Padrão

Priorizar o que exige ação humana imediata:

``` sql
ORDER BY
  CASE
    WHEN q.decision_status = 'BLOCKED_DUPLICATE' THEN 1
    WHEN q.reason = 'AMBIGUOUS' THEN 2
    WHEN q.reason = 'LOW_CONFIDENCE' THEN 3
    WHEN q.reason = 'NO_RESULT' THEN 4
    WHEN q.reason = 'ALIAS_DETECTED' THEN 5
    WHEN q.decision_status = 'READY_TO_APPLY' THEN 6
    WHEN q.decision_status = 'IGNORED' THEN 9
    ELSE 10
  END,
  q.confidence ASC NULLS FIRST,
  q.updated_at DESC,
  m.title ASC;
```

------------------------------------------------------------------------

# 12. Endpoints

## Listar fila

``` http
GET /api/mangaupdates/review
```

``` ts
export interface ReviewQueryParams {
  page?: number;
  pageSize?: number;
  search?: string;
  reason?: PendingReason;
  status?: PendingDecisionStatus;
  onlyReadyToApply?: boolean;
  includeIgnored?: boolean;
}
```

## Salvar decisão

``` http
POST /api/mangaupdates/decisions
```

``` ts
export interface SaveDecisionRequest {
  queueId: string;
  decisionType:
    | "SELECT_CANDIDATE"
    | "MANUAL_ID"
    | "NO_MATCH"
    | "IGNORE_TEMPORARILY"
    | "CLEAR_DECISION";

  selectedCandidateId?: string;
  manualMangaupdatesId?: string;
  ignoredReason?: string;
}
```

## Resposta

``` json
{
  "success": true,
  "data": {
    "queueId": "dq_001",
    "decisionStatus": "READY_TO_APPLY",
    "message": "Decisão salva. Item pronto para aplicação."
  }
}
```

------------------------------------------------------------------------

# 13. Validações

## Ao selecionar candidato

Validar:

-   candidato pertence ao item da fila;
-   candidato possui `mangaupdatesId`;
-   ID ainda não está aplicado em outra obra;
-   item ainda não foi aplicado por outro processo.

## Ao informar ID manual

Validar:

``` text
- não vazio;
- formato válido;
- não duplicado;
- opcionalmente existente na API;
- não bloqueado por rate limit.
```

## Ao marcar sem correspondência

Exigir confirmação:

``` text
Esta obra será marcada como sem correspondência no MangaUpdates.
Você poderá reabrir essa decisão futuramente.
```

------------------------------------------------------------------------

# 14. Edge Cases

  -----------------------------------------------------------------------
  Caso                    Tratamento
  ----------------------- -----------------------------------------------
  ID já usado por outra   Bloquear aplicação e exibir obra conflitante
  obra                    

  Candidato removido da   Manter candidato salvo localmente e sinalizar
  API                     "não encontrado na API"

  API fora do ar          Permitir salvar decisão local, mas bloquear
                          validação externa

  Item aplicado por outro Exibir stale state e recarregar fila
  processo                

  Usuária seleciona       Permitir limpar decisão antes de aplicar
  candidato errado        

  Obra ignorada volta em  Não duplicar fila; atualizar item existente
  nova busca              

  Obra sem candidato      Priorizar campo de ID manual

  Muitos candidatos       Mostrar top 5 e botão "ver todos"
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# 15. Critérios de Aceite

-   A tela lista somente itens pendentes ou ainda não aplicados.
-   A usuária consegue selecionar um candidato.
-   A usuária consegue informar ID manual.
-   A decisão salva não grava diretamente na tabela principal.
-   Itens com decisão aparecem como prontos para aplicar.
-   IDs duplicados geram alerta.
-   Itens ignorados podem ser reabertos.
-   A interface não perde a decisão ao trocar de item.
-   A lista suporta paginação.
-   A aplicação definitiva fica restrita à tela "Aplicar decisões".

------------------------------------------------------------------------

# 16. Atualizações Arquiteturais (Protótipo Revisado)

## 16.1 Conceito de UX

A tela deixa de ser uma "mesa de decisão" e passa a funcionar como uma
**área de revisão focada**, onde apenas **uma obra é revisada por vez**.

Princípios:

-   reduzir carga cognitiva;
-   separar fila e decisão;
-   evitar múltiplos painéis concorrendo pela atenção;
-   permitir navegação extremamente rápida entre pendências.

## 16.2 Arquitetura Visual

``` text
┌──────────────────────────────────────────────────────────────┐
│ Sidebar contextual                                            │
├───────────────────┬──────────────────────────────────────────┤
│ Fila de revisão   │ Painel de revisão                        │
│                   │                                          │
│ • Obra A          │ Obra local                               │
│ • Obra B          │ Alerta compacto                          │
│ • Obra C          │ Lista de candidatos                      │
│                   │ ID manual                                │
│                   │ Rodapé de ações                          │
└───────────────────┴──────────────────────────────────────────┘
```

### Fila de revisão

Cada item deve exibir somente:

-   título;
-   motivo;
-   quantidade de candidatos;
-   status.

Jamais exibir aliases ou candidatos diretamente na lista.

### Painel

Sempre mostra apenas um item.

Caso nenhum item esteja selecionado:

``` text
Selecione uma obra na fila para iniciar a revisão.
```

## 16.3 Menu Contextual de Fluxos

Esta tela passa a ser acessada exclusivamente por:

``` text
Fluxos
 ├ Buscar candidatos
 ├ Revisar pendências
 ├ Aplicar decisões
 ├ Atualizar metadados
 └ Sincronizar Notion
```

Não deve existir menu interno na página.

## 16.4 Microinterações

### Selecionar candidato

-   destaca cartão;
-   exibe badge "Selecionado ✓";
-   remove ID manual;
-   habilita "Salvar decisão".

### Informar ID manual

-   limpa seleção existente;
-   valida em tempo real;
-   apresenta erro inline;
-   habilita salvar somente quando válido.

### Salvar decisão

Estado inicial:

``` text
Desabilitado
```

Habilitar apenas quando existir:

-   candidato selecionado; ou
-   ID manual válido.

Após salvar:

-   persistir decisão temporária;
-   atualizar status da fila;
-   opcionalmente navegar para próxima pendência.

## 16.5 Estados Visuais

Adicionar documentação para:

-   Painel vazio;
-   Item selecionado;
-   Loading parcial;
-   API indisponível;
-   Sem candidatos;
-   ID manual inválido;
-   Duplicidade detectada;
-   Pronto para aplicar.

## 16.6 Navegação

Trocar de item:

-   preserva decisões já salvas;
-   não perde alterações.

Ao retornar para a tela:

-   restaurar último item aberto.

## 16.7 Integração com o Menu

Ao clicar em Fluxos:

-   menu principal desliza para fora;
-   menu contextual entra;
-   breadcrumb atualiza;
-   conteúdo central anima.

Ao clicar em voltar:

-   restaurar menu principal;
-   manter última etapa em memória.

## 16.8 Requisitos de UX

-   nenhuma ação definitiva nesta etapa;
-   uma única decisão por vez;
-   botão principal sempre visível no rodapé;
-   alerta compacto;
-   fila navegável por teclado;
-   Enter confirma seleção;
-   Esc cancela edição de ID manual.

## 16.9 Critérios adicionais de aceite

-   botão "Salvar decisão" permanece desabilitado sem decisão válida;
-   destaque visual inequívoco do candidato selecionado;
-   painel nunca exibe mais de uma obra simultaneamente;
-   suporte a milhares de itens com paginação e lazy loading;
-   transições suaves entre itens sem recarregar toda a página.
