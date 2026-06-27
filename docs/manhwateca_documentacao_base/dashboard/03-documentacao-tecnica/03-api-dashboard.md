# Dashboard — Documentação Técnica

## 03 - API Dashboard

---

# Objetivo

Este documento especifica os contratos de comunicação entre o Backend e o Frontend do módulo **Dashboard**.

Todo o Frontend deve consumir **um único endpoint**, responsável por retornar um **Dashboard ViewModel** completamente consolidado.

O objetivo é eliminar múltiplas chamadas HTTP, reduzir o acoplamento da interface com os serviços internos e garantir consistência entre todos os componentes renderizados.

---

# Arquitetura da API

O Dashboard deve utilizar exclusivamente o endpoint abaixo.

```http
GET /api/dashboard
```

Não devem existir endpoints separados para:

* métricas;
* workflow;
* pendências;
* integrações;
* próximo passo.

Toda a informação deve ser agregada antes da serialização.

---

# Fluxo da Requisição

```text
Frontend

↓

GET /api/dashboard

↓

Dashboard Controller

↓

DashboardAggregationService

↓

DashboardViewModel

↓

JSON

↓

Frontend
```

---

# Endpoint

## GET /api/dashboard

Retorna o estado completo do Dashboard.

### Request

```http
GET /api/dashboard HTTP/1.1
Accept: application/json
```

Nenhum parâmetro é necessário.

---

# Response

```json
{
  "generatedAt": "2026-06-27T00:00:00Z",
  "version": "1.0",
  "status": "success",

  "nextAction": {},

  "metrics": {},

  "workflow": {},

  "pendingActions": [],

  "integrations": [],

  "quickActions": []
}
```

---

# Response Status

| Campo          | Tipo   | Obrigatório | Descrição                    |
| -------------- | ------ | ----------- | ---------------------------- |
| generatedAt    | string | Sim         | Data de geração do ViewModel |
| version        | string | Sim         | Versão do contrato           |
| status         | string | Sim         | success / warning / error    |
| nextAction     | object | Sim         | Próxima ação recomendada     |
| metrics        | object | Sim         | Métricas agregadas           |
| workflow       | object | Sim         | Estado do Workflow           |
| pendingActions | array  | Sim         | Lista de pendências          |
| integrations   | array  | Sim         | Estado das integrações       |
| quickActions   | array  | Sim         | Atalhos disponíveis          |

---

# nextAction

Representa a principal ação recomendada.

```json
{
  "id": "resolve_ids",
  "title": "Resolver IDs",
  "description": "Existem 8 obras sem identificação.",
  "priority": "high",
  "action": "/fluxos#resolver-ids",
  "buttonLabel": "Continuar fluxo"
}
```

## Campos

| Campo       | Tipo   | Descrição                |
| ----------- | ------ | ------------------------ |
| id          | string | Identificador interno    |
| title       | string | Título apresentado na UI |
| description | string | Explicação resumida      |
| priority    | string | low, medium, high        |
| action      | string | Destino da navegação     |
| buttonLabel | string | Texto do botão           |

---

# metrics

```json
{
  "libraryCount": 347,
  "newChapters": 23,
  "missingIds": 8,
  "pendingNotionSync": 14
}
```

## Campos

| Campo             | Tipo    | Origem          |
| ----------------- | ------- | --------------- |
| libraryCount      | integer | PostgreSQL      |
| newChapters       | integer | MangaRepository |
| missingIds        | integer | MangaRepository |
| pendingNotionSync | integer | SyncRepository  |

Todos os valores devem ser inteiros maiores ou iguais a zero.

---

# workflow

```json
{
  "currentStep": 3,
  "totalSteps": 5,
  "progress": 60,
  "steps": [
    {
      "id": "organize",
      "status": "completed"
    },
    {
      "id": "catalog",
      "status": "completed"
    },
    {
      "id": "resolve_ids",
      "status": "running"
    },
    {
      "id": "metadata",
      "status": "pending"
    },
    {
      "id": "notion",
      "status": "pending"
    }
  ]
}
```

## Status possíveis

| Valor     | Significado        |
| --------- | ------------------ |
| pending   | Ainda não iniciado |
| running   | Em execução        |
| completed | Finalizado         |
| blocked   | Bloqueado          |
| error     | Falhou             |

---

# pendingActions

Lista ordenada por prioridade.

```json
[
  {
    "id": "missing_ids",
    "title": "Resolver IDs",
    "severity": "high",
    "description": "8 obras aguardam identificação.",
    "action": "/fluxos#resolver-ids"
  },
  {
    "id": "notion_sync",
    "title": "Sincronizar Notion",
    "severity": "medium",
    "description": "14 alterações pendentes.",
    "action": "/fluxos#notion"
  }
]
```

## Ordenação

O backend deve ordenar:

1. High
2. Medium
3. Low

O Frontend nunca deve ordenar essa lista.

---

# integrations

```json
[
  {
    "id": "postgres",
    "label": "PostgreSQL",
    "status": "healthy",
    "message": "Operacional"
  },
  {
    "id": "mangaupdates",
    "label": "MangaUpdates",
    "status": "warning",
    "message": "Resposta lenta"
  },
  {
    "id": "notion",
    "label": "Notion",
    "status": "error",
    "message": "Token inválido"
  }
]
```

## Status possíveis

| Valor   | Cor UI   |
| ------- | -------- |
| healthy | Verde    |
| warning | Amarelo  |
| error   | Vermelho |
| unknown | Cinza    |

---

# quickActions

```json
[
  {
    "id": "library",
    "label": "Biblioteca",
    "route": "/biblioteca"
  },
  {
    "id": "flows",
    "label": "Fluxos",
    "route": "/fluxos"
  },
  {
    "id": "refresh",
    "label": "Recarregar",
    "action": "refresh"
  },
  {
    "id": "settings",
    "label": "Configurações",
    "route": "/configuracoes"
  }
]
```

---

# Resposta sem pendências

Quando nenhuma pendência existir:

```json
{
  "pendingActions": []
}
```

O backend nunca deve retornar `null`.

---

# Resposta sem integrações

Mesmo que alguma integração esteja desabilitada, a estrutura deve permanecer consistente.

Exemplo:

```json
{
  "id": "notion",
  "status": "unknown",
  "message": "Integração desabilitada"
}
```

---

# Resposta de erro

Quando o Dashboard não puder ser construído:

```http
HTTP/1.1 500 Internal Server Error
```

```json
{
  "status": "error",
  "error": {
    "code": "DASHBOARD_BUILD_FAILED",
    "message": "Não foi possível construir o Dashboard."
  }
}
```

---

# Regras de serialização

O contrato deve obedecer às seguintes regras:

* Nunca retornar `null` quando um objeto vazio puder ser utilizado.
* Arrays vazios devem ser serializados como `[]`.
* Campos booleanos nunca devem ser representados como strings.
* Datas devem utilizar ISO-8601 em UTC.
* Todos os identificadores internos devem permanecer estáveis entre versões.

---

# Versionamento

O contrato deve ser compatível entre versões.

Alterações incompatíveis devem gerar uma nova versão do endpoint.

Exemplo:

```text
/api/v1/dashboard

/api/v2/dashboard
```

---

# Princípios do contrato

O contrato deve seguir os seguintes princípios:

* **Backend-driven UI:** toda a lógica de agregação é responsabilidade do servidor.
* **Contrato estável:** o Frontend deve depender apenas do ViewModel.
* **Baixo acoplamento:** alterações internas dos serviços não devem impactar a interface.
* **Compatibilidade:** novos campos podem ser adicionados sem quebrar consumidores existentes.

---

# Relação com outros documentos

Este documento define apenas os contratos HTTP.

Os detalhes de implementação encontram-se em:

| Documento             | Conteúdo                                        |
| --------------------- | ----------------------------------------------- |
| 02-arquitetura.md     | Fluxo interno da aplicação                      |
| 04-modelo-de-dados.md | Origem dos dados e consultas SQL                |
| 05-componentes.md     | Mapeamento dos campos para os componentes da UI |
| 06-estados.md         | Estados visuais derivados das respostas da API  |
