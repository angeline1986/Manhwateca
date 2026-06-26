# US-004 — Consultar pendências críticas

## Identificação

| Campo            | Valor                                                  |
| ---------------- | ------------------------------------------------------ |
| **ID**           | US-004                                                 |
| **Título**       | Consultar pendências críticas                          |
| **Módulo**       | Dashboard                                              |
| **Prioridade**   | Muito Alta                                             |
| **Tipo**         | Funcionalidade                                         |
| **Epic**         | Dashboard                                              |
| **Dependências** | Workflow, Biblioteca, PostgreSQL, MangaUpdates, Notion |

---

# Objetivo

Como **usuária da Manhwateca**,

quero **visualizar rapidamente todas as pendências que exigem minha intervenção**,

para que **eu consiga resolver os problemas que impedem ou impactam o fluxo de trabalho antes de executar novas tarefas**.

---

# Descrição

O Dashboard deve consolidar todas as pendências relevantes da aplicação em um único painel.

Uma pendência representa qualquer situação que exija uma decisão ou ação do usuário.

O objetivo não é listar todas as ocorrências do sistema, mas destacar apenas aquelas que afetam diretamente a continuidade do workflow ou a consistência da biblioteca.

Cada pendência deve informar:

* o problema identificado;
* sua prioridade;
* a quantidade de itens afetados;
* uma breve explicação;
* a ação recomendada.

O Dashboard deve limitar a quantidade de informações exibidas, incentivando o usuário a acessar a página **Fluxos** para resolver a pendência.

---

# Valor de Negócio

Sem uma visão centralizada das pendências, o usuário precisa navegar entre diferentes módulos para descobrir o que precisa ser resolvido.

Ao consolidar essas informações no Dashboard, a Manhwateca:

* reduz tempo de análise;
* evita esquecimentos;
* diminui erros operacionais;
* conduz o usuário naturalmente para a próxima atividade.

---

# Fluxo Principal

1. O usuário acessa o Dashboard.
2. O sistema identifica todas as pendências abertas.
3. As pendências são classificadas por prioridade.
4. O Dashboard exibe somente as pendências relevantes.
5. O usuário escolhe uma delas.
6. O sistema abre a página **Fluxos** posicionada na etapa correspondente.

---

# Fluxos Alternativos

### FA-01 — Nenhuma pendência encontrada

Caso não existam pendências abertas, o Dashboard deve apresentar:

> Nenhuma pendência encontrada.

O painel permanece visível para manter consistência visual.

---

### FA-02 — Existe uma pendência crítica

Caso exista um problema que impeça qualquer operação (por exemplo, PostgreSQL indisponível), apenas essa pendência deve ser destacada.

As demais permanecem ocultas até que o bloqueio seja resolvido.

---

### FA-03 — Existem múltiplas pendências

Quando houver diversas pendências simultaneamente, elas devem ser ordenadas automaticamente pela prioridade definida nas regras de negócio.

---

# Critérios de Aceite

| ID     | Critério                                                                                                |
| ------ | ------------------------------------------------------------------------------------------------------- |
| AC-001 | O Dashboard deve exibir apenas pendências que exijam intervenção do usuário.                            |
| AC-002 | Cada pendência deve possuir descrição, prioridade e ação recomendada.                                   |
| AC-003 | As pendências devem ser ordenadas automaticamente pela prioridade.                                      |
| AC-004 | Pendências resolvidas não devem permanecer visíveis.                                                    |
| AC-005 | Selecionar uma pendência deve direcionar o usuário para a etapa correspondente em **Fluxos**.           |
| AC-006 | O painel deve permanecer visível mesmo quando não houver pendências, exibindo uma mensagem informativa. |

---

# Componentes Relacionados

## Painel — Pendências Acionáveis

Lista resumida contendo as pendências abertas.

Cada item apresenta:

* ícone;
* título;
* descrição;
* prioridade;
* ação sugerida.

---

## Item de Pendência

Cada item representa um único tipo de problema.

Exemplo:

```text
8 obras sem ID

Resolver antes de atualizar metadados.

[Abrir Fluxos]
```

---

## Estado vazio

Quando não existirem pendências:

```text
✔ Nenhuma pendência encontrada

Sua biblioteca está pronta para uso.
```

---

# Regras de Negócio Relacionadas

### RN-019

Uma pendência somente deve ser exibida se exigir alguma ação do usuário.

---

### RN-020

Pendências informativas não devem aparecer nesse painel.

Exemplo:

* última sincronização realizada;
* quantidade total de obras.

Essas informações pertencem aos indicadores do Dashboard.

---

### RN-021

Pendências devem ser agrupadas por categoria, nunca por item individual.

Exemplo correto:

```text
23 obras com novos capítulos
```

Exemplo incorreto:

```text
Payback
Semantic Error
Define The Relationship
...
```

O detalhamento pertence ao módulo **Fluxos**.

---

### RN-022

Cada categoria de pendência deve aparecer apenas uma vez.

---

### RN-023

Uma pendência crítica bloqueante possui prioridade superior a qualquer outra.

Exemplo:

```text
Banco indisponível
```

tem prioridade maior que

```text
8 IDs pendentes
```

---

### RN-024

Pendências devem ser recalculadas sempre que o Dashboard for atualizado.

---

### RN-025

Uma pendência resolvida deve desaparecer automaticamente após atualização do Dashboard.

---

### RN-026

Cada pendência deve possuir uma ação recomendada claramente identificada.

---

### RN-027

Pendências nunca executam ações diretamente.

Elas apenas direcionam o usuário para o módulo responsável.

---

### RN-028

A quantidade exibida representa o número de ocorrências pendentes no momento da consulta.

---

# Matriz de Priorização

| Prioridade | Tipo de Pendência          | Ação Recomendada              |
| ---------- | -------------------------- | ----------------------------- |
| Crítica    | Banco indisponível         | Configurações                 |
| Crítica    | Biblioteca inacessível     | Configurações                 |
| Alta       | Organização pendente       | Fluxos → Organizar biblioteca |
| Alta       | Catálogo desatualizado     | Fluxos → Catalogar arquivos   |
| Alta       | Obras sem ID               | Fluxos → Resolver IDs         |
| Média      | Metadados pendentes        | Fluxos → Atualizar metadados  |
| Média      | Sincronização pendente     | Fluxos → Sincronizar Notion   |
| Baixa      | Novos capítulos detectados | Biblioteca                    |

---

# Fonte de Dados

| Pendência              | Origem              |
| ---------------------- | ------------------- |
| Biblioteca inacessível | Sistema de arquivos |
| Banco indisponível     | PostgreSQL          |
| Organização pendente   | Workflow            |
| Catálogo desatualizado | Workflow            |
| Obras sem ID           | Catálogo            |
| Metadados pendentes    | MangaUpdates        |
| Sincronização pendente | Notion              |

---

# Pós-condições

Após utilizar esta funcionalidade, o usuário deve ser capaz de:

* compreender rapidamente quais problemas exigem atenção;
* identificar a prioridade de cada pendência;
* acessar diretamente o módulo responsável pela resolução;
* prosseguir no workflow sem precisar investigar manualmente o estado da aplicação.

---

# Observações de UX

O painel de pendências deve seguir alguns princípios fundamentais:

* Exibir apenas informações acionáveis.
* Evitar listas extensas de obras individuais.
* Agrupar ocorrências por categoria.
* Destacar visualmente apenas pendências críticas.
* Servir como um ponto de entrada para o módulo **Fluxos**, que é o responsável pela resolução efetiva das pendências.

Essa abordagem mantém o Dashboard limpo, orientado à tomada de decisão e evita duplicação de funcionalidades com as demais páginas da aplicação.
