# US-005 — Acessar ações rápidas

## Identificação

| Campo            | Valor                               |
| ---------------- | ----------------------------------- |
| **ID**           | US-005                              |
| **Título**       | Acessar ações rápidas               |
| **Módulo**       | Dashboard                           |
| **Prioridade**   | Média                               |
| **Tipo**         | Funcionalidade                      |
| **Epic**         | Dashboard                           |
| **Dependências** | Workflow, Biblioteca, Configurações |

---

# Objetivo

Como **usuária da Manhwateca**,

quero **acessar rapidamente as principais funcionalidades do sistema diretamente pelo Dashboard**,

para que **eu consiga iniciar minhas atividades sem precisar navegar por diversos menus**.

---

# Descrição

O Dashboard deve disponibilizar uma área de **Ações Rápidas**, composta por atalhos para os principais objetivos do usuário.

Esses atalhos devem representar intenções de negócio, e não funcionalidades técnicas.

Por exemplo, o usuário pensa:

* "Quero organizar minha biblioteca."

e não:

* "Quero executar o script de organização."

Da mesma forma:

* "Quero sincronizar o Notion."

e não:

* "Executar notion_apply_batch."

O Dashboard deve traduzir objetivos do usuário em navegação para o módulo responsável.

As ações rápidas **não executam processos diretamente**. Elas apenas direcionam o usuário para a página e etapa apropriadas.

---

# Valor de Negócio

As ações rápidas reduzem o tempo necessário para localizar funcionalidades frequentes.

Além disso:

* diminuem a navegação;
* simplificam o uso da aplicação;
* ocultam detalhes técnicos;
* tornam o Dashboard o ponto central de entrada do sistema.

---

# Fluxo Principal

1. O usuário acessa o Dashboard.
2. O sistema apresenta a seção **Ações Rápidas**.
3. O usuário seleciona uma ação.
4. O Dashboard identifica o módulo responsável.
5. O sistema navega automaticamente para a página correspondente.

---

# Fluxos Alternativos

### FA-01 — Ação bloqueada

Caso a ação não possa ser executada devido ao estado atual do Workflow, o Dashboard deve redirecionar o usuário para a etapa obrigatória anterior.

Exemplo:

Usuário seleciona:

> Sincronizar Notion

Entretanto existem obras sem ID.

O sistema deve abrir:

> Fluxos → Resolver IDs

---

### FA-02 — Ambiente indisponível

Caso exista um erro de infraestrutura (PostgreSQL, diretório da biblioteca, configurações), o Dashboard deve abrir **Configurações** em vez da funcionalidade solicitada.

---

# Critérios de Aceite

| ID     | Critério                                                                     |
| ------ | ---------------------------------------------------------------------------- |
| AC-001 | O Dashboard deve apresentar uma seção de ações rápidas.                      |
| AC-002 | Cada ação deve representar um objetivo do usuário.                           |
| AC-003 | Selecionar uma ação deve abrir o módulo correspondente.                      |
| AC-004 | Nenhuma ação rápida deve executar alterações automaticamente.                |
| AC-005 | O Dashboard deve respeitar os bloqueios definidos pelo Workflow.             |
| AC-006 | A navegação deve posicionar o usuário diretamente na funcionalidade correta. |

---

# Componentes Relacionados

## Card — Organizar Biblioteca

Objetivo:

Permitir que o usuário inicie o processo de organização física da biblioteca.

Destino:

```text
Fluxos

↓

Etapa 1
Organizar biblioteca
```

---

## Card — Catalogar Arquivos

Objetivo:

Atualizar o catálogo local a partir da biblioteca física.

Destino:

```text
Fluxos

↓

Etapa 2
Catalogar arquivos
```

---

## Card — Resolver IDs

Objetivo:

Revisar obras que ainda não possuem identificação confirmada.

Destino:

```text
Fluxos

↓

Etapa 3
Resolver IDs
```

---

## Card — Atualizar Metadados

Objetivo:

Atualizar informações provenientes do MangaUpdates.

Destino:

```text
Fluxos

↓

Etapa 4
Atualizar metadados
```

---

## Card — Sincronizar Notion

Objetivo:

Iniciar o processo de sincronização do catálogo local com o Notion.

Destino:

```text
Fluxos

↓

Etapa 5
Sincronizar Notion
```

---

## Card — Abrir Biblioteca

Objetivo:

Consultar ou editar informações das obras.

Destino:

```text
Biblioteca
```

---

# Regras de Negócio Relacionadas

### RN-029

Ações rápidas representam **objetivos do usuário**, nunca nomes de scripts ou processos internos.

---

### RN-030

Cada ação rápida deve possuir um único destino.

---

### RN-031

O Dashboard não deve executar operações potencialmente destrutivas diretamente.

---

### RN-032

Caso uma ação dependa de etapas anteriores do Workflow, o sistema deve redirecionar automaticamente para a primeira etapa pendente.

---

### RN-033

Ações rápidas devem respeitar a ordem oficial do Workflow.

---

### RN-034

A quantidade de ações rápidas deve permanecer reduzida para evitar sobrecarga visual.

Recomendação:

* entre 4 e 6 ações.

---

### RN-035

As ações rápidas devem permanecer fixas, independentemente da quantidade de pendências.

Apenas seu comportamento poderá variar conforme o estado do Workflow.

---

### RN-036

Caso uma ação esteja temporariamente indisponível, ela deve permanecer visível, porém desabilitada, acompanhada de uma justificativa.

---

# Matriz de Navegação

| Ação Rápida          | Destino          |
| -------------------- | ---------------- |
| Organizar biblioteca | Fluxos → Etapa 1 |
| Catalogar arquivos   | Fluxos → Etapa 2 |
| Resolver IDs         | Fluxos → Etapa 3 |
| Atualizar metadados  | Fluxos → Etapa 4 |
| Sincronizar Notion   | Fluxos → Etapa 5 |
| Abrir biblioteca     | Biblioteca       |
| Configurações        | Configurações    |

---

# Pós-condições

Após utilizar esta funcionalidade, o usuário deve ser capaz de:

* acessar rapidamente o módulo desejado;
* iniciar uma atividade sem navegar pelo menu principal;
* ser direcionado automaticamente para a etapa correta do processo;
* respeitar o fluxo operacional definido pela Manhwateca.

---

# Observações de UX

As ações rápidas devem seguir os seguintes princípios:

* Ser orientadas ao **objetivo do usuário**, e não à tecnologia.
* Utilizar verbos claros e consistentes (Organizar, Catalogar, Resolver, Atualizar, Sincronizar).
* Não substituir o card **Próximo Passo Recomendado**, mas complementá-lo.
* Manter uma quantidade reduzida de opções para preservar a simplicidade do Dashboard.
* Quando houver conflito entre a ação escolhida e o estado do Workflow, o sistema deve conduzir o usuário para a etapa correta, em vez de permitir uma execução fora da sequência.
