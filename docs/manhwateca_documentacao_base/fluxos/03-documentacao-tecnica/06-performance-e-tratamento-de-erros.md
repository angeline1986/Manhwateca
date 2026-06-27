# Performance e Tratamento de Erros

> Documento: **06-performance-e-tratamento-de-erros.md**

---

# Objetivo

Este documento estabelece os requisitos técnicos de desempenho, resiliência e recuperação de falhas do módulo **Fluxos**.

Seu objetivo é garantir que o Workflow permaneça previsível, observável e robusto, mesmo durante o processamento de bibliotecas extensas ou diante da indisponibilidade de integrações externas.

As diretrizes aqui descritas devem orientar tanto a implementação quanto a evolução futura do módulo.

---

# Objetivos de Performance

A implementação deve priorizar:

* tempo de resposta consistente;
* baixo consumo de memória;
* processamento incremental;
* operações idempotentes;
* escalabilidade linear conforme o crescimento da biblioteca.

O desempenho não deve comprometer a confiabilidade do processamento.

---

# Metas de Desempenho

| Métrica                          | Objetivo         |
| -------------------------------- | ---------------- |
| Início do Workflow               | < 2 s            |
| Atualização do progresso         | ≤ 1 s            |
| Atualização da interface         | ≤ 500 ms         |
| Consulta ao banco                | < 100 ms (média) |
| Escrita no banco                 | < 200 ms (média) |
| Tempo de resposta da API interna | < 300 ms         |

Esses valores servem como referência para monitoramento e otimização.

---

# Processamento em Lotes

Sempre que possível, operações repetitivas devem ser agrupadas.

Exemplos:

* inserção de registros;
* atualização de metadados;
* sincronização com o Notion.

Evitar processamento individual quando operações em lote forem suportadas.

---

# Persistência Incremental

Os resultados não devem permanecer apenas em memória.

Durante a execução:

* persistir estados intermediários;
* atualizar progresso periodicamente;
* registrar alterações confirmadas.

Essa estratégia reduz perdas em caso de interrupção inesperada.

---

# Consumo de Memória

O Workflow deve evitar carregar toda a biblioteca simultaneamente.

Recomendações:

* iterar sobre coleções;
* utilizar paginação quando aplicável;
* liberar estruturas temporárias ao final de cada etapa;
* evitar duplicação desnecessária de objetos.

---

# Controle de Concorrência

O módulo deve impedir execuções concorrentes do Workflow.

Entretanto, operações internas poderão utilizar paralelismo controlado para melhorar o desempenho.

Diretrizes:

* isolamento entre obras;
* sincronização apenas na persistência;
* ausência de compartilhamento mutável entre tarefas.

---

# Timeout

Toda comunicação com serviços externos deve possuir timeout configurado.

| Serviço      | Timeout sugerido |
| ------------ | ---------------- |
| PostgreSQL   | 5 s              |
| MangaUpdates | 15 s             |
| Notion       | 20 s             |
| Biblioteca   | 10 s             |

Nenhuma operação deve aguardar indefinidamente.

---

# Retry

Falhas temporárias devem utilizar política limitada de repetição.

Estratégia recomendada:

```text id="0pgp7i"
Tentativa 1

↓

Aguardar

↓

Tentativa 2

↓

Aguardar

↓

Tentativa 3

↓

Registrar falha
```

Após o número máximo de tentativas, a etapa deve registrar o erro e seguir conforme as regras de negócio.

---

# Circuit Breaker

Quando um serviço externo apresentar falhas consecutivas, recomenda-se interromper temporariamente novas chamadas.

Fluxo sugerido:

```text id="r3sj0v"
Falhas sucessivas

↓

Abrir Circuit Breaker

↓

Interromper chamadas

↓

Aguardar período de recuperação

↓

Testar disponibilidade

↓

Fechar Circuit Breaker
```

Essa estratégia evita sobrecarga em serviços degradados.

---

# Classificação de Erros

Os erros devem ser classificados conforme sua natureza.

| Categoria    | Exemplos                     | Tratamento                               |
| ------------ | ---------------------------- | ---------------------------------------- |
| Validação    | Dados obrigatórios ausentes  | Corrigir entrada                         |
| Integração   | Timeout, indisponibilidade   | Retry ou reprocessamento                 |
| Persistência | Falha no banco               | Interromper etapa                        |
| Configuração | Token inválido               | Solicitar intervenção                    |
| Lógica       | Violação de regra de negócio | Registrar e interromper operação afetada |

Essa classificação facilita monitoramento e suporte.

---

# Recuperação

Após uma falha recuperável, o sistema deve:

1. preservar alterações persistidas;
2. registrar o ponto de interrupção;
3. informar o usuário;
4. permitir reprocessamento da etapa.

Não é necessário reiniciar todo o Workflow.

---

# Observabilidade

Todas as etapas devem produzir informações para monitoramento.

Registrar:

* início e fim da etapa;
* duração;
* quantidade processada;
* erros;
* alertas;
* integrações utilizadas.

Essas métricas permitem identificar gargalos e tendências de desempenho.

---

# Logs Estruturados

Cada evento relevante deve incluir, no mínimo:

```text id="3g5r2n"
executionId
stage
operation
status
duration
processed
errorCode
timestamp
```

Logs devem ser estruturados para facilitar consulta e integração com ferramentas de observabilidade.

---

# Monitoramento

O módulo deve disponibilizar indicadores como:

* Workflows executados;
* tempo médio por etapa;
* taxa de sucesso;
* taxa de falhas;
* tempo médio das integrações;
* quantidade de reprocessamentos.

Esses indicadores apoiam a evolução contínua do sistema.

---

# Degradação Controlada

Quando uma integração estiver indisponível:

* limitar o impacto à etapa dependente;
* preservar resultados anteriores;
* registrar pendências;
* permitir retomada posterior.

A indisponibilidade de um serviço externo não deve comprometer etapas independentes.

---

# Requisitos de Escalabilidade

A arquitetura deve suportar:

* crescimento do número de obras;
* aumento da frequência de execuções;
* inclusão de novas integrações;
* novas etapas do Workflow.

A expansão do sistema não deve exigir mudanças estruturais na arquitetura existente.

---

# Relação com os Demais Documentos

| Documento           | Complementa                            |
| ------------------- | -------------------------------------- |
| 02-arquitetura.md   | Organização dos componentes            |
| 04-processamento.md | Pipeline interno                       |
| 05-integracoes.md   | Estratégias específicas por integração |
| 07-testes.md        | Validação de desempenho e resiliência  |
| 08-checklists.md    | Critérios de revisão e implantação     |

---

# Conclusão

Os requisitos de **performance e tratamento de erros** do módulo **Fluxos** visam garantir que o Workflow permaneça eficiente, resiliente e previsível, mesmo diante de grandes volumes de dados e falhas em serviços externos. A combinação de persistência incremental, políticas de timeout, retry, circuit breaker, observabilidade e degradação controlada proporciona uma base sólida para uma operação confiável e para a evolução contínua da Manhwateca.
