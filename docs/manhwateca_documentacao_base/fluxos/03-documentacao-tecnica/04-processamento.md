# Processamento

> Documento: **04-processamento.md**

---

# Objetivo

Este documento descreve o fluxo interno de processamento do módulo **Fluxos**, detalhando como o Workflow é executado desde a solicitação inicial até sua conclusão.

Enquanto o documento **Arquitetura** apresenta a organização dos componentes, este documento detalha **como esses componentes interagem durante uma execução**, incluindo validações, persistência, tratamento de concorrência, publicação de progresso e recuperação de falhas.

---

# Visão Geral

O Workflow é composto por cinco etapas executadas de forma sequencial.

Cada etapa segue exatamente o mesmo ciclo operacional.

```text
Solicitação

↓

Validação

↓

Preparação

↓

Processamento

↓

Persistência

↓

Atualização do Estado

↓

Finalização
```

Essa padronização simplifica manutenção, testes e inclusão de novas etapas.

---

# Pipeline Geral

```text
WorkflowController

↓

WorkflowOrchestrator

↓

Validar Ambiente

↓

Executar Etapa 1

↓

Persistir

↓

Executar Etapa 2

↓

Persistir

↓

Executar Etapa 3

↓

Persistir

↓

Executar Etapa 4

↓

Persistir

↓

Executar Etapa 5

↓

Persistir

↓

Encerrar Workflow
```

O Orchestrator controla exclusivamente a ordem das etapas.

---

# Inicialização

Ao receber uma solicitação de execução:

1. verificar se já existe um Workflow ativo;
2. validar dependências obrigatórias;
3. criar um identificador único da execução;
4. registrar horário de início;
5. inicializar o estado global do Workflow.

Exemplo de estrutura interna:

```json
{
  "executionId": "wf_20260627_001",
  "status": "running",
  "currentStage": "organization",
  "startedAt": "2026-06-27T01:40:00Z"
}
```

---

# Ciclo de Execução das Etapas

Cada etapa deve implementar o mesmo ciclo de vida.

```text
validate()

↓

prepare()

↓

execute()

↓

persist()

↓

finalize()
```

## validate()

Responsável por verificar:

* pré-requisitos;
* disponibilidade das integrações;
* elegibilidade da etapa.

Nenhuma alteração deve ser realizada nesta fase.

---

## prepare()

Responsável por:

* carregar dados necessários;
* inicializar estruturas temporárias;
* abrir contexto de execução;
* preparar métricas.

---

## execute()

Executa efetivamente o processamento.

Exemplos:

* organizar biblioteca;
* catalogar obras;
* resolver IDs;
* atualizar metadados;
* sincronizar Notion.

Esta é a fase de maior duração do Workflow.

---

## persist()

Responsável por:

* salvar alterações;
* registrar progresso;
* atualizar indicadores;
* registrar histórico.

Persistências devem ocorrer em lotes sempre que possível.

---

## finalize()

Responsável por:

* liberar recursos;
* consolidar estatísticas;
* atualizar estado da etapa;
* preparar transição para a próxima etapa.

---

# Processamento por Obra

Dentro de uma etapa, cada obra segue um fluxo independente.

```text
Selecionar Obra

↓

Validar Elegibilidade

↓

Processar

↓

Persistir Resultado

↓

Registrar Métricas
```

Falhas em uma obra não devem interromper o processamento das demais.

---

# Controle de Concorrência

O módulo deve permitir apenas **uma execução global do Workflow por vez**.

Antes de iniciar uma nova execução:

* verificar existência de execução ativa;
* bloquear novas execuções concorrentes;
* retornar erro apropriado quando necessário.

Entretanto, dentro de uma etapa, o processamento poderá utilizar paralelismo controlado para aumentar o desempenho, desde que:

* cada obra seja processada de forma independente;
* não ocorram conflitos de escrita;
* os resultados sejam persistidos de maneira consistente.

---

# Persistência

A persistência deve ocorrer em diferentes níveis.

## Estado do Workflow

Atualizado sempre que uma etapa iniciar ou terminar.

---

## Estado da Etapa

Atualizado durante o processamento.

Campos típicos:

* status;
* progresso;
* quantidade processada;
* duração.

---

## Dados das Obras

Persistidos conforme cada operação for concluída.

A persistência incremental reduz perdas em caso de interrupção.

---

# Atualização de Progresso

Durante a execução, o Orchestrator deve publicar eventos de progresso.

Exemplo:

```json
{
  "stage": "metadata",
  "processed": 382,
  "total": 684,
  "progress": 56
}
```

A interface poderá consumir essas informações periodicamente ou por mecanismo de atualização em tempo real.

---

# Recuperação após Falhas

Caso uma etapa seja interrompida:

1. preservar alterações já persistidas;
2. registrar o ponto de interrupção;
3. atualizar o estado da execução;
4. permitir reprocessamento posterior.

Nenhuma etapa anterior deve ser reexecutada automaticamente.

---

# Cancelamento

Ao solicitar cancelamento:

```text
Receber solicitação

↓

Marcar execução como "cancelling"

↓

Concluir operação corrente

↓

Persistir alterações

↓

Liberar recursos

↓

Atualizar estado para "cancelled"
```

O cancelamento deve ocorrer de forma cooperativa, evitando interromper operações críticas no meio da execução.

---

# Registro de Eventos

Cada execução deve produzir eventos relevantes para auditoria e monitoramento.

Exemplos:

* Workflow iniciado;
* etapa iniciada;
* etapa concluída;
* erro de integração;
* cancelamento solicitado;
* Workflow finalizado.

Esses eventos podem ser utilizados para logs, métricas e histórico.

---

# Estratégia de Reprocessamento

Uma etapa poderá ser reexecutada quando:

* falhar;
* houver novas obras elegíveis;
* uma integração voltar a ficar disponível;
* o usuário solicitar atualização.

O reprocessamento deve limitar-se à etapa selecionada e às suas operações internas.

---

# Sequência de Finalização

Após a conclusão da última etapa:

1. consolidar métricas;
2. registrar duração total;
3. atualizar estado do Workflow;
4. atualizar indicadores do Dashboard;
5. disponibilizar resumo da execução.

---

# Considerações de Implementação

Durante a implementação, recomenda-se que:

* operações longas sejam desacopladas da camada HTTP;
* serviços sejam idempotentes sempre que possível;
* persistências sejam realizadas em transações curtas;
* integrações externas possuam timeout e política de retry;
* logs sejam estruturados por `executionId`.

---

# Relação com os Demais Documentos

| Documento                               | Complementa                             |
| --------------------------------------- | --------------------------------------- |
| 02-arquitetura.md                       | Organização dos componentes             |
| 03-api-e-contratos.md                   | Endpoints que iniciam o processamento   |
| 05-integracoes.md                       | Comunicação com serviços externos       |
| 06-performance-e-tratamento-de-erros.md | Estratégias de otimização e resiliência |
| 07-testes.md                            | Validação do pipeline de processamento  |

---

# Conclusão

O processamento do módulo **Fluxos** é estruturado como um pipeline sequencial e resiliente, coordenado pelo **Workflow Orchestrator**. A padronização do ciclo de vida das etapas, a persistência incremental, o controle de concorrência e a recuperação segura após falhas garantem que o Workflow possa operar sobre grandes bibliotecas com previsibilidade, consistência e facilidade de manutenção.
