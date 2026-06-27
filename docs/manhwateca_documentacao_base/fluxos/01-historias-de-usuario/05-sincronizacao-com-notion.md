# Sincronização com Notion

> Documento: **05-sincronizacao-com-notion.md**

---

# Objetivo

A etapa de **Sincronização com Notion** é responsável por refletir, no banco de dados do Notion, o estado atual da biblioteca da Manhwateca.

Após a atualização dos metadados, todas as informações necessárias já estão consolidadas no banco PostgreSQL. Esta etapa compara os registros locais com os existentes no Notion, identifica diferenças e executa apenas as operações necessárias para manter ambas as bases sincronizadas.

Seu objetivo é garantir que o Notion represente fielmente o estado da biblioteca local, evitando duplicidades, perdas de informação e atualizações desnecessárias.

---

# Escopo

Esta etapa contempla:

* conexão com a API do Notion;
* identificação de registros existentes;
* criação de novas páginas;
* atualização de páginas existentes;
* sincronização de propriedades;
* atualização do status de sincronização;
* registro de falhas e inconsistências.

Não contempla:

* organização da biblioteca;
* resolução de IDs;
* atualização de metadados no MangaUpdates.

---

# US-021 — Sincronizar automaticamente a biblioteca

## História

**Como** usuário

**Quero** que minhas obras sejam sincronizadas automaticamente com o Notion

**Para que** meu painel no Notion permaneça atualizado sem necessidade de edição manual.

---

## Critérios de Aceite

* Processar todas as obras elegíveis.
* Atualizar apenas registros alterados.
* Criar registros inexistentes.
* Registrar o resultado da sincronização.

---

## Regras de Negócio

RN-033

A sincronização deve utilizar o identificador da página do Notion (`notion_page_id`) quando existente.

RN-034

A ausência do `notion_page_id` indica que a obra ainda não foi criada no Notion.

---

# US-022 — Criar novas páginas no Notion

## História

**Como** sistema

**Quero** criar automaticamente páginas para novas obras

**Para que** toda a biblioteca esteja representada no Notion.

---

## Critérios de Aceite

* Criar apenas obras inexistentes.
* Armazenar o `notion_page_id` retornado pela API.
* Atualizar o banco local após a criação.

---

## Regras de Negócio

RN-035

Cada obra deve possuir apenas uma página correspondente no Notion.

RN-036

A criação nunca deve ocorrer quando já existir um `notion_page_id` válido.

---

# US-023 — Atualizar páginas existentes

## História

**Como** usuário

**Quero** que alterações realizadas na Manhwateca sejam refletidas no Notion

**Para que** ambas as bases permaneçam sincronizadas.

---

## Critérios de Aceite

Atualizar propriedades como:

* título;
* status;
* progresso da leitura;
* quantidade de capítulos;
* avaliação;
* gêneros;
* autores;
* data da última atualização.

---

## Regras de Negócio

RN-037

Somente propriedades alteradas devem ser enviadas para a API do Notion.

---

# US-024 — Tratar falhas de sincronização

## História

**Como** usuário

**Quero** ser informado quando uma sincronização falhar

**Para que** eu possa tomar ações corretivas.

---

## Critérios de Aceite

* Registrar erro.
* Informar qual obra falhou.
* Permitir nova sincronização posteriormente.
* Continuar sincronizando as demais obras.

---

## Regras de Negócio

RN-038

Uma falha em uma obra nunca deverá interromper a sincronização das demais.

RN-039

Toda falha deve ser registrada para auditoria.

---

# US-025 — Finalizar a sincronização

## História

**Como** sistema

**Quero** consolidar o resultado da sincronização

**Para que** o Workflow possa ser encerrado corretamente.

---

## Critérios de Aceite

Ao término da etapa, o sistema deverá informar:

* quantidade de obras processadas;
* páginas criadas;
* páginas atualizadas;
* páginas ignoradas;
* falhas encontradas;
* tempo total de execução.

---

## Regras de Negócio

RN-040

O resumo da sincronização deve permanecer disponível até a próxima execução do Workflow.

---

# Fluxo Principal

```text
Usuário inicia Sincronização

↓

Sistema identifica obras elegíveis

↓

Conecta à API do Notion

↓

Existe notion_page_id?

├── Sim
│
▼
Atualizar página

└── Não
     │
     ▼
Criar nova página

↓

Registrar resultado

↓

Atualizar banco local

↓

Gerar resumo da sincronização

↓

Etapa concluída
```

---

# Fluxos Alternativos

## Nenhuma obra pendente

Resultado esperado:

* informar que não existem alterações;
* concluir imediatamente.

---

## API do Notion indisponível

Resultado esperado:

* registrar erro;
* interromper apenas as operações afetadas;
* permitir nova tentativa.

---

## Página removida do Notion

Resultado esperado:

* invalidar o `notion_page_id`;
* marcar a obra para recriação na próxima sincronização.

---

# Exceções

| Código   | Situação                       |
| -------- | ------------------------------ |
| FLUX-017 | API do Notion indisponível     |
| FLUX-018 | Banco do Notion não encontrado |
| FLUX-019 | Página inexistente             |
| FLUX-020 | Falha ao criar página          |
| FLUX-021 | Falha ao atualizar página      |
| FLUX-022 | Limite de requisições excedido |

---

# Dependências

Esta etapa depende de:

* Atualização de Metadados concluída;
* PostgreSQL operacional;
* integração configurada com o Notion.

---

# Impactos nos demais módulos

Após a conclusão desta etapa:

* o Dashboard atualizará o estado das integrações;
* o indicador de sincronizações pendentes será recalculado;
* o banco do Notion refletirá o estado atual da biblioteca;
* o Workflow poderá ser encerrado.

---

# Prioridade

**Muito Alta**

A sincronização com o Notion representa a etapa final de integração externa da Manhwateca e garante que a base utilizada pelo usuário permaneça consistente com os dados processados localmente.

---

# Rastreabilidade

| Próximo documento       | Relação                      |
| ----------------------- | ---------------------------- |
| Especificação Funcional | 05-integracoes.md            |
| Documentação Técnica    | 05-integracoes.md            |
| Manual do Usuário       | 07-sincronizar-com-notion.md |

---

# Conclusão

A etapa de **Sincronização com Notion** consolida todo o processamento realizado pela Manhwateca, refletindo automaticamente no Notion as informações produzidas durante o Workflow. Ao criar, atualizar e validar registros de forma incremental e resiliente, ela garante consistência entre a base local e a base utilizada pelo usuário para gerenciamento diário de sua biblioteca.
