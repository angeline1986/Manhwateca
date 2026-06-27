# Arquitetura

> Documento: **02-arquitetura.md**

---

# Objetivo

Este documento descreve a arquitetura técnica do módulo **Fluxos**, apresentando sua decomposição em componentes, responsabilidades, fluxo de dados, padrões arquiteturais e mecanismos de comunicação entre as camadas da aplicação.

O objetivo é estabelecer uma arquitetura modular, desacoplada e extensível, capaz de suportar a evolução do Workflow sem aumentar significativamente a complexidade do sistema.

---

# Visão Arquitetural

O módulo Fluxos é estruturado em camadas, onde cada uma possui responsabilidades claramente definidas e comunicação exclusivamente com a camada imediatamente inferior.

```text
┌──────────────────────────────────────────────┐
│                  Interface Web               │
└──────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────┐
│           Workflow Controller                │
└──────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────┐
│          Workflow Orchestrator               │
└──────────────────────────────────────────────┘
        │          │           │
        ▼          ▼           ▼
 Organizar   Catalogar   Resolver IDs
        │          │           │
        ▼          ▼           ▼
 Atualizar Metadados    Sincronizar Notion
        │
        ▼
┌──────────────────────────────────────────────┐
│                Services                      │
└──────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────┐
│             Repositories                     │
└──────────────────────────────────────────────┘
        │
        ▼
 PostgreSQL • MangaUpdates • Notion • Biblioteca
```

---

# Arquitetura em Camadas

## Interface (Presentation Layer)

Responsável exclusivamente por:

* renderizar a interface;
* exibir progresso;
* enviar comandos do usuário;
* consumir os endpoints do backend.

A interface nunca executa regras de negócio.

---

## Controller Layer

Responsabilidades:

* receber requisições HTTP;
* validar parâmetros básicos;
* iniciar o Workflow;
* retornar respostas padronizadas.

Não contém regras de negócio.

---

## Orchestrator Layer

É o núcleo do módulo Fluxos.

Responsável por:

* controlar a sequência das etapas;
* validar pré-condições;
* controlar transições;
* consolidar resultados;
* interromper o Workflow quando necessário;
* publicar eventos internos.

Nenhuma regra específica de integração deve permanecer nesta camada.

---

## Service Layer

Cada etapa do Workflow possui seu próprio serviço.

Exemplo:

```text
WorkflowOrchestrator
        │
        ├── OrganizationService
        ├── CatalogService
        ├── IdResolutionService
        ├── MetadataService
        └── NotionSyncService
```

Cada serviço implementa apenas a lógica da sua etapa.

---

## Repository Layer

Responsável por:

* leitura;
* escrita;
* consultas;
* persistência.

Nenhuma regra de negócio deve existir nesta camada.

---

# Componentes Principais

## WorkflowController

Responsável por expor os endpoints públicos.

Exemplos:

* iniciar Workflow;
* consultar status;
* cancelar execução;
* consultar histórico.

---

## WorkflowOrchestrator

Coordena toda a execução.

Responsabilidades:

* iniciar etapas;
* controlar estados;
* publicar progresso;
* tratar interrupções;
* finalizar execução.

É o único componente autorizado a controlar a ordem das etapas.

---

## Stage Services

Cada etapa é implementada de forma independente.

```text
OrganizationService

CatalogService

IdResolutionService

MetadataService

NotionSyncService
```

Todos implementam uma interface comum de execução.

---

# Contrato das Etapas

Cada serviço deve expor uma interface padronizada.

```python
class WorkflowStage:

    def validate(self):
        ...

    def execute(self):
        ...

    def finalize(self):
        ...
```

Essa padronização permite adicionar novas etapas sem alterar o Orchestrator.

---

# Fluxo de Execução

```text
Usuário

↓

WorkflowController

↓

WorkflowOrchestrator

↓

validate()

↓

execute()

↓

finalize()

↓

Próxima etapa
```

Cada etapa é executada somente após a conclusão da anterior.

---

# Comunicação entre Componentes

A comunicação deve ocorrer exclusivamente por interfaces públicas.

Exemplo:

```text
Controller

↓

Orchestrator

↓

Service

↓

Repository
```

É proibido:

* Controller acessar Repository;
* UI acessar Services;
* Repository acessar APIs externas diretamente sem abstração apropriada.

---

# Padrões Arquiteturais

## Repository Pattern

Utilizado para abstrair o acesso ao PostgreSQL.

Benefícios:

* desacoplamento;
* facilidade de testes;
* substituição de persistência.

---

## Service Layer

Centraliza regras de negócio.

Cada serviço representa uma única responsabilidade.

---

## Orchestrator Pattern

O Workflow é coordenado por um componente dedicado.

Vantagens:

* controle centralizado;
* baixo acoplamento;
* facilidade de manutenção.

---

## Strategy Pattern

Pode ser utilizado para encapsular diferentes estratégias de execução de etapas, permitindo futuras expansões sem alterar o fluxo principal.

---

## Dependency Injection

Todas as dependências devem ser fornecidas externamente.

Exemplo:

```python
MetadataService(
    manga_updates_client,
    manga_repository,
    logger,
)
```

Evita dependências ocultas e facilita testes unitários.

---

# Tratamento de Dependências

As integrações externas devem ser abstraídas.

```text
MetadataService

↓

MangaUpdatesClient

↓

API
```

A lógica do serviço nunca deve depender diretamente da implementação da API.

---

# Estado da Execução

O Orchestrator deve controlar:

* etapa atual;
* percentual;
* tempo de execução;
* quantidade processada;
* erros;
* alertas;
* cancelamentos.

Essas informações alimentam a interface em tempo real.

---

# Escalabilidade

A arquitetura deve permitir:

* inclusão de novas etapas;
* substituição de integrações;
* execução de novos serviços;
* evolução do Workflow sem alterações estruturais.

Adicionar uma nova etapa deve exigir apenas:

1. Implementar um novo Stage Service.
2. Registrá-lo no Orchestrator.
3. Atualizar a documentação correspondente.

---

# Observabilidade

Todos os componentes devem produzir informações observáveis.

Exemplos:

* logs estruturados;
* métricas;
* eventos;
* duração das etapas;
* quantidade de itens processados.

Essas informações são utilizadas pelo Dashboard e pelas ferramentas de diagnóstico.

---

# Relação com os Demais Documentos

| Documento                               | Complementa                    |
| --------------------------------------- | ------------------------------ |
| 01-visao-geral.md                       | Objetivos arquiteturais        |
| 03-api-e-contratos.md                   | Comunicação entre UI e Backend |
| 04-processamento.md                     | Pipeline interno do Workflow   |
| 05-integracoes.md                       | Arquitetura das integrações    |
| 06-performance-e-tratamento-de-erros.md | Estratégias de resiliência     |

---

# Conclusão

A arquitetura do módulo **Fluxos** é baseada em uma clara separação de responsabilidades, tendo o **Workflow Orchestrator** como elemento central de coordenação e serviços especializados para cada etapa do processo. O uso combinado de camadas bem definidas, padrões como Repository, Service Layer, Orchestrator e Dependency Injection garante uma implementação extensível, testável e de fácil manutenção, permitindo que o Workflow evolua sem comprometer a estabilidade do restante da aplicação.
