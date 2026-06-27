# Dashboard — Documentação Técnica

## 09 - Tratamento de Erros

---

# Objetivo

Este documento define a estratégia oficial de tratamento de erros do módulo **Dashboard** da Manhwateca.

O Dashboard é um módulo agregador que depende de diversas fontes de dados, incluindo:

* PostgreSQL
* Sistema de Arquivos (Biblioteca)
* MangaUpdates
* Notion
* Serviços internos do Workflow

Por esse motivo, a arquitetura deve ser resiliente a falhas parciais, permitindo que a interface continue funcional sempre que possível.

O princípio adotado é:

> **Falhas isoladas nunca devem impedir o carregamento completo do Dashboard, exceto quando comprometem a construção do ViewModel como um todo.**

---

# Objetivos

A estratégia de tratamento de erros possui cinco objetivos principais.

* Isolar falhas por componente.
* Evitar indisponibilidade total da interface.
* Produzir mensagens consistentes para o usuário.
* Registrar informações completas para diagnóstico.
* Garantir previsibilidade para Frontend e Backend.

---

# Classificação dos Erros

Todos os erros devem pertencer a uma das categorias abaixo.

| Categoria                  | Severidade | Interrompe o Dashboard |
| -------------------------- | ---------- | ---------------------- |
| Erro de infraestrutura     | Alta       | Depende da origem      |
| Erro de integração externa | Média      | Não                    |
| Erro de dados              | Média      | Não                    |
| Erro de negócio            | Baixa      | Não                    |
| Erro inesperado            | Crítica    | Sim                    |

---

# Erros de Infraestrutura

São falhas relacionadas aos componentes fundamentais da aplicação.

Exemplos:

* PostgreSQL indisponível;
* diretório da biblioteca inacessível;
* falha de leitura do sistema de arquivos;
* corrupção do banco.

Exemplo:

```text
DashboardAggregationService

↓

PostgreSQL

↓

ConnectionError
```

Quando o banco de dados estiver indisponível, o Dashboard poderá retornar:

```http
HTTP 503 Service Unavailable
```

ou

```http
HTTP 500 Internal Server Error
```

dependendo da estratégia adotada pelo projeto.

---

# Erros de Integração

Integrações externas nunca devem impedir a construção do Dashboard.

Exemplos:

* timeout do MangaUpdates;
* timeout do Notion;
* API indisponível;
* limite de requisições.

Fluxo esperado:

```text
DashboardAggregationService

↓

NotionService

↓

Timeout

↓

IntegrationStatus = ERROR

↓

Dashboard continua
```

O componente correspondente deve apresentar o estado **error**, mantendo os demais componentes operacionais.

---

# Erros de Dados

São situações em que os dados existem, mas não atendem às expectativas.

Exemplos:

* obra sem ID;
* sincronização pendente;
* metadados incompletos;
* Workflow inconsistente.

Esses casos não representam falhas técnicas.

Devem gerar:

* pendências;
* recomendações;
* alertas visuais.

Nunca exceções.

---

# Erros de Negócio

São estados previstos pelas regras da aplicação.

Exemplos:

* biblioteca vazia;
* nenhuma obra cadastrada;
* nenhum capítulo novo;
* nenhuma pendência.

Esses estados devem produzir componentes em **Empty State**, jamais erros.

---

# Erros Inesperados

São exceções não tratadas.

Exemplos:

* NullReference;
* IndexError;
* TypeError;
* ValueError inesperado;
* falhas de serialização.

Fluxo:

```text
Exception

↓

Logger

↓

DashboardErrorHandler

↓

HTTP 500
```

---

# Hierarquia de Exceções

Recomenda-se utilizar exceções específicas.

```text
DashboardException

├── InfrastructureException

├── IntegrationException

├── ValidationException

├── AggregationException

└── SerializationException
```

Nunca utilizar `Exception` genericamente fora da camada superior.

---

# Estratégia de Captura

Cada serviço deve capturar apenas as exceções que conhece.

Exemplo:

```python
try:
    notion.check_status()
except TimeoutError:
    ...
```

Nunca capturar indiscriminadamente:

```python
except Exception:
    ...
```

Essa prática dificulta o diagnóstico.

---

# Estratégia do Aggregation Service

O Aggregation Service deve continuar construindo o ViewModel mesmo diante de falhas isoladas.

Exemplo:

```text
Metrics OK

↓

Workflow OK

↓

Notion ERROR

↓

Integrations WARNING

↓

Dashboard completo
```

Somente falhas estruturais impedem a construção do ViewModel.

---

# Estratégia de Degradação

Quando um serviço falhar:

```text
Serviço indisponível

↓

Valor conhecido

↓

Status ERROR

↓

Mensagem amigável
```

Exemplo JSON:

```json
{
  "id": "notion",
  "status": "error",
  "message": "Integração temporariamente indisponível."
}
```

O Frontend nunca deve inferir o motivo do erro.

---

# Mensagens ao Usuário

As mensagens devem ser:

* objetivas;
* compreensíveis;
* orientadas à ação.

Exemplos:

| Correta                              | Evitar                   |
| ------------------------------------ | ------------------------ |
| Não foi possível consultar o Notion. | Exception 504            |
| PostgreSQL indisponível.             | psycopg OperationalError |
| Biblioteca não encontrada.           | FileNotFoundError        |

Detalhes técnicos devem permanecer apenas nos logs.

---

# Estratégia de Retry

Retries automáticos são permitidos apenas para erros transitórios.

Exemplos:

* timeout;
* conexão recusada;
* indisponibilidade temporária.

Configuração recomendada:

| Tentativa | Intervalo  |
| --------- | ---------- |
| 1         | imediato   |
| 2         | 1 segundo  |
| 3         | 2 segundos |

Após três tentativas, a falha deve ser propagada.

---

# Logs

Todos os erros devem gerar logs estruturados.

Exemplo:

```json
{
  "module": "dashboard",
  "service": "integration_service",
  "integration": "notion",
  "severity": "warning",
  "exception": "TimeoutError",
  "duration_ms": 2150,
  "timestamp": "2026-06-27T00:00:00Z"
}
```

---

# Correlação

Cada atualização deve possuir um identificador único.

Exemplo:

```json
{
  "requestId": "3d43df84",
  "operation": "dashboard.refresh"
}
```

Todos os logs gerados durante aquela atualização devem compartilhar o mesmo `requestId`.

Isso facilita rastreamento distribuído.

---

# Frontend

O Frontend nunca deve interpretar exceções.

Ele apenas consome estados.

Exemplo:

```json
{
  "status": "error",
  "message": "Integração indisponível."
}
```

A decisão sobre severidade pertence exclusivamente ao Backend.

---

# Observabilidade

Indicadores recomendados:

| Métrica                    | Meta  |
| -------------------------- | ----- |
| Taxa de erro               | < 1%  |
| Falhas críticas            | 0     |
| Retry bem-sucedido         | > 80% |
| Tempo médio de recuperação | < 5 s |

---

# Casos de Falha

## PostgreSQL indisponível

Resultado esperado:

* Dashboard indisponível;
* erro global;
* botão "Tentar novamente".

---

## MangaUpdates indisponível

Resultado esperado:

* Integração em erro;
* Dashboard funcional;
* Workflow preservado.

---

## Notion indisponível

Resultado esperado:

* Integração em erro;
* sincronização indisponível;
* demais componentes funcionais.

---

## Biblioteca inacessível

Resultado esperado:

* pendência crítica;
* Workflow bloqueado;
* Dashboard funcional, quando possível.

---

## Erro inesperado

Resultado esperado:

* log estruturado;
* resposta HTTP 500;
* página de erro do Dashboard.

---

# Anti-patterns

As seguintes práticas são proibidas:

* ocultar exceções silenciosamente;
* utilizar `print()` para registrar erros;
* retornar mensagens técnicas ao usuário;
* repetir infinitamente requisições com falha;
* capturar exceções genéricas em todas as camadas;
* misturar lógica de recuperação com renderização.

---

# Checklist

| Item                        | Obrigatório |
| --------------------------- | ----------- |
| Exceções tipadas            | ✅           |
| Logs estruturados           | ✅           |
| Request ID                  | ✅           |
| Retry controlado            | ✅           |
| Falhas isoladas             | ✅           |
| Mensagens amigáveis         | ✅           |
| Sem detalhes técnicos na UI | ✅           |

---

# Relação com outros documentos

| Documento           | Conteúdo relacionado           |
| ------------------- | ------------------------------ |
| 03-api-dashboard.md | Contratos de erro da API       |
| 06-estados.md       | Estado `Error` dos componentes |
| 08-atualizacao.md   | Recuperação durante o refresh  |
| 10-performance.md   | Impacto dos retries e timeouts |

---

# Conclusão

O tratamento de erros do Dashboard segue uma estratégia de **falha isolada e degradação controlada**, onde cada integração é tratada independentemente e apenas falhas estruturais impedem a geração do `DashboardViewModel`. Essa abordagem aumenta a disponibilidade da aplicação, facilita o diagnóstico por meio de logs estruturados e proporciona uma experiência consistente ao usuário, mesmo diante de indisponibilidades temporárias de serviços externos.
