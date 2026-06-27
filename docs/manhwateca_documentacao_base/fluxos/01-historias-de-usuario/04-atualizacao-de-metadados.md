# Atualização de Metadados

> Documento: **04-atualizacao-de-metadados.md**

---

# Objetivo

A etapa de **Atualização de Metadados** é responsável por enriquecer automaticamente as obras catalogadas utilizando informações provenientes do **MangaUpdates**.

Após a associação do identificador oficial (`mangaupdates_id`), o sistema consulta a API do MangaUpdates para obter informações atualizadas da obra e persisti-las no banco de dados da Manhwateca.

O objetivo desta etapa é manter a biblioteca consistente, atualizada e preparada para sincronização com o Notion.

---

# Escopo

Esta etapa contempla:

* consulta ao MangaUpdates;
* atualização dos metadados da obra;
* atualização do status de publicação;
* atualização da quantidade de capítulos;
* atualização de títulos alternativos;
* atualização de gêneros, autores e artistas;
* atualização da data da última sincronização.

Não contempla:

* resolução de IDs;
* sincronização com Notion;
* alterações manuais realizadas pelo usuário.

---

# US-016 — Atualizar automaticamente os metadados

## História

**Como** usuário

**Quero** que a Manhwateca atualize automaticamente os dados das minhas obras

**Para que** minha biblioteca permaneça sempre sincronizada com as informações mais recentes disponíveis no MangaUpdates.

---

## Critérios de Aceite

* Atualizar todas as obras elegíveis.
* Consultar apenas obras com `mangaupdates_id`.
* Persistir somente informações válidas.
* Registrar a data da última atualização.

---

## Regras de Negócio

RN-027

Somente obras com identificador válido poderão ser processadas.

RN-028

Cada obra deve ser atualizada independentemente das demais.

---

# US-017 — Atualizar apenas obras elegíveis

## História

**Como** sistema

**Quero** ignorar obras que não possam ser atualizadas

**Para que** recursos não sejam desperdiçados com consultas desnecessárias.

---

## Critérios de Aceite

Não processar obras:

* sem MangaUpdates ID;
* desabilitadas pelo usuário;
* marcadas como arquivadas (quando aplicável).

---

## Regras de Negócio

RN-029

A elegibilidade deve ser avaliada antes de qualquer chamada à API.

---

# US-018 — Preservar informações locais

## História

**Como** usuário

**Quero** que informações personalizadas permaneçam intactas

**Para que** atualizações automáticas não sobrescrevam dados definidos manualmente.

---

## Critérios de Aceite

O sistema não deverá substituir:

* notas pessoais;
* avaliação;
* status de leitura;
* tags locais;
* propriedades exclusivas da Manhwateca.

---

## Regras de Negócio

RN-030

Somente campos provenientes do MangaUpdates poderão ser atualizados automaticamente.

---

# US-019 — Registrar histórico de atualização

## História

**Como** usuário

**Quero** saber quando uma obra foi atualizada

**Para que** eu possa acompanhar a frequência de sincronização.

---

## Critérios de Aceite

Registrar:

* data da atualização;
* duração da operação;
* resultado da atualização;
* origem dos dados.

---

## Regras de Negócio

RN-031

Toda atualização deve produzir um registro de auditoria.

---

# US-020 — Preparar obras para sincronização com Notion

## História

**Como** sistema

**Quero** identificar quais obras foram atualizadas com sucesso

**Para que** elas sejam sincronizadas posteriormente com o Notion.

---

## Critérios de Aceite

* Marcar obras atualizadas.
* Atualizar fila de sincronização.
* Informar quantidade de obras prontas.

---

## Regras de Negócio

RN-032

Somente obras atualizadas com sucesso poderão ser consideradas prontas para sincronização.

---

# Fluxo Principal

```text
Usuário inicia Atualização de Metadados

↓

Sistema identifica obras elegíveis

↓

Consulta MangaUpdates

↓

Obtém metadados atualizados

↓

Atualiza banco de dados

↓

Registra histórico

↓

Atualiza fila do Notion

↓

Etapa concluída
```

---

# Fluxos Alternativos

## Obra sem MangaUpdates ID

Resultado esperado:

* ignorar obra;
* registrar motivo;
* continuar processamento.

---

## API temporariamente indisponível

Resultado esperado:

* registrar falha;
* manter dados atuais;
* permitir nova tentativa.

---

## Metadados inalterados

Resultado esperado:

* registrar atualização;
* manter dados existentes;
* concluir processamento normalmente.

---

# Exceções

| Código   | Situação                       |
| -------- | ------------------------------ |
| FLUX-013 | MangaUpdates indisponível      |
| FLUX-014 | Resposta inválida da API       |
| FLUX-015 | Falha ao persistir metadados   |
| FLUX-016 | Limite de requisições excedido |

---

# Dependências

Esta etapa depende de:

* Resolução de IDs concluída;
* MangaUpdates disponível;
* PostgreSQL operacional.

Não depende de:

* Notion.

---

# Impactos nos demais módulos

Após a conclusão desta etapa:

* a Biblioteca passa a exibir informações atualizadas da obra;
* o Dashboard atualiza indicadores relacionados ao Workflow;
* a sincronização com o Notion poderá utilizar os novos metadados;
* relatórios passam a refletir os dados mais recentes.

---

# Prioridade

**Muito Alta**

A atualização de metadados é responsável por manter a biblioteca alinhada com a fonte oficial de informações, reduzindo inconsistências e evitando manutenção manual.

---

# Rastreabilidade

| Próximo documento       | Relação                   |
| ----------------------- | ------------------------- |
| Especificação Funcional | 03-etapas-do-workflow.md  |
| Documentação Técnica    | 05-integracoes.md         |
| Manual do Usuário       | 06-atualizar-metadados.md |

---

# Conclusão

A etapa de **Atualização de Metadados** enriquece automaticamente as obras da Manhwateca utilizando informações oficiais do MangaUpdates. Ao preservar os dados personalizados do usuário e atualizar apenas os campos de origem externa, ela mantém a biblioteca consistente, atualizada e pronta para a sincronização com o Notion.
