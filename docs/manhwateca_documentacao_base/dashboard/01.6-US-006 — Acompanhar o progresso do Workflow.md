# US-006 — Acompanhar o progresso do Workflow

## Identificação

| Campo            | Valor                              |
| ---------------- | ---------------------------------- |
| **ID**           | US-006                             |
| **Título**       | Acompanhar o progresso do Workflow |
| **Módulo**       | Dashboard                          |
| **Prioridade**   | Alta                               |
| **Tipo**         | Funcionalidade                     |
| **Epic**         | Dashboard                          |
| **Dependências** | Workflow                           |

---

# Objetivo

Como **usuária da Manhwateca**,

quero **visualizar em qual etapa do workflow minha biblioteca se encontra**,

para que **eu saiba exatamente o que já foi concluído, o que está em andamento e qual será a próxima etapa do processo**.

---

# Descrição

O Dashboard deve apresentar um resumo visual do Workflow da Manhwateca.

O objetivo não é permitir a execução das etapas, mas fornecer contexto suficiente para que o usuário compreenda o andamento do processo sem precisar abrir a página **Fluxos**.

O resumo deve refletir o estado atual do Workflow, indicando:

* etapas concluídas;
* etapa atual;
* etapas pendentes;
* etapas bloqueadas.

O Dashboard deve apresentar apenas um resumo. Toda interação operacional permanece concentrada na página **Fluxos**.

---

# Valor de Negócio

Grande parte das operações da Manhwateca depende da execução de etapas em uma ordem específica.

Ao apresentar o progresso do Workflow, o Dashboard permite que o usuário:

* retome o trabalho após períodos de inatividade;
* compreenda rapidamente em qual ponto o processo foi interrompido;
* identifique bloqueios antes de iniciar novas atividades;
* tenha confiança de que o processo está seguindo a sequência correta.

---

# Fluxo Principal

1. O usuário acessa o Dashboard.
2. O sistema consulta o estado atual do Workflow.
3. O Dashboard exibe o resumo das etapas.
4. O usuário identifica a etapa atual.
5. O usuário seleciona **Continuar fluxo**.
6. O sistema abre a página **Fluxos** posicionada exatamente na etapa atual.

---

# Fluxos Alternativos

### FA-01 — Workflow ainda não iniciado

Caso nenhuma etapa tenha sido executada, o Dashboard deve indicar:

```text
Workflow não iniciado

Próxima etapa:
Organizar biblioteca
```

---

### FA-02 — Workflow concluído

Caso todas as etapas tenham sido concluídas, o Dashboard deve apresentar:

```text
Workflow concluído

Nenhuma etapa pendente.
```

---

### FA-03 — Workflow bloqueado

Caso exista um bloqueio, a etapa correspondente deve permanecer destacada com indicação de impedimento.

O Dashboard deve informar o motivo do bloqueio.

---

### FA-04 — Workflow em execução

Caso exista uma tarefa em andamento, o Dashboard deve indicar:

* etapa atual;
* status da execução;
* progresso (quando disponível).

---

# Critérios de Aceite

| ID     | Critério                                                                               |
| ------ | -------------------------------------------------------------------------------------- |
| AC-001 | O Dashboard deve apresentar um resumo do Workflow.                                     |
| AC-002 | Deve existir apenas uma etapa marcada como atual.                                      |
| AC-003 | Etapas concluídas devem ser identificadas visualmente.                                 |
| AC-004 | Etapas bloqueadas devem informar o motivo do bloqueio.                                 |
| AC-005 | O botão **Continuar fluxo** deve abrir a página **Fluxos** posicionada na etapa atual. |
| AC-006 | O resumo deve ser atualizado sempre que o Dashboard for recarregado.                   |

---

# Componentes Relacionados

## Resumo do Workflow

Representação simplificada das cinco etapas oficiais da Manhwateca.

Exemplo:

```text
✔ Organizar biblioteca

✔ Catalogar arquivos

► Resolver IDs

○ Atualizar metadados

○ Sincronizar Notion
```

---

## Indicador de Etapa Atual

A etapa atual deve receber destaque visual.

Deve existir apenas uma etapa ativa.

---

## Indicador de Conclusão

Etapas concluídas devem permanecer visíveis, permitindo que o usuário compreenda o histórico da execução.

---

## Botão — Continuar Fluxo

Responsável por abrir a página **Fluxos** exatamente na etapa atualmente recomendada.

---

# Regras de Negócio Relacionadas

### RN-037

O Workflow oficial da Manhwateca é composto por cinco etapas sequenciais:

1. Organizar biblioteca
2. Catalogar arquivos
3. Resolver IDs
4. Atualizar metadados
5. Sincronizar Notion

---

### RN-038

A ordem das etapas é fixa e não pode ser alterada pela interface.

---

### RN-039

Somente uma etapa pode estar marcada como **Atual**.

---

### RN-040

Etapas concluídas não podem retornar ao estado "Atual" sem reinicialização explícita do Workflow.

---

### RN-041

Etapas bloqueadas impedem o avanço para as etapas seguintes.

---

### RN-042

O Dashboard deve refletir exatamente o estado mantido pelo módulo **Fluxos**, sem recalcular o progresso localmente.

O módulo **Fluxos** é a única fonte de verdade para o estado do Workflow.

---

### RN-043

O Dashboard não deve permitir alterar manualmente o estado de nenhuma etapa.

---

### RN-044

Caso uma etapa esteja em execução, ela deve permanecer identificada até a conclusão da tarefa correspondente.

---

### RN-045

Toda navegação iniciada pelo botão **Continuar fluxo** deve respeitar a etapa atual definida pelo Workflow.

---

# Estados Possíveis das Etapas

| Estado       | Descrição                                                               |
| ------------ | ----------------------------------------------------------------------- |
| Não iniciada | A etapa ainda não foi executada.                                        |
| Atual        | É a etapa que deve ser executada neste momento.                         |
| Em execução  | Existe uma tarefa em andamento relacionada à etapa.                     |
| Concluída    | A etapa foi executada com sucesso.                                      |
| Bloqueada    | A etapa não pode ser executada devido a uma dependência não satisfeita. |
| Erro         | A última execução terminou com falha.                                   |

---

# Diagrama de Estados Simplificado

```text
Não iniciada
      │
      ▼
Atual
      │
      ▼
Em execução
      │
 ┌────┴────┐
 ▼         ▼
Concluída  Erro
              │
              ▼
            Atual
```

---

# Fonte de Dados

Todas as informações apresentadas pelo resumo do Workflow devem ser obtidas exclusivamente do módulo **Fluxos**.

O Dashboard não deve manter qualquer lógica própria de controle de estados.

---

# Pós-condições

Após utilizar esta funcionalidade, o usuário deve ser capaz de:

* compreender imediatamente em qual etapa do processo sua biblioteca se encontra;
* identificar o progresso geral do Workflow;
* reconhecer eventuais bloqueios;
* continuar o processo exatamente do ponto em que foi interrompido.

---

# Observações de UX

O resumo do Workflow deve ser **informativo**, e não interativo.

Seu propósito é fornecer contexto e reforçar visualmente a progressão do processo.

Toda execução, revisão de pendências e confirmação de ações permanece centralizada na página **Fluxos**, preservando uma separação clara entre **orientação (Dashboard)** e **execução (Fluxos)**.
