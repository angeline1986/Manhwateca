# US-003 — Visualizar métricas operacionais

## Identificação

| Campo            | Valor                            |
| ---------------- | -------------------------------- |
| **ID**           | US-003                           |
| **Título**       | Visualizar métricas operacionais |
| **Módulo**       | Dashboard                        |
| **Prioridade**   | Alta                             |
| **Tipo**         | Funcionalidade                   |
| **Epic**         | Dashboard                        |
| **Dependências** | Catálogo, Workflow, Notion       |

---

# Objetivo

Como **usuária da Manhwateca**,

quero **visualizar rapidamente os principais indicadores operacionais da biblioteca**,

para que **eu consiga avaliar o estado atual da coleção sem precisar acessar outros módulos da aplicação**.

---

# Descrição

O Dashboard deve apresentar um conjunto reduzido de indicadores consolidados que representem a situação operacional da biblioteca.

Essas métricas têm finalidade exclusivamente informativa e devem permitir que o usuário compreenda rapidamente o estado da coleção.

As métricas devem ser apresentadas em formato de cards, utilizando linguagem simples e números fáceis de interpretar.

O Dashboard não deve apresentar gráficos complexos ou estatísticas detalhadas.

---

# Valor de Negócio

A consulta rápida das métricas permite que o usuário:

* acompanhe a evolução da biblioteca;
* identifique situações que exigem atenção;
* confirme se os processos foram executados corretamente;
* tenha confiança de que o catálogo está consistente.

Além disso, evita a necessidade de abrir módulos como Biblioteca ou Fluxos apenas para verificar informações básicas.

---

# Fluxo Principal

1. O usuário acessa o Dashboard.
2. O sistema consulta os indicadores consolidados.
3. O Dashboard apresenta os cards de métricas.
4. O usuário interpreta os números exibidos.
5. Caso alguma métrica indique necessidade de ação, o usuário pode seguir a recomendação apresentada no Dashboard.

---

# Fluxos Alternativos

### FA-01 — Não existem obras cadastradas

Caso o catálogo esteja vazio, os cards devem apresentar valor **0**, sem caracterizar erro.

---

### FA-02 — Dados temporariamente indisponíveis

Caso alguma métrica não possa ser calculada, o Dashboard deve exibir:

> Dados indisponíveis

sem comprometer o carregamento das demais informações.

---

### FA-03 — Atualização em andamento

Caso exista uma tarefa que esteja atualizando o catálogo, as métricas devem permanecer visíveis utilizando os últimos valores consolidados até a conclusão da tarefa.

---

# Critérios de Aceite

| ID     | Critério                                                                       |
| ------ | ------------------------------------------------------------------------------ |
| AC-001 | O Dashboard deve apresentar métricas em formato de cards.                      |
| AC-002 | Cada card deve possuir um título e um valor numérico.                          |
| AC-003 | As métricas devem utilizar dados consolidados do catálogo.                     |
| AC-004 | O carregamento das métricas não deve iniciar processos demorados.              |
| AC-005 | A indisponibilidade de uma métrica não deve impedir o carregamento das demais. |
| AC-006 | As métricas devem ser atualizadas sempre que o Dashboard for recarregado.      |

---

# Componentes Relacionados

## Card — Total de Obras

Apresenta a quantidade total de obras registradas no catálogo.

Exemplo:

```text
347
Obras catalogadas
```

---

## Card — Novos Capítulos

Apresenta a quantidade de obras que possuem novos capítulos detectados desde a última atualização.

Exemplo:

```text
23
Novos capítulos
```

---

## Card — Obras sem ID

Quantidade de obras que ainda não possuem identificação confirmada no MangaUpdates.

Exemplo:

```text
8
Sem ID
```

---

## Card — Notion

Quantidade de páginas que precisam ser sincronizadas.

Exemplo:

```text
14
Pendentes
```

---

# Regras de Negócio Relacionadas

### RN-011

As métricas devem ser calculadas utilizando informações consolidadas do banco de dados.

---

### RN-012

Nenhuma métrica deve executar consultas ao MangaUpdates durante o carregamento do Dashboard.

---

### RN-013

Nenhuma métrica deve consultar diretamente a biblioteca física.

---

### RN-014

Os valores apresentados representam apenas o estado conhecido da última atualização.

---

### RN-015

Valores indisponíveis devem ser sinalizados ao usuário sem comprometer a visualização dos demais indicadores.

---

### RN-016

Os cards devem permanecer sempre na mesma posição, independentemente do valor apresentado.

A interface não deve ocultar ou reordenar métricas dinamicamente.

---

### RN-017

As métricas possuem finalidade informativa e não permitem edição direta.

---

### RN-018

Os valores exibidos devem representar uma única fonte de verdade, evitando divergências entre Dashboard, Biblioteca e Fluxos.

---

# Fonte de Dados

| Métrica              | Origem                          |
| -------------------- | ------------------------------- |
| Total de Obras       | Catálogo local (PostgreSQL)     |
| Novos Capítulos      | Resultado da última catalogação |
| Obras sem ID         | Workflow / Catálogo             |
| Pendências do Notion | Processo de sincronização       |

---

# Pós-condições

Após visualizar as métricas, o usuário deve ser capaz de:

* compreender rapidamente a situação operacional da biblioteca;
* identificar indicadores que merecem atenção;
* confirmar que o catálogo está atualizado;
* prosseguir para o próximo passo recomendado com maior confiança.

---

# Observações de UX

As métricas devem seguir alguns princípios de usabilidade:

* Exibir apenas os indicadores realmente úteis para a tomada de decisão.
* Evitar excesso de cards ou informações estatísticas.
* Utilizar títulos curtos e autoexplicativos.
* Manter a disposição fixa dos cards entre diferentes execuções da aplicação.
* Complementar as métricas com o card **Próximo Passo Recomendado**, que contextualiza os números e orienta a próxima ação do usuário.
