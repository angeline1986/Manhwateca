# API e Contratos

> Documento: **03-api-e-contratos.md**

---

# Objetivo

Este documento define os contratos de comunicação entre o Front-end e o Back-end do módulo **Fluxos**.

Seu objetivo é estabelecer uma API estável, previsível e desacoplada da implementação interna, permitindo que a interface interaja com o Workflow exclusivamente por meio de endpoints públicos.

Os contratos descritos neste documento representam o formato esperado das requisições e respostas. A implementação interna pode evoluir sem impacto para a interface, desde que esses contratos sejam preservados.

---

# Princípios

A API do módulo Fluxos deve seguir os seguintes princípios:

* Stateless;
* JSON como formato padrão;
* versionamento por URL;
* respostas consistentes;
* tratamento uniforme de erros;
* contratos independentes da implementação interna.

---

# Endpoints

| Método | Endpoint                        | Finalidade                          |
| ------ | ------------------------------- | ----------------------------------- |
| GET    | `/api/flows/status`             | Consulta o estado atual do Workflow |
| POST   | `/api/flows/start`              | Inicia o Workflow completo          |
| POST   | `/api/flows/stages/{stage}/run` | Executa uma etapa específica        |
| POST   | `/api/flows/cancel`             | Solicita o cancelamento da execução |
| GET    | `/api/flows/history`            | Consulta o histórico de execuções   |
| GET    | `/api/flows/integrations`       | Consulta o estado das integrações   |

---

# Modelo de Resposta

Todas as respostas devem seguir a mesma estrutura.

```json
{
  "success": true,
  "timestamp": "2026-06-27T01:35:00Z",
  "data": {},
  "errors": [],
  "warnings": []
}
```

---

# Consulta do Status

## Request

```http
GET /api/flows/status
```

---

## Response

```json
{
  "success": true,
  "data": {
    "running": true,
    "currentStage": "metadata",
    "progress": {
      "current": 4,
      "total": 5,
      "percent": 80
    },
    "startedAt": "2026-06-27T01:20:18Z"
  }
}
```

---

# Iniciar Workflow

## Request

```http
POST /api/flows/start
```

Corpo:

```json
{
  "force": false
}
```

`force` indica se uma nova execução poderá substituir uma execução anterior interrompida.

---

## Response

```json
{
  "success": true,
  "data": {
    "executionId": "wf_20260627_001",
    "status": "running"
  }
}
```

---

# Executar Etapa Individual

## Request

```http
POST /api/flows/stages/metadata/run
```

ou

```http
POST /api/flows/stages/notion/run
```

---

## Response

```json
{
  "success": true,
  "data": {
    "stage": "metadata",
    "started": true
  }
}
```

---

# Cancelar Workflow

## Request

```http
POST /api/flows/cancel
```

---

## Response

```json
{
  "success": true,
  "data": {
    "status": "cancel_requested"
  }
}
```

O cancelamento deve ser tratado como uma solicitação assíncrona.

---

# Histórico

## Request

```http
GET /api/flows/history
```

---

## Response

```json
{
  "success": true,
  "data": [
    {
      "executionId": "wf_20260627_001",
      "startedAt": "...",
      "finishedAt": "...",
      "duration": 523,
      "status": "completed"
    }
  ]
}
```

---

# Integrações

## Request

```http
GET /api/flows/integrations
```

---

## Response

```json
{
  "success": true,
  "data": {
    "database": "online",
    "library": "online",
    "mangaupdates": "online",
    "notion": "offline"
  }
}
```

---

# Modelo de Erro

Todas as falhas devem utilizar o mesmo contrato.

```json
{
  "success": false,
  "errors": [
    {
      "code": "FLOW_DATABASE_UNAVAILABLE",
      "message": "PostgreSQL indisponível."
    }
  ]
}
```

O campo `message` é destinado à interface.

O campo `code` é utilizado pela aplicação para tratamento programático.

---

# Estados do Workflow

O Backend deve utilizar um conjunto padronizado de estados.

| Valor                   | Significado                    |
| ----------------------- | ------------------------------ |
| idle                    | Nenhuma execução               |
| validating              | Executando validações iniciais |
| running                 | Workflow em andamento          |
| cancelling              | Cancelamento solicitado        |
| cancelled               | Cancelado                      |
| completed               | Finalizado                     |
| completed_with_warnings | Finalizado com alertas         |
| failed                  | Finalizado com erro            |

---

# Estados das Etapas

Cada etapa deve informar seu próprio estado.

```json
{
  "stage": "metadata",
  "status": "running",
  "progress": 62
}
```

Valores possíveis:

* waiting
* validating
* running
* completed
* completed_with_warnings
* skipped
* failed
* cancelled

---

# Modelo de Progresso

```json
{
  "current": 382,
  "total": 684,
  "percent": 56,
  "elapsedSeconds": 183,
  "estimatedRemainingSeconds": 145
}
```

Essas informações alimentam a barra de progresso da interface.

---

# Modelo de Integração

```json
{
  "database": {
    "status": "online"
  },
  "library": {
    "status": "online"
  },
  "mangaupdates": {
    "status": "warning"
  },
  "notion": {
    "status": "offline"
  }
}
```

Cada integração deve possuir estrutura independente, permitindo a inclusão futura de novas propriedades.

---

# Compatibilidade

Os contratos públicos da API devem preservar compatibilidade retroativa.

Diretrizes:

* não remover propriedades existentes;
* adicionar novos campos como opcionais;
* manter semântica dos valores;
* versionar alterações incompatíveis.

---

# Segurança

A API deve validar:

* parâmetros obrigatórios;
* formato das requisições;
* estado atual do Workflow;
* permissões do usuário (quando aplicável).

Requisições inválidas devem retornar erro padronizado.

---

# Relação com os Demais Documentos

| Documento           | Complementa                                  |
| ------------------- | -------------------------------------------- |
| 02-arquitetura.md   | Componentes responsáveis pelos endpoints     |
| 04-processamento.md | Pipeline interno executado após cada chamada |
| 05-integracoes.md   | Serviços consumidos pelos endpoints          |
| 07-testes.md        | Estratégia de validação dos contratos        |

---

# Conclusão

Os contratos definidos para a API do módulo **Fluxos** estabelecem uma interface estável entre Front-end e Back-end, isolando a implementação interna das necessidades da interface. A padronização de endpoints, modelos de resposta, estados e erros reduz o acoplamento entre as camadas da aplicação e facilita tanto a evolução do Workflow quanto a automação de testes e a integração com futuros clientes da API.
