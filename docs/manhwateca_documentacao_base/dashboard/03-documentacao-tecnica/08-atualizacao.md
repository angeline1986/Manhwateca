# Dashboard — Documentação Técnica

## 08 - Atualização

---

# Objetivo

Este documento define a estratégia de atualização de dados do Dashboard da Manhwateca.

O Dashboard é um módulo predominantemente **read-only**, cuja principal responsabilidade é apresentar uma visão consistente do estado atual da aplicação. Para isso, deve utilizar mecanismos de atualização que garantam:

* consistência entre componentes;
* baixo tempo de resposta;
* mínima carga sobre PostgreSQL;
* isolamento de falhas;
* experiência visual estável.

Este documento especifica:

* ciclo de vida da atualização;
* política de cache;
* invalidação;
* gatilhos de refresh;
* concorrência;
* atualização parcial e total;
* sincronização entre Frontend e Backend.

---

# Visão Geral

Toda atualização do Dashboard deve reconstruir integralmente o `DashboardViewModel`.

Não deve existir atualização individual de componentes.

Fluxo geral:

```text
Usuário

↓

Solicita atualização

↓

Dashboard Controller

↓

DashboardAggregationService

↓

Repositories

↓

Serviços externos

↓

DashboardViewModel

↓

Frontend
```

O Frontend recebe sempre um ViewModel completo.

---

# Fontes de Atualização

O Dashboard pode ser atualizado por diferentes mecanismos.

| Origem                          | Tipo       | Obrigatório            |
| ------------------------------- | ---------- | ---------------------- |
| Primeira abertura da página     | Automático | Sim                    |
| Botão Recarregar                | Manual     | Sim                    |
| Retorno do módulo Fluxos        | Automático | Sim                    |
| Alteração de Configurações      | Automático | Sim                    |
| Atualização periódica (polling) | Opcional   | Não                    |
| Evento interno da aplicação     | Opcional   | Sim, quando disponível |

---

# Ciclo de Vida

A atualização segue sempre a mesma sequência.

```text
Dashboard existente

↓

Refresh solicitado

↓

DashboardAggregationService

↓

Construção do novo ViewModel

↓

Validação

↓

Substituição atômica

↓

Renderização
```

O ViewModel anterior permanece válido até que o novo esteja completamente disponível.

---

# Estratégia de Refresh

Existem dois tipos de atualização.

## Refresh Completo

Reconstrói todo o Dashboard.

Utilizado quando:

* usuário clica em **Recarregar**;
* retorna do módulo Fluxos;
* configurações foram alteradas.

Fluxo:

```text
Refresh

↓

Todos os Services

↓

Novo ViewModel

↓

Renderização
```

---

## Refresh Parcial

Pode ser utilizado futuramente para componentes independentes.

Exemplos:

* apenas Integrações;
* apenas Workflow.

Entretanto, **a versão atual da Manhwateca não deve utilizar atualização parcial**.

Todo refresh deve ser completo para preservar consistência.

---

# Política de Cache

Cada serviço pode manter cache próprio.

Exemplo:

| Informação   | TTL  |
| ------------ | ---- |
| Métricas     | 30 s |
| Workflow     | 10 s |
| Integrações  | 15 s |
| Pendências   | 15 s |
| Próxima ação | 10 s |

O DashboardAggregationService nunca deve manter cache próprio.

Ele apenas consome os caches especializados.

---

# Estratégia de Invalidação

O cache deve ser invalidado quando ocorrer qualquer operação que altere o estado da biblioteca.

## Organizar Biblioteca

Invalidar:

* métricas;
* Workflow;
* pendências.

---

## Catalogar Arquivos

Invalidar:

* métricas;
* Workflow;
* próxima ação.

---

## Resolver IDs

Invalidar:

* métricas;
* Workflow;
* pendências;
* próxima ação.

---

## Atualizar Metadados

Invalidar:

* métricas;
* Workflow.

---

## Sincronizar Notion

Invalidar:

* integrações;
* pendências;
* métricas.

---

# Atualização após Navegação

Ao retornar ao Dashboard:

```text
Fluxos

↓

Dashboard

↓

Dashboard antigo permanece visível

↓

Refreshing

↓

Novo ViewModel

↓

Renderização
```

Essa estratégia evita telas vazias.

---

# Atualização Manual

Ao clicar em **Recarregar**:

```text
Click

↓

Spinner discreto

↓

GET /api/dashboard

↓

Novo ViewModel

↓

Renderização
```

Durante esse processo:

* manter componentes visíveis;
* bloquear múltiplos cliques;
* impedir chamadas concorrentes.

---

# Controle de Concorrência

Nunca permitir duas atualizações simultâneas.

Exemplo:

```text
Refresh

↓

request #1

↓

request #2

✖ Cancelada
```

Estratégias possíveis:

* AbortController (Frontend);
* Request Token;
* Mutex lógico.

Apenas a requisição mais recente deve atualizar a interface.

---

# Atualização Atômica

O Frontend nunca deve substituir componentes individualmente.

Fluxo correto:

```text
ViewModel antigo

↓

Novo ViewModel completo

↓

Substituição única

↓

Re-renderização
```

Isso elimina inconsistências temporárias.

---

# Consistência Temporal

Todos os componentes do Dashboard devem representar o mesmo instante lógico.

Exemplo incorreto:

```text
Métricas
12:00

Workflow
12:02

Pendências
11:58
```

Exemplo correto:

```text
Métricas
12:03

Workflow
12:03

Pendências
12:03
```

O campo `generatedAt` deve refletir esse instante.

---

# Atualização de Componentes

Todos os componentes são atualizados simultaneamente.

```text
DashboardPage

├── Header
├── NextAction
├── Metrics
├── PendingActions
├── Workflow
├── Integrations
└── QuickActions
```

Nenhum componente realiza requisições independentes.

---

# Falhas Durante a Atualização

Caso algum serviço falhe:

```text
DashboardAggregationService

↓

Captura exceção

↓

Marca componente afetado

↓

Continua agregação

↓

Retorna ViewModel
```

Exemplo:

```json
{
  "integrations": [
    {
      "id": "notion",
      "status": "error",
      "message": "Integração indisponível"
    }
  ]
}
```

A atualização não deve ser interrompida por falhas isoladas.

---

# Estratégia de Retry

Caso a atualização falhe completamente:

Fluxo:

```text
Erro

↓

Mensagem

↓

Botão Tentar novamente

↓

Nova requisição
```

Não executar retries automáticos infinitos.

Recomendações:

* máximo de 3 tentativas automáticas;
* backoff exponencial;
* logs estruturados.

---

# Eventos que Disparam Atualização

| Evento                        | Atualização |
| ----------------------------- | ----------- |
| Abrir Dashboard               | Completa    |
| Botão Recarregar              | Completa    |
| Conclusão do Workflow         | Completa    |
| Alteração de Configuração     | Completa    |
| Retorno da Biblioteca         | Opcional    |
| Alteração de filtros (futuro) | Parcial     |

---

# Logs

Cada atualização deve gerar logs.

Exemplo:

```json
{
  "module": "dashboard",
  "operation": "refresh",
  "duration_ms": 182,
  "status": "success",
  "generatedAt": "2026-06-27T00:00:00Z"
}
```

Em caso de erro:

```json
{
  "module": "dashboard",
  "operation": "refresh",
  "status": "error",
  "component": "integration_service",
  "message": "Timeout"
}
```

---

# Métricas de Observabilidade

Devem ser monitorados:

| Métrica                   | Meta     |
| ------------------------- | -------- |
| Tempo médio de refresh    | < 300 ms |
| Percentual de sucesso     | > 99%    |
| Tempo de agregação        | < 200 ms |
| Tempo de renderização     | < 100 ms |
| Atualizações concorrentes | 0        |

---

# Regras Arquiteturais

A atualização deve obedecer às seguintes regras:

* apenas um endpoint para atualização;
* apenas um ViewModel por refresh;
* atualização atômica;
* componentes independentes;
* invalidação orientada por eventos;
* cache localizado nos serviços;
* DashboardAggregationService sem estado persistente;
* nenhuma lógica de atualização distribuída entre componentes.

---

# Checklist

Antes da implementação, verificar:

| Item                          | Obrigatório |
| ----------------------------- | ----------- |
| Refresh completo implementado | ✅           |
| Cache especializado           | ✅           |
| Invalidação por evento        | ✅           |
| Atualização atômica           | ✅           |
| Sem requisições concorrentes  | ✅           |
| Logs estruturados             | ✅           |
| Retry controlado              | ✅           |

---

# Relação com outros documentos

| Documento                 | Conteúdo relacionado                   |
| ------------------------- | -------------------------------------- |
| 03-api-dashboard.md       | Endpoint `/api/dashboard`              |
| 05-componentes.md         | Componentes atualizados pelo ViewModel |
| 06-estados.md             | Estado `Refreshing`                    |
| 09-tratamento-de-erros.md | Estratégias de recuperação após falhas |
| 10-performance.md         | Impacto do refresh no desempenho       |

---

# Conclusão

A estratégia de atualização do Dashboard baseia-se na reconstrução completa e atômica do `DashboardViewModel`, preservando a consistência entre todos os componentes da interface. O uso de caches especializados, invalidação orientada por eventos e atualização sem interrupção visual garante uma experiência fluida ao usuário e reduz significativamente a complexidade da camada de apresentação.
