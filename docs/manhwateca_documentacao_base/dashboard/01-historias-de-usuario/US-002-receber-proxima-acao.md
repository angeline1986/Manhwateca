# US-002 — Receber a próxima ação recomendada

## Identificação

| Campo            | Valor                              |
| ---------------- | ---------------------------------- |
| **ID**           | US-002                             |
| **Título**       | Receber a próxima ação recomendada |
| **Módulo**       | Dashboard                          |
| **Prioridade**   | Muito Alta                         |
| **Tipo**         | Funcionalidade                     |
| **Epic**         | Dashboard                          |
| **Dependências** | Workflow                           |

---

# Objetivo

Como **usuária da Manhwateca**,

quero **que o sistema identifique automaticamente qual é a próxima etapa do processo que devo executar**,

para que **eu não precise decidir manualmente qual módulo utilizar nem lembrar em qual etapa parei**.

---

# Descrição

O Dashboard deve analisar continuamente o estado atual do Workflow, das pendências existentes e das integrações para determinar qual é a próxima ação mais adequada.

Essa recomendação deve ser apresentada em destaque na parte superior da tela através do card **Próximo Passo Recomendado**.

A recomendação representa apenas uma orientação. A execução efetiva da atividade ocorrerá na página **Fluxos**.

O Dashboard nunca deve apresentar mais de uma recomendação principal simultaneamente.

---

# Valor de Negócio

A Manhwateca possui um processo composto por diversas etapas dependentes entre si.

Sem uma recomendação automática, o usuário precisa lembrar:

* qual etapa executou anteriormente;
* quais pendências ainda existem;
* quais ações podem ou não ser executadas.

Ao recomendar automaticamente a próxima etapa, o sistema reduz a carga cognitiva, diminui erros operacionais e torna o workflow linear e previsível.

---

# Fluxo Principal

1. O usuário acessa o Dashboard.
2. O sistema consulta o estado atual do Workflow.
3. O sistema verifica pendências existentes.
4. O sistema identifica bloqueios.
5. O sistema determina a etapa prioritária.
6. O Dashboard exibe o card "Próximo Passo Recomendado".
7. O usuário seleciona **Continuar fluxo**.
8. O sistema abre a página **Fluxos** posicionada automaticamente na etapa recomendada.

---

# Fluxos Alternativos

### FA-01 — Workflow concluído

Caso todas as etapas estejam concluídas, o Dashboard deve apresentar:

> Biblioteca sincronizada. Nenhuma ação pendente.

O botão principal deve permitir apenas iniciar uma nova verificação.

---

### FA-02 — Existe bloqueio crítico

Caso exista algum bloqueio que impeça a continuidade do Workflow, a recomendação deve ser substituída pela resolução desse bloqueio.

Exemplo:

> Banco de dados indisponível.

ou

> Biblioteca não encontrada.

---

### FA-03 — Existe tarefa em execução

Caso uma etapa esteja sendo executada em segundo plano, o Dashboard não deve recomendar uma nova etapa.

Nesse cenário deve apresentar:

> Atualização de metadados em andamento...

---

### FA-04 — Primeira execução

Caso nenhuma etapa tenha sido executada anteriormente, o Dashboard deve recomendar:

> Organizar biblioteca.

---

# Critérios de Aceite

| ID     | Critério                                                                                            |
| ------ | --------------------------------------------------------------------------------------------------- |
| AC-001 | O Dashboard deve exibir exatamente uma recomendação principal.                                      |
| AC-002 | A recomendação deve refletir o estado atual do Workflow.                                            |
| AC-003 | A recomendação deve considerar bloqueios antes de sugerir novas ações.                              |
| AC-004 | O botão **Continuar fluxo** deve abrir a página Fluxos posicionada na etapa correspondente.         |
| AC-005 | Caso exista uma tarefa em execução, nenhuma nova recomendação deve ser apresentada.                 |
| AC-006 | Caso todas as etapas estejam concluídas, o Dashboard deve informar que não existem ações pendentes. |
| AC-007 | A recomendação deve ser recalculada sempre que o Dashboard for atualizado.                          |

---

# Regras de Negócio Relacionadas

* **RN-005** — O sistema deve recomendar apenas uma etapa por vez.
* **RN-006** — A recomendação deve sempre considerar a ordem oficial do Workflow.
* **RN-007** — Uma etapa bloqueada nunca pode ser recomendada.
* **RN-008** — Pendências críticas possuem prioridade sobre pendências informativas.
* **RN-009** — Tarefas em execução impedem a recomendação de novas etapas.
* **RN-010** — O Dashboard não deve iniciar automaticamente a etapa recomendada; ele apenas direciona o usuário para a página Fluxos.

---

# Matriz de Decisão

| Situação                               | Próximo Passo Recomendado    |
| -------------------------------------- | ---------------------------- |
| Biblioteca não configurada             | Configurar biblioteca        |
| Organização pendente                   | Organizar biblioteca         |
| Catálogo desatualizado                 | Catalogar arquivos           |
| Existem obras sem ID                   | Resolver IDs                 |
| Existem metadados pendentes            | Atualizar metadados          |
| Existem alterações pendentes no Notion | Sincronizar Notion           |
| Workflow concluído                     | Nenhuma ação pendente        |
| Existe bloqueio crítico                | Resolver bloqueio            |
| Existe tarefa em execução              | Aguardar conclusão da tarefa |

---

# Pós-condições

Após a execução desta funcionalidade, o usuário deve ser capaz de:

* identificar imediatamente qual é a próxima etapa do processo;
* continuar exatamente de onde parou;
* evitar executar etapas fora da ordem;
* navegar diretamente para a página **Fluxos** já posicionada na atividade recomendada.

---

## Observação de Arquitetura

Esta User Story é a principal responsável por conectar o **Dashboard** ao módulo **Fluxos**.

O Dashboard **não executa nenhuma etapa do workflow**. Sua responsabilidade termina ao calcular a recomendação e encaminhar o usuário para a etapa correta. Toda a lógica de execução permanece centralizada na página **Fluxos**, mantendo uma separação clara entre orientação (Dashboard) e execução (Fluxos).
