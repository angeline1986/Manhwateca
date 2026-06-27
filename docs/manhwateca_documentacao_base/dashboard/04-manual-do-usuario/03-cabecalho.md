# Manual do Usuário — Dashboard

## 03 - Cabeçalho

---

# Objetivo deste capítulo

Neste capítulo você aprenderá a utilizar o **Cabeçalho** do Dashboard.

Embora seja um dos menores componentes da tela, ele desempenha um papel importante ao identificar a página atual, informar quando os dados foram atualizados pela última vez e permitir a atualização manual das informações.

---

# O que é o Cabeçalho?

O Cabeçalho é a primeira área exibida no Dashboard.

Ele permanece no topo da página e reúne informações gerais sobre o estado atual da tela.

Além de identificar que você está no Dashboard, ele também informa quando os dados exibidos foram atualizados pela última vez e oferece acesso rápido à atualização manual.

---

# Estrutura do Cabeçalho

O Cabeçalho é composto pelos seguintes elementos.

```text
┌────────────────────────────────────────────────────────────┐
│ Dashboard                                                  │
│ Centro de comando da biblioteca                            │
│                                                            │
│ Última atualização: Hoje às 20:35      [ Recarregar ]      │
└────────────────────────────────────────────────────────────┘
```

Cada elemento possui uma função específica, descrita nas próximas seções.

---

# Identificação da Página

Na parte superior do Cabeçalho é exibido o nome do módulo atual.

Essa identificação permite confirmar rapidamente que você está na tela principal da aplicação.

Normalmente serão exibidos:

* **Dashboard**
* **Centro de comando da biblioteca** (subtítulo)

Essas informações permanecem constantes durante toda a utilização da página.

---

# Última Atualização

Logo abaixo do título é apresentada a data e o horário da última atualização das informações exibidas.

Exemplo:

```text
Última atualização:
Hoje às 20:35
```

ou

```text
Última atualização:
26/06/2026 20:35
```

Essa informação indica quando o Dashboard recebeu os dados mais recentes da aplicação.

Ela não representa necessariamente o momento em que uma sincronização com serviços externos foi executada.

---

# Quando observar a data de atualização?

A data de atualização é útil principalmente nas seguintes situações:

* após retornar de outro módulo da aplicação;
* antes de iniciar uma nova atividade;
* quando houver dúvidas se as informações estão atualizadas;
* após concluir uma etapa do Workflow.

Sempre que necessário, utilize o botão **Recarregar** para obter uma nova leitura dos dados.

---

# Botão **Recarregar**

O botão **Recarregar** permite solicitar uma atualização manual do Dashboard.

Ao utilizá-lo, a aplicação consulta novamente as informações mais recentes e atualiza todos os componentes da página.

Essa operação é rápida e não altera nenhum dado da biblioteca.

---

# Como atualizar o Dashboard

Siga os passos abaixo.

1. Localize o botão **Recarregar** no canto superior direito do Cabeçalho.
2. Clique em **Recarregar**.
3. Aguarde alguns instantes.
4. O Dashboard será atualizado automaticamente.
5. A data de **Última atualização** será alterada para refletir a nova consulta.

Você não precisa atualizar manualmente a página do navegador.

---

# Quando utilizar o botão **Recarregar**

Recomenda-se utilizar esse recurso quando:

* concluir uma etapa do Workflow;
* retornar da página **Fluxos**;
* retornar da página **Biblioteca**;
* alterar alguma configuração importante;
* desejar confirmar se existem novas pendências.

Na maioria das situações, uma atualização é suficiente para sincronizar as informações exibidas.

---

# O que acontece durante a atualização?

Ao clicar em **Recarregar**, a aplicação executa o seguinte processo:

1. Solicita uma nova leitura das informações.
2. Aguarda a resposta da aplicação.
3. Atualiza todos os componentes do Dashboard.
4. Atualiza a data da última atualização.

Durante esse processo, o restante da interface continua disponível.

Você não perde a posição da página nem precisa reiniciar a aplicação.

---

# O que o botão **Recarregar** não faz

É importante compreender que o botão **Recarregar** não executa tarefas operacionais.

Ele **não**:

* organiza a biblioteca;
* cataloga arquivos;
* resolve IDs;
* consulta o MangaUpdates;
* sincroniza o Notion;
* modifica qualquer obra cadastrada.

Seu único objetivo é atualizar as informações apresentadas no Dashboard.

---

# Situações comuns

## Acabei de concluir uma etapa do Workflow

Utilize **Recarregar** para visualizar imediatamente o novo estado da biblioteca.

---

## As métricas parecem antigas

Atualize o Dashboard antes de iniciar uma nova atividade.

---

## Não vejo uma alteração que acabei de realizar

Recarregue a página utilizando o botão **Recarregar**.

Se a alteração ainda não aparecer, verifique se a operação foi concluída com sucesso no módulo correspondente.

---

# Boas práticas

Para manter as informações sempre atualizadas:

* utilize **Recarregar** após concluir atividades importantes;
* evite atualizar repetidamente em intervalos muito curtos;
* confirme a data da última atualização antes de interpretar métricas ou pendências.

> **Dica:** O Dashboard foi projetado para ser atualizado rapidamente. Sempre que houver dúvida sobre a atualidade das informações, utilize o botão **Recarregar** em vez de recarregar toda a página do navegador.

---

# Perguntas Frequentes

### O botão Recarregar altera minha biblioteca?

Não.

Ele apenas solicita uma nova leitura das informações já existentes.

---

### Preciso atualizar sempre?

Não obrigatoriamente.

Entretanto, recomenda-se atualizar o Dashboard após concluir atividades importantes para garantir que as informações exibidas estejam atualizadas.

---

### Posso continuar utilizando a aplicação durante a atualização?

Sim.

A atualização não bloqueia a utilização da interface.

---

### A atualização consulta novamente todos os serviços externos?

Não necessariamente.

O Dashboard apenas solicita um novo conjunto de informações consolidadas ao sistema.

---

# Resumo

Neste capítulo você aprendeu:

* qual é a função do Cabeçalho;
* como interpretar a data da última atualização;
* quando utilizar o botão **Recarregar**;
* o que acontece durante a atualização;
* quais ações **não** são executadas por esse botão.

Esses conceitos serão importantes para compreender os próximos componentes do Dashboard.
