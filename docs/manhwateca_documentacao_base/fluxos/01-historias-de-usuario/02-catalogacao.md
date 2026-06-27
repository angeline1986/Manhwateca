# Catalogação

> Documento: **02-catalogacao.md**

---

# Objetivo

A etapa de **Catalogação** é responsável por transformar as obras identificadas na biblioteca em registros estruturados dentro da Manhwateca.

Após a organização física dos arquivos, esta etapa identifica cada obra, atualiza ou cria seu registro interno e prepara as informações necessárias para as etapas de Resolução de IDs e Atualização de Metadados.

Seu objetivo é garantir que toda obra existente na biblioteca possua um cadastro consistente no banco de dados.

---

# Escopo

Esta etapa contempla:

* identificação de obras;
* criação de registros internos;
* atualização de registros existentes;
* detecção de duplicidades;
* associação entre diretório físico e cadastro;
* preparação para resolução de IDs.

Não contempla:

* busca no MangaUpdates;
* obtenção de metadados;
* sincronização com Notion.

---

# US-006 — Catalogar novas obras

## História

**Como** usuário

**Quero** que as novas obras encontradas sejam catalogadas automaticamente

**Para que** passem a fazer parte da biblioteca gerenciada pela Manhwateca.

---

## Critérios de Aceite

* Toda nova obra encontrada deve gerar um registro no banco.
* Obras já catalogadas não devem ser duplicadas.
* O sistema deve registrar a data da catalogação.
* A catalogação deve ocorrer sem intervenção manual sempre que possível.

---

## Regras de Negócio

RN-010

Uma obra somente poderá ser catalogada após a etapa de Organização da Biblioteca.

RN-011

Cada obra deve possuir um identificador interno único.

RN-012

O diretório físico da obra deve permanecer associado ao registro catalogado.

---

# US-007 — Atualizar obras existentes

## História

**Como** usuário

**Quero** que obras já catalogadas sejam atualizadas quando sofrerem alterações

**Para que** o banco permaneça consistente com a biblioteca.

---

## Critérios de Aceite

* Atualizar caminho da obra quando necessário.
* Atualizar quantidade de capítulos detectados.
* Atualizar data da última catalogação.
* Preservar histórico da obra.

---

## Regras de Negócio

RN-013

A atualização nunca deverá apagar informações já enriquecidas manualmente pelo usuário.

---

# US-008 — Detectar obras duplicadas

## História

**Como** usuário

**Quero** ser informado quando houver possíveis obras duplicadas

**Para que** eu possa corrigir inconsistências antes das próximas etapas.

---

## Critérios de Aceite

* Detectar registros com mesmo nome.
* Detectar múltiplos diretórios associados à mesma obra.
* Registrar alerta de possível duplicidade.
* Não remover automaticamente registros.

---

## Regras de Negócio

RN-014

A confirmação de duplicidade depende de validação do usuário.

---

# US-009 — Validar cadastro da obra

## História

**Como** sistema

**Quero** validar os dados mínimos de cada obra

**Para que** apenas registros consistentes avancem para a Resolução de IDs.

---

## Critérios de Aceite

Cada obra deve possuir, no mínimo:

* título identificado;
* diretório válido;
* identificador interno;
* status de catalogação.

---

## Regras de Negócio

RN-015

Obras incompletas permanecem catalogadas, porém sinalizadas como pendentes.

---

# US-010 — Preparar obras para Resolução de IDs

## História

**Como** sistema

**Quero** identificar quais obras ainda não possuem identificação externa

**Para que** elas sejam processadas na próxima etapa do Workflow.

---

## Critérios de Aceite

* Identificar obras sem MangaUpdates ID.
* Atualizar fila de processamento.
* Informar quantidade de obras pendentes.

---

## Regras de Negócio

RN-016

Toda obra sem identificador externo deve permanecer elegível para a etapa de Resolução de IDs.

---

# Fluxo Principal

```text
Usuário inicia Catalogação

↓

Sistema consulta índice da biblioteca

↓

Localiza obras não catalogadas

↓

Cria novos registros

↓

Atualiza registros existentes

↓

Valida consistência

↓

Identifica pendências

↓

Atualiza fila da Resolução de IDs

↓

Etapa concluída
```

---

# Fluxos Alternativos

## Nenhuma obra nova

Resultado esperado:

* atualizar registros existentes;
* concluir a etapa normalmente.

---

## Obras parcialmente cadastradas

Resultado esperado:

* completar as informações disponíveis;
* registrar pendências quando necessário.

---

## Possível duplicidade

Resultado esperado:

* registrar alerta;
* manter ambos os registros;
* aguardar decisão do usuário.

---

# Exceções

| Código   | Situação                        |
| -------- | ------------------------------- |
| FLUX-005 | Falha ao criar registro da obra |
| FLUX-006 | Duplicidade detectada           |
| FLUX-007 | Dados mínimos insuficientes     |
| FLUX-008 | Falha de persistência no banco  |

---

# Dependências

Esta etapa depende de:

* Organização da Biblioteca concluída;
* PostgreSQL disponível.

Não depende de:

* MangaUpdates;
* Notion.

---

# Impactos nos demais módulos

Após a conclusão desta etapa:

* novas obras passam a aparecer na Biblioteca;
* o Dashboard atualiza os indicadores de catalogação;
* a etapa de Resolução de IDs poderá processar apenas obras elegíveis;
* relatórios passam a considerar os novos registros.

---

# Prioridade

**Alta**

A Catalogação estabelece a representação lógica da biblioteca dentro da Manhwateca e serve como base para todas as integrações externas.

---

# Rastreabilidade

| Próximo documento       | Relação                  |
| ----------------------- | ------------------------ |
| Especificação Funcional | 03-etapas-do-workflow.md |
| Documentação Técnica    | 04-processamento.md      |
| Manual do Usuário       | 04-catalogar-obras.md    |

---

# Conclusão

A etapa de **Catalogação** transforma a estrutura física identificada na biblioteca em registros persistidos e consistentes no banco de dados da Manhwateca. Ao consolidar o cadastro das obras, detectar inconsistências e preparar os registros para a Resolução de IDs, ela estabelece a ponte entre a organização local dos arquivos e o enriquecimento dos dados por meio das integrações externas.
