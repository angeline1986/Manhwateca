# Resolução de IDs

> Documento: **03-resolucao-de-ids.md**

---

# Objetivo

A etapa de **Resolução de IDs** é responsável por associar cada obra catalogada ao seu identificador oficial no **MangaUpdates**.

O identificador (`mangaupdates_id`) é a principal chave de integração da Manhwateca com serviços externos e permite que as próximas etapas do Workflow obtenham metadados, acompanhem novos capítulos e sincronizem informações com o Notion.

Esta etapa representa o elo entre a biblioteca local e as fontes oficiais de dados.

---

# Escopo

Esta etapa contempla:

* localizar possíveis correspondências no MangaUpdates;
* validar resultados encontrados;
* associar o identificador oficial à obra;
* tratar ambiguidades;
* permitir confirmação manual quando necessário;
* registrar obras não localizadas.

Não contempla:

* download de metadados;
* sincronização com Notion;
* atualização de capítulos.

---

# US-011 — Localizar automaticamente o ID da obra

## História

**Como** usuário

**Quero** que o sistema pesquise automaticamente o MangaUpdates

**Para que** minhas obras sejam identificadas sem necessidade de pesquisa manual.

---

## Critérios de Aceite

* Pesquisar utilizando o título principal da obra.
* Utilizar títulos alternativos quando disponíveis.
* Registrar todos os candidatos encontrados.
* Associar automaticamente quando houver uma única correspondência confiável.

---

## Regras de Negócio

RN-017

A pesquisa deve utilizar prioritariamente o título catalogado.

RN-018

Caso existam títulos alternativos cadastrados, eles poderão ser utilizados como consultas secundárias.

RN-019

Toda pesquisa deve registrar sua data de execução.

---

# US-012 — Resolver ambiguidades

## História

**Como** usuário

**Quero** escolher manualmente entre múltiplos resultados encontrados

**Para que** o identificador correto seja associado à obra.

---

## Critérios de Aceite

* Exibir todos os candidatos encontrados.
* Permitir comparação entre os resultados.
* Permitir selecionar apenas um ID.
* Confirmar a associação antes da gravação.

---

## Regras de Negócio

RN-020

Nunca selecionar automaticamente um candidato quando houver múltiplas correspondências equivalentes.

RN-021

A decisão manual prevalece sobre futuras pesquisas automáticas.

---

# US-013 — Registrar obras não localizadas

## História

**Como** usuário

**Quero** saber quais obras não foram encontradas

**Para que** eu possa realizar verificações posteriormente.

---

## Critérios de Aceite

* Registrar tentativa de pesquisa.
* Marcar a obra como "ID não encontrado".
* Permitir nova tentativa futuramente.

---

## Regras de Negócio

RN-022

Uma obra não localizada permanece elegível para novas pesquisas.

RN-023

A ausência de ID não impede a permanência da obra na biblioteca.

---

# US-014 — Confirmar associação do ID

## História

**Como** usuário

**Quero** confirmar o identificador encontrado

**Para que** futuras integrações utilizem informações corretas.

---

## Critérios de Aceite

* Persistir o `mangaupdates_id`.
* Registrar data da associação.
* Registrar origem da associação (automática ou manual).

---

## Regras de Negócio

RN-024

Após confirmado, o identificador passa a ser considerado a referência oficial da obra.

RN-025

Alterações futuras devem exigir confirmação explícita.

---

# US-015 — Preparar obras para atualização de metadados

## História

**Como** sistema

**Quero** identificar quais obras já possuem identificador válido

**Para que** apenas elas avancem para a etapa de atualização de metadados.

---

## Critérios de Aceite

* Selecionar apenas obras com `mangaupdates_id`.
* Atualizar a fila da próxima etapa.
* Informar quantidade de obras prontas.

---

## Regras de Negócio

RN-026

Obras sem identificador permanecem excluídas da atualização automática de metadados.

---

# Fluxo Principal

```text
Usuário inicia Resolução de IDs

↓

Sistema identifica obras pendentes

↓

Pesquisa MangaUpdates

↓

Analisa resultados

↓

Única correspondência?

├── Sim
│
▼
Associar automaticamente

└── Não
     │
     ▼
Solicitar confirmação do usuário

↓

Persistir mangaupdates_id

↓

Atualizar fila de Metadados

↓

Etapa concluída
```

---

# Fluxos Alternativos

## Nenhum resultado encontrado

Resultado esperado:

* registrar tentativa;
* marcar obra como "não localizada";
* permitir nova tentativa.

---

## Múltiplos candidatos

Resultado esperado:

* apresentar lista de candidatos;
* aguardar confirmação do usuário.

---

## Associação incorreta identificada

Resultado esperado:

* permitir substituição do ID;
* registrar alteração em histórico.

---

# Exceções

| Código   | Situação                         |
| -------- | -------------------------------- |
| FLUX-009 | MangaUpdates indisponível        |
| FLUX-010 | Nenhum candidato encontrado      |
| FLUX-011 | Múltiplos candidatos encontrados |
| FLUX-012 | Falha ao gravar identificador    |

---

# Dependências

Esta etapa depende de:

* Catalogação concluída;
* conectividade com MangaUpdates;
* PostgreSQL disponível.

Não depende de:

* Notion.

---

# Impactos nos demais módulos

Após a conclusão desta etapa:

* a Atualização de Metadados poderá ser executada;
* o Dashboard atualizará o indicador de obras sem ID;
* a Biblioteca exibirá o identificador oficial da obra;
* futuras sincronizações utilizarão o `mangaupdates_id` como chave principal.

---

# Prioridade

**Muito Alta**

A Resolução de IDs é a etapa que habilita todas as integrações externas da Manhwateca.

Sem um identificador oficial, não é possível obter metadados confiáveis nem sincronizar corretamente as informações.

---

# Rastreabilidade

| Próximo documento       | Relação                  |
| ----------------------- | ------------------------ |
| Especificação Funcional | 03-etapas-do-workflow.md |
| Documentação Técnica    | 05-integracoes.md        |
| Manual do Usuário       | 05-resolver-ids.md       |

---

# Conclusão

A etapa de **Resolução de IDs** estabelece a identidade oficial de cada obra dentro do ecossistema da Manhwateca. Ao associar o identificador do MangaUpdates de forma automática ou assistida, ela garante consistência entre a biblioteca local e as fontes externas, habilitando a atualização de metadados, o acompanhamento de capítulos e a sincronização com o Notion.
