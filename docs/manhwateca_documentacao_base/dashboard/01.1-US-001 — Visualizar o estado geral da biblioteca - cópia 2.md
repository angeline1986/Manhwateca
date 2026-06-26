
# US-001 — Visualizar o estado geral da biblioteca

## Identificação

| Campo            | Valor                                   |
| ---------------- | --------------------------------------- |
| **ID**           | US-001                                  |
| **Título**       | Visualizar o estado geral da biblioteca |
| **Módulo**       | Dashboard                               |
| **Prioridade**   | Alta                                    |
| **Tipo**         | Funcionalidade                          |
| **Epic**         | Dashboard                               |
| **Dependências** | Nenhuma                                 |

---

# Objetivo

Como **usuária da Manhwateca**,

quero **visualizar rapidamente o estado geral da minha biblioteca e das integrações do sistema**,

para que **eu possa compreender a situação atual da aplicação antes de decidir qual ação executar**.

---

# Descrição

Ao acessar a Manhwateca, o Dashboard deve apresentar uma visão consolidada do estado operacional do sistema.

Essa visão deve reunir informações provenientes da biblioteca local, do catálogo, do workflow e das integrações, eliminando a necessidade de acessar múltiplas páginas para entender a situação atual.

O Dashboard deve atuar exclusivamente como uma tela de monitoramento e orientação, não sendo responsável pela execução de processos complexos.

---

# Valor de Negócio

Esta funcionalidade reduz a carga cognitiva do usuário ao concentrar, em uma única tela, as informações mais relevantes sobre a operação da Manhwateca.

O usuário consegue identificar rapidamente se existe alguma pendência crítica, se o ambiente está saudável e se pode continuar exatamente de onde parou.

---

# Fluxo Principal

1. O usuário acessa a aplicação.
2. O sistema carrega as informações consolidadas do Dashboard.
3. O Dashboard apresenta os indicadores principais da biblioteca.
4. O Dashboard apresenta o estado das integrações.
5. O Dashboard apresenta a situação atual do workflow.
6. O usuário avalia o estado geral antes de decidir a próxima ação.

---

# Fluxos Alternativos

### FA-01 — Dados parcialmente indisponíveis

Caso alguma integração esteja indisponível, o Dashboard deve continuar sendo exibido utilizando os dados disponíveis.

Os componentes afetados devem apresentar estado de indisponibilidade sem impedir o carregamento da página.

---

### FA-02 — Nenhuma obra cadastrada

Caso o catálogo esteja vazio, o Dashboard deve apresentar uma mensagem orientando o usuário a iniciar o processo de catalogação.

---

### FA-03 — Primeira execução

Caso seja o primeiro acesso ao sistema, o Dashboard deve exibir um estado inicial com orientações para configurar a biblioteca antes de executar qualquer workflow.

---

# Critérios de Aceite

| ID     | Critério                                                                                                                                              |
| ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| AC-001 | O Dashboard deve carregar automaticamente ao iniciar a aplicação.                                                                                     |
| AC-002 | O Dashboard deve apresentar informações consolidadas da biblioteca.                                                                                   |
| AC-003 | O Dashboard deve apresentar o estado das integrações configuradas.                                                                                    |
| AC-004 | O Dashboard deve apresentar o estado atual do workflow.                                                                                               |
| AC-005 | O Dashboard não deve permitir edição de dados diretamente nessa tela.                                                                                 |
| AC-006 | O Dashboard deve continuar carregando mesmo quando uma integração estiver indisponível, sinalizando o problema ao usuário.                            |
| AC-007 | O Dashboard deve responder em tempo compatível com o carregamento da aplicação, utilizando dados consolidados em vez de executar operações demoradas. |

---

# Regras de Negócio Relacionadas

* **RN-001** — O Dashboard deve representar o estado atual da aplicação utilizando apenas informações consolidadas.
* **RN-002** — O Dashboard não deve executar tarefas de organização, catalogação ou sincronização automaticamente.
* **RN-003** — Toda informação apresentada deve possuir uma origem única de dados, evitando divergências entre módulos.
* **RN-004** — O Dashboard deve permanecer funcional mesmo quando uma ou mais integrações estiverem indisponíveis.

---

# Pós-condições

Após o carregamento bem-sucedido desta funcionalidade, o usuário deve ser capaz de:

* compreender a situação geral da biblioteca;
* identificar possíveis problemas;
* verificar a saúde das integrações;
* decidir conscientemente qual será a próxima ação dentro da Manhwateca.

 