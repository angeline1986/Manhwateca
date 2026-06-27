# Visão Geral

> Documento: **01-visao-geral.md**

---

# Objetivo

Este documento apresenta a visão técnica do módulo **Fluxos**, descrevendo seu papel dentro da arquitetura da Manhwateca, seus objetivos de engenharia, responsabilidades, limites de atuação e princípios de implementação.

O módulo Fluxos é responsável por orquestrar todo o processamento operacional da aplicação. Ele coordena a execução das etapas do Workflow, integra os diferentes serviços da plataforma e garante que a biblioteca local evolua de um conjunto de arquivos para um catálogo estruturado e sincronizado.

---

# Papel Arquitetural

Dentro da arquitetura da Manhwateca, o módulo Fluxos atua como um **orquestrador de processos**.

Sua responsabilidade não é executar diretamente todas as regras de negócio, mas coordenar a execução dos serviços responsáveis por cada etapa do Workflow.

```text
                 Dashboard
                     │
                     ▼
               Fluxos (Orquestrador)
                     │
    ┌────────────────┼─────────────────┐
    ▼                ▼                 ▼
 Organização   Catalogação      Integrações
                     │
                     ▼
             PostgreSQL / APIs
```

Essa separação reduz o acoplamento entre interface, regras de negócio e integrações externas.

---

# Responsabilidades

O módulo Fluxos possui as seguintes responsabilidades:

* iniciar e controlar o Workflow;
* validar pré-condições de execução;
* coordenar a sequência das etapas;
* acompanhar o progresso do processamento;
* consolidar resultados;
* registrar eventos relevantes;
* atualizar o Dashboard ao término da execução.

Não é responsabilidade deste módulo:

* renderizar componentes visuais;
* implementar acesso direto às APIs externas;
* persistir dados diretamente no banco sem utilização da camada apropriada;
* executar lógica exclusiva de apresentação.

---

# Objetivos de Engenharia

A implementação deve atender aos seguintes objetivos:

## Confiabilidade

O Workflow deve produzir resultados consistentes mesmo diante de falhas parciais.

---

## Idempotência

Sempre que possível, uma etapa poderá ser executada novamente sem produzir efeitos colaterais ou registros duplicados.

---

## Baixo Acoplamento

Cada etapa deve depender apenas de contratos públicos das camadas inferiores.

Mudanças em uma integração não devem exigir alterações nas demais etapas.

---

## Observabilidade

Todo processamento deve ser rastreável por meio de logs, métricas e estados de execução.

---

## Escalabilidade

O módulo deve suportar crescimento da biblioteca sem alterações estruturais significativas.

---

# Escopo Técnico

O Workflow compreende cinco etapas principais.

```text
Organizar Biblioteca

↓

Catalogar Obras

↓

Resolver IDs

↓

Atualizar Metadados

↓

Sincronizar Notion
```

Cada etapa representa uma unidade lógica independente, porém coordenada pelo mesmo orquestrador.

---

# Componentes Envolvidos

O módulo interage com os seguintes componentes da aplicação.

| Componente            | Responsabilidade                  |
| --------------------- | --------------------------------- |
| Workflow Controller   | Receber solicitações da interface |
| Workflow Orchestrator | Coordenar a execução das etapas   |
| Services              | Implementar regras de negócio     |
| Repositories          | Persistência de dados             |
| PostgreSQL            | Armazenamento principal           |
| MangaUpdates Client   | Consulta de IDs e metadados       |
| Notion Client         | Sincronização externa             |

Cada componente possui responsabilidade única e interfaces bem definidas.

---

# Fluxo de Alto Nível

```text
Interface Web

↓

Workflow Controller

↓

Workflow Orchestrator

↓

Services

↓

Repositories / APIs Externas

↓

Atualização do Estado

↓

Resposta para Interface
```

O controlador atua apenas como ponto de entrada. Toda coordenação pertence ao Orchestrator.

---

# Modelo de Execução

O Workflow deve ser tratado como uma execução única composta por múltiplas etapas.

Cada etapa segue o ciclo:

```text
Validar

↓

Executar

↓

Persistir

↓

Registrar

↓

Concluir
```

Somente após a conclusão de uma etapa a seguinte poderá ser iniciada.

---

# Dependências Externas

O módulo depende dos seguintes serviços.

| Serviço      | Obrigatório | Utilização                   |
| ------------ | ----------- | ---------------------------- |
| PostgreSQL   | Sim         | Todas as etapas              |
| Biblioteca   | Sim         | Organização e Catalogação    |
| MangaUpdates | Parcial     | Resolução de IDs e Metadados |
| Notion       | Parcial     | Sincronização                |

As integrações devem ser acessadas exclusivamente por componentes especializados.

---

# Princípios Arquiteturais

A implementação do módulo deve seguir:

* separação de responsabilidades;
* composição em vez de acoplamento;
* inversão de dependências;
* tratamento explícito de erros;
* operações idempotentes;
* processamento incremental;
* registro de eventos relevantes.

Esses princípios orientam toda a evolução do módulo.

---

# Requisitos Não Funcionais

O módulo deve atender aos seguintes requisitos:

| Requisito        | Objetivo                                         |
| ---------------- | ------------------------------------------------ |
| Confiabilidade   | Evitar inconsistências entre etapas              |
| Disponibilidade  | Permitir reexecuções seguras                     |
| Manutenibilidade | Facilitar evolução do Workflow                   |
| Observabilidade  | Registrar métricas e logs                        |
| Performance      | Processar grandes bibliotecas de forma eficiente |

---

# Relação com os Demais Documentos

Este documento serve como ponto de entrada para a documentação técnica.

A sequência recomendada é:

1. Visão Geral;
2. Arquitetura;
3. API e Contratos;
4. Processamento;
5. Integrações;
6. Performance e Tratamento de Erros;
7. Testes;
8. Checklists.

Cada documento aprofunda um aspecto específico da implementação.

---

# Conclusão

O módulo **Fluxos** é o núcleo operacional da Manhwateca. Sua função é coordenar, de forma consistente e resiliente, todas as etapas necessárias para transformar a biblioteca local em um catálogo atualizado e sincronizado. A arquitetura proposta privilegia separação de responsabilidades, baixo acoplamento e alta observabilidade, criando uma base sólida para a evolução contínua do sistema.
