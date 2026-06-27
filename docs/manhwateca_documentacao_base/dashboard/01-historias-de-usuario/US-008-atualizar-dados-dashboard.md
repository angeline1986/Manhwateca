# US-008 — Atualizar os dados do Dashboard

## Identificação

| Campo            | Valor                               |
| ---------------- | ----------------------------------- |
| **ID**           | US-008                              |
| **Título**       | Atualizar os dados do Dashboard     |
| **Módulo**       | Dashboard                           |
| **Prioridade**   | Média                               |
| **Tipo**         | Funcionalidade                      |
| **Epic**         | Dashboard                           |
| **Dependências** | Dashboard API, Workflow, PostgreSQL |

---

# Objetivo

Como **usuária da Manhwateca**,

quero **atualizar manualmente as informações exibidas no Dashboard**,

para que **eu possa visualizar o estado mais recente da aplicação após executar alguma operação, sem precisar recarregar toda a página ou reiniciar o sistema**.

---

# Descrição

O Dashboard deve disponibilizar um botão **Recarregar**, responsável por atualizar todas as informações exibidas na tela.

A atualização deve solicitar novamente os dados consolidados ao backend e substituir apenas os conteúdos necessários, preservando o estado da interface e evitando recarregar toda a aplicação.

Essa funcionalidade não executa tarefas operacionais, como catalogação, busca de metadados ou sincronização. Ela apenas consulta o estado atual do sistema.

---

# Valor de Negócio

Durante o uso da Manhwateca, diversas informações podem mudar após a execução de tarefas no módulo **Fluxos**.

Permitir a atualização manual do Dashboard oferece benefícios como:

* confirmação imediata dos resultados;
* redução da necessidade de reiniciar a aplicação;
* visualização do estado mais recente da biblioteca;
* melhoria da percepção de responsividade do sistema.

---

# Fluxo Principal

1. O usuário executa uma ou mais operações na Manhwateca.
2. O usuário retorna ao Dashboard.
3. O usuário seleciona **Recarregar**.
4. O Dashboard solicita os dados atualizados ao backend.
5. Os componentes da tela são atualizados.
6. O usuário visualiza o novo estado da aplicação.

---

# Fluxos Alternativos

### FA-01 — Atualização realizada com sucesso

Todos os componentes recebem os novos dados.

Uma mensagem discreta pode ser apresentada:

```text
Dashboard atualizado.
```

---

### FA-02 — Falha na atualização

Caso ocorra erro de comunicação, o Dashboard deve manter os dados atuais e informar:

```text
Não foi possível atualizar as informações.

Tente novamente.
```

---

### FA-03 — Atualização sem alterações

Caso nenhum dado tenha sido alterado desde a última consulta, o Dashboard deve apenas atualizar a data da última verificação.

---

# Critérios de Aceite

| ID     | Critério                                                                                |
| ------ | --------------------------------------------------------------------------------------- |
| AC-001 | O Dashboard deve disponibilizar um botão **Recarregar**.                                |
| AC-002 | A atualização deve consultar novamente o backend.                                       |
| AC-003 | Apenas os dados devem ser atualizados; a página não deve ser recarregada completamente. |
| AC-004 | O estado visual da interface deve ser preservado durante a atualização.                 |
| AC-005 | Em caso de erro, os dados atuais devem permanecer visíveis.                             |
| AC-006 | Após a atualização, o Dashboard deve refletir o estado mais recente da aplicação.       |

---

# Componentes Relacionados

## Botão — Recarregar

Responsável por solicitar novamente todas as informações necessárias para renderizar o Dashboard.

---

## Indicador de Atualização

Durante a consulta, o botão pode apresentar um estado de carregamento.

Exemplo:

```text
Atualizando...
```

---

## Mensagem de Resultado

Após a conclusão da operação, o sistema pode apresentar uma confirmação discreta.

Exemplo:

```text
Dados atualizados.
```

---

# Regras de Negócio Relacionadas

### RN-053

A atualização do Dashboard não deve iniciar tarefas operacionais.

---

### RN-054

O sistema deve consultar apenas informações consolidadas já existentes.

---

### RN-055

A atualização deve ocorrer de forma assíncrona, sem bloquear a interface.

---

### RN-056

Em caso de falha, o Dashboard deve preservar os dados anteriormente exibidos.

---

### RN-057

A atualização deve ocorrer de forma atômica.

Os componentes não devem exibir informações parcialmente atualizadas.

---

### RN-058

Uma nova atualização não deve ser iniciada enquanto a anterior estiver em andamento.

---

### RN-059

Ao concluir a atualização, o Dashboard deve recalcular:

* próximo passo recomendado;
* métricas;
* pendências;
* estado do workflow;
* estado das integrações.

---

### RN-060

O Dashboard não deve executar consultas diretamente às APIs externas (MangaUpdates ou Notion) durante a atualização.

Todas as informações devem ser obtidas por meio da API consolidada do backend.

---

# Dados Atualizados

Ao executar a atualização, o sistema deve consultar:

* próximo passo recomendado;
* métricas operacionais;
* pendências críticas;
* progresso do workflow;
* estado das integrações;
* data da última atualização.

---

# Fonte de Dados

Toda a atualização deve ocorrer por meio de um endpoint consolidado, por exemplo:

```http
GET /api/dashboard
```

O Dashboard não deve realizar múltiplas chamadas independentes para cada componente.

---

# Pós-condições

Após utilizar esta funcionalidade, o usuário deve ser capaz de:

* confirmar que as informações exibidas refletem o estado atual da aplicação;
* visualizar imediatamente os efeitos de operações executadas anteriormente;
* continuar utilizando o Dashboard sem interrupções ou perda de contexto.

---

# Observações de UX

A atualização do Dashboard deve transmitir rapidez e continuidade.

Para isso:

* evitar recarregar toda a página;
* manter a posição de rolagem;
* preservar estados visuais da interface;
* utilizar indicadores discretos de carregamento;
* evitar mensagens excessivas de sucesso.

> **Observação de arquitetura:** o Dashboard deve consumir uma **API agregadora**, responsável por consolidar todas as informações necessárias para a tela. Essa abordagem reduz chamadas ao backend, simplifica o front-end e garante consistência entre os diferentes componentes exibidos.
