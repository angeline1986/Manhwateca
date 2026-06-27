# Finalização do Workflow

> Documento: **06-finalizacao-do-workflow.md**

---

# Objetivo

A etapa de **Finalização do Workflow** consolida os resultados produzidos durante todas as etapas anteriores do módulo Fluxos.

Seu objetivo é validar a integridade do processamento executado, registrar métricas da execução, atualizar o estado global do Workflow e disponibilizar ao usuário um resumo completo da operação.

Esta etapa não executa novas transformações sobre a biblioteca. Sua responsabilidade é verificar se o Workflow foi concluído com sucesso, identificar pendências remanescentes e preparar o sistema para futuras execuções.

---

# Escopo

Esta etapa contempla:

* consolidação dos resultados do Workflow;
* validação da execução de todas as etapas;
* geração do resumo da execução;
* atualização do estado do Workflow;
* registro de métricas e auditoria;
* identificação de pendências remanescentes;
* atualização do Dashboard.

Não contempla:

* novas consultas ao MangaUpdates;
* sincronizações adicionais;
* alterações na biblioteca;
* processamento de obras.

---

# US-026 — Consolidar os resultados do Workflow

## História

**Como** usuário

**Quero** visualizar um resumo da execução do Workflow

**Para que** eu saiba exatamente o que foi realizado e quais ações ainda são necessárias.

---

## Critérios de Aceite

O sistema deve apresentar:

* quantidade de obras organizadas;
* quantidade de obras catalogadas;
* IDs resolvidos;
* metadados atualizados;
* sincronizações concluídas;
* pendências restantes;
* duração total da execução.

---

## Regras de Negócio

RN-041

O resumo deve representar exclusivamente a execução corrente.

RN-042

As informações exibidas devem ser derivadas dos resultados efetivamente processados.

---

# US-027 — Atualizar o estado do Workflow

## História

**Como** sistema

**Quero** atualizar o estado geral do Workflow

**Para que** os demais módulos conheçam o resultado da última execução.

---

## Critérios de Aceite

Registrar:

* data de início;
* data de término;
* duração;
* status final;
* etapa concluída;
* quantidade de erros;
* quantidade de alertas.

---

## Regras de Negócio

RN-043

O Workflow somente poderá ser considerado concluído quando todas as etapas obrigatórias tiverem sido executadas.

RN-044

Execuções parcialmente concluídas deverão permanecer registradas para auditoria.

---

# US-028 — Identificar pendências remanescentes

## História

**Como** usuário

**Quero** saber quais pendências permaneceram após o Workflow

**Para que** eu possa decidir se executarei uma nova rodada de processamento.

---

## Critérios de Aceite

Listar:

* obras sem ID;
* obras não sincronizadas;
* falhas de integração;
* inconsistências encontradas;
* etapas interrompidas.

---

## Regras de Negócio

RN-045

Pendências devem permanecer disponíveis até serem resolvidas.

---

# US-029 — Registrar histórico da execução

## História

**Como** usuário

**Quero** que cada execução seja registrada

**Para que** eu possa consultar posteriormente o histórico do processamento.

---

## Critérios de Aceite

Registrar:

* identificador da execução;
* usuário responsável (quando aplicável);
* horário de início;
* horário de término;
* duração;
* resultado;
* quantidade de erros;
* quantidade de alertas.

---

## Regras de Negócio

RN-046

Cada execução deve possuir um identificador único.

RN-047

Os registros históricos não devem ser alterados após sua conclusão.

---

# US-030 — Preparar o sistema para uma nova execução

## História

**Como** sistema

**Quero** finalizar corretamente todos os estados temporários

**Para que** uma nova execução possa ser iniciada sem inconsistências.

---

## Critérios de Aceite

* limpar filas temporárias;
* liberar recursos utilizados;
* finalizar tarefas pendentes;
* atualizar indicadores do Dashboard;
* manter apenas informações permanentes.

---

## Regras de Negócio

RN-048

Estados temporários não devem permanecer ativos após a conclusão do Workflow.

RN-049

A limpeza nunca deverá remover dados históricos.

---

# Fluxo Principal

```text
Usuário conclui a última etapa

↓

Sistema valida todas as etapas

↓

Consolida resultados

↓

Registra histórico

↓

Atualiza estado do Workflow

↓

Atualiza Dashboard

↓

Libera recursos temporários

↓

Workflow finalizado
```

---

# Fluxos Alternativos

## Workflow concluído com alertas

Resultado esperado:

* marcar execução como concluída;
* destacar pendências existentes;
* permitir nova execução posteriormente.

---

## Workflow interrompido

Resultado esperado:

* registrar etapa interrompida;
* preservar histórico parcial;
* permitir retomada em nova execução.

---

## Falhas de integração

Resultado esperado:

* registrar falhas;
* concluir etapas já executadas;
* informar necessidade de reprocessamento.

---

# Exceções

| Código   | Situação                             |
| -------- | ------------------------------------ |
| FLUX-023 | Workflow interrompido                |
| FLUX-024 | Falha ao registrar histórico         |
| FLUX-025 | Erro ao consolidar resultados        |
| FLUX-026 | Erro ao atualizar estado do Workflow |

---

# Dependências

Esta etapa depende da conclusão das seguintes etapas:

* Organização da Biblioteca;
* Catalogação;
* Resolução de IDs;
* Atualização de Metadados;
* Sincronização com Notion.

---

# Impactos nos demais módulos

Após a conclusão desta etapa:

* o Dashboard passa a refletir o estado atualizado do sistema;
* métricas operacionais são recalculadas;
* pendências críticas são atualizadas;
* uma nova execução do Workflow poderá ser iniciada;
* relatórios passam a utilizar os dados da última execução.

---

# Prioridade

**Alta**

Embora não realize processamento sobre as obras, esta etapa garante a consistência operacional da Manhwateca, fornece rastreabilidade das execuções e prepara o ambiente para novos ciclos do Workflow.

---

# Rastreabilidade

| Próximo documento       | Relação                     |
| ----------------------- | --------------------------- |
| Especificação Funcional | 03-etapas-do-workflow.md    |
| Documentação Técnica    | 04-processamento.md         |
| Manual do Usuário       | 08-acompanhar-o-workflow.md |

---

# Conclusão

A etapa de **Finalização do Workflow** encerra o ciclo operacional da Manhwateca de forma controlada e auditável. Ao consolidar resultados, registrar métricas, identificar pendências e atualizar o estado global do sistema, ela garante que o usuário tenha uma visão clara do processamento realizado e que a aplicação esteja preparada para futuras execuções, preservando consistência, rastreabilidade e confiabilidade.
