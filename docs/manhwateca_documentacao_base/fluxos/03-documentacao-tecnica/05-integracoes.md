# Integrações

> Documento: **05-integracoes.md**

---

# Objetivo

Este documento descreve a arquitetura técnica das integrações utilizadas pelo módulo **Fluxos**, definindo responsabilidades, contratos internos, estratégias de comunicação, tratamento de falhas e boas práticas de implementação.

O Workflow da Manhwateca depende de quatro recursos principais:

* Biblioteca local;
* PostgreSQL;
* MangaUpdates;
* Notion.

Cada integração deve ser implementada de forma desacoplada, permitindo evolução independente e facilidade de testes.

---

# Visão Geral

A arquitetura proposta separa completamente o Workflow das implementações específicas de cada serviço.

```text
                    Workflow
                        │
                        ▼
               Integration Services
        ┌──────────┼──────────┬──────────┐
        ▼          ▼          ▼          ▼
 LibraryService Database  MangaUpdates  Notion
                        Client         Client
```

O Orchestrator nunca deve consumir APIs externas diretamente.

---

# Organização dos Componentes

Cada integração deve possuir uma camada própria.

```text
WorkflowOrchestrator
        │
        ▼
Stage Service
        │
        ▼
Integration Service
        │
        ▼
Client
        │
        ▼
Serviço Externo
```

Separar **Service** e **Client** facilita testes, substituição de bibliotecas e simulação de falhas.

---

# Biblioteca Local

## Responsabilidade

Representa a origem física das obras.

É utilizada nas etapas:

* Organização;
* Catalogação.

---

## Responsabilidades do LibraryService

* localizar diretórios;
* listar obras;
* validar estrutura;
* detectar alterações;
* normalizar caminhos.

---

## Interface sugerida

```python
class LibraryService:

    def scan()

    def validate()

    def list_works()

    def detect_changes()
```

---

# PostgreSQL

## Responsabilidade

Fonte oficial de persistência da Manhwateca.

Toda leitura e gravação deve ocorrer por meio da camada Repository.

---

## Organização

```text
Workflow

↓

Service

↓

Repository

↓

PostgreSQL
```

Nunca permitir:

* SQL na UI;
* SQL no Controller;
* SQL no Orchestrator.

---

## Operações

Leitura:

* obras;
* etapas;
* histórico;
* configurações.

Escrita:

* metadados;
* estados;
* progresso;
* sincronizações;
* logs.

---

# MangaUpdates

## Responsabilidade

Fornecer:

* IDs oficiais;
* metadados;
* títulos alternativos;
* autores;
* artistas;
* gêneros;
* status;
* quantidade de capítulos.

---

## Organização

```text
MetadataService

↓

MangaUpdatesClient

↓

HTTP Client

↓

API
```

---

## Interface sugerida

```python
class MangaUpdatesClient:

    def search()

    def get_series()

    def get_metadata()
```

---

## Estratégia de Retry

Erros temporários devem utilizar política controlada de repetição.

Exemplo:

* tentativa 1;
* tentativa 2;
* tentativa 3;
* registrar falha.

Jamais repetir indefinidamente.

---

## Timeout

Toda chamada deve possuir timeout configurado.

A indisponibilidade da API nunca poderá bloquear indefinidamente o Workflow.

---

# Notion

## Responsabilidade

Sincronizar a representação externa da biblioteca.

---

## Organização

```text
NotionSyncService

↓

NotionClient

↓

HTTP

↓

Notion API
```

---

## Interface sugerida

```python
class NotionClient:

    def create_page()

    def update_page()

    def query_database()
```

---

# Abstração das Integrações

Nenhum componente do Workflow deve conhecer detalhes da implementação externa.

Exemplo:

```python
metadata_service.update(work)
```

e não

```python
requests.post(...)
```

Toda comunicação HTTP deve permanecer encapsulada no Client correspondente.

---

# Contrato Interno

As integrações devem retornar objetos padronizados.

Exemplo:

```python
Result(
    success=True,
    data=...,
    warnings=[],
    errors=[]
)
```

Isso evita tratamento específico para cada serviço.

---

# Tratamento de Falhas

As falhas devem ser classificadas.

| Tipo         | Exemplo         | Tratamento        |
| ------------ | --------------- | ----------------- |
| Temporária   | Timeout         | Retry             |
| Permanente   | 404             | Registrar erro    |
| Configuração | Token inválido  | Interromper etapa |
| Validação    | Dados inválidos | Ignorar registro  |

Cada categoria deve possuir comportamento previsível.

---

# Observabilidade

Cada integração deve registrar:

* início da chamada;
* tempo de resposta;
* código retornado;
* quantidade de itens;
* resultado final.

Essas informações alimentam logs e métricas.

---

# Logs

Cada operação deve registrar, no mínimo:

```text
executionId

service

operation

duration

status

error
```

Nunca registrar:

* tokens;
* credenciais;
* informações sensíveis.

---

# Estratégia de Cache

Quando apropriado, respostas poderão ser reutilizadas.

Exemplos:

* pesquisa recente de IDs;
* metadados inalterados;
* configurações do Notion.

O cache deve possuir política de expiração claramente definida.

---

# Versionamento

Os Clients devem encapsular diferenças entre versões das APIs.

O restante da aplicação nunca deve depender de endpoints específicos.

---

# Testabilidade

Cada integração deve permitir substituição por implementações simuladas (mocks ou fakes).

Exemplo:

```python
FakeMangaUpdatesClient

FakeNotionClient

FakeLibraryService
```

Isso permite testes determinísticos sem dependência de serviços externos.

---

# Evolução

Novas integrações deverão seguir a mesma estrutura.

```text
Workflow

↓

Service

↓

Integration Service

↓

Client

↓

API
```

Nenhuma nova integração deve acessar diretamente o Workflow.

---

# Relação com os Demais Documentos

| Documento                               | Complementa                                |
| --------------------------------------- | ------------------------------------------ |
| 02-arquitetura.md                       | Organização das camadas                    |
| 03-api-e-contratos.md                   | Contratos públicos                         |
| 04-processamento.md                     | Pipeline de execução                       |
| 06-performance-e-tratamento-de-erros.md | Retry, timeout e resiliência               |
| 07-testes.md                            | Estratégias de mock e testes de integração |

---

# Conclusão

A arquitetura de integrações do módulo **Fluxos** foi concebida para isolar completamente o Workflow das implementações específicas de PostgreSQL, Biblioteca, MangaUpdates e Notion. A adoção de **Services**, **Clients**, contratos padronizados e estratégias consistentes de retry, timeout e observabilidade reduz o acoplamento, facilita testes e torna a evolução das integrações significativamente mais segura.
