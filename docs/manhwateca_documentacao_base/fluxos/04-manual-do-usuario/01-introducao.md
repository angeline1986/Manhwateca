# Introdução

> Documento: **01-introducao.md**

---

# Bem-vindo ao módulo Fluxos

O módulo **Fluxos** é responsável por executar todas as operações que mantêm a sua biblioteca organizada e sincronizada.

Sempre que você adicionar novas obras, reorganizar pastas, atualizar informações ou sincronizar o Notion, será nesta página que essas tarefas serão executadas.

Enquanto o **Dashboard** informa o estado atual da biblioteca, o módulo **Fluxos** é onde essas informações são efetivamente processadas.

---

# O que é um Workflow?

Na Manhwateca, um **Workflow** é uma sequência organizada de etapas executadas em uma ordem específica.

Cada etapa prepara os dados necessários para a próxima.

Isso garante que a biblioteca permaneça consistente durante todo o processamento.

O Workflow padrão é composto por cinco etapas.

```text
Organizar Biblioteca

↓

Catalogar Obras

↓

Resolver IDs

↓

Atualizar Metadados

↓

Sincronizar Notion
```

Essa sequência é executada automaticamente sempre que você inicia o Workflow completo.

---

# Qual é o objetivo da página Fluxos?

A página **Fluxos** funciona como um centro de processamento.

Ela permite:

* organizar a biblioteca;
* cadastrar novas obras;
* localizar identificadores oficiais;
* atualizar informações das obras;
* sincronizar dados com o Notion;
* acompanhar o progresso da execução;
* visualizar mensagens e alertas.

Em outras palavras, ela transforma alterações feitas na sua biblioteca em informações organizadas dentro da Manhwateca.

---

# Quando devo utilizar esta página?

Você deverá utilizar o módulo Fluxos sempre que ocorrer alguma alteração relevante na biblioteca.

Situações comuns incluem:

* adicionar novas obras;
* remover obras antigas;
* renomear pastas;
* reorganizar diretórios;
* atualizar informações oficiais das obras;
* sincronizar alterações com o Notion.

> **Dica**
>
> Mesmo que apenas uma pequena alteração tenha sido realizada, executar o Workflow garante que todas as informações permaneçam sincronizadas.

---

# Como funciona uma execução?

Quando você inicia o Workflow, a Manhwateca executa automaticamente todas as etapas necessárias.

Durante esse processo, o sistema:

1. verifica se o ambiente está preparado;
2. organiza a biblioteca;
3. cataloga novas obras;
4. resolve IDs pendentes;
5. atualiza metadados;
6. sincroniza os resultados com o Notion;
7. apresenta um resumo da execução.

Todo esse processamento pode ser acompanhado em tempo real pela própria interface.

---

# O que acontece durante o processamento?

Enquanto o Workflow estiver em execução, a página exibirá continuamente:

* etapa atual;
* progresso geral;
* quantidade de obras processadas;
* mensagens informativas;
* alertas;
* possíveis erros.

Você não precisa atualizar a página manualmente para acompanhar o andamento.

---

# Posso utilizar outros módulos durante a execução?

Sim.

O Workflow continua sendo executado mesmo que você navegue para outras páginas da Manhwateca.

Ao retornar para a página **Fluxos**, o sistema recuperará automaticamente:

* a etapa atual;
* o progresso;
* as mensagens recentes;
* o estado das integrações.

> **Importante**
>
> Sair da página **Fluxos** não interrompe o processamento. Para interromper uma execução, utilize o botão **Cancelar Workflow**.

---

# Quanto tempo demora uma execução?

O tempo necessário depende principalmente de:

* quantidade de obras;
* alterações realizadas;
* velocidade de acesso ao banco de dados;
* tempo de resposta do MangaUpdates;
* tempo de resposta do Notion.

Bibliotecas maiores naturalmente exigem mais tempo de processamento.

---

# O que acontece se ocorrer um erro?

Caso algum problema seja encontrado durante uma etapa:

* o sistema informará claramente o ocorrido;
* sempre que possível, continuará processando as demais obras;
* as alterações já concluídas serão preservadas;
* você poderá executar novamente apenas a etapa afetada.

Isso evita a necessidade de reiniciar todo o Workflow.

---

# Preciso executar todas as etapas sempre?

Na maioria das situações, recomenda-se executar o Workflow completo.

Entretanto, algumas etapas também podem ser executadas individualmente.

Por exemplo:

* atualizar apenas os metadados;
* sincronizar novamente com o Notion;
* resolver IDs pendentes.

Essa flexibilidade permite realizar manutenções específicas sem repetir todo o processamento.

---

# Antes da primeira execução

Antes de utilizar o módulo Fluxos pela primeira vez, verifique se:

* a biblioteca está configurada corretamente;
* o PostgreSQL está em execução;
* a conexão com o MangaUpdates está disponível;
* a integração com o Notion foi configurada (caso utilize esse recurso).

Esses requisitos garantem que todas as etapas possam ser executadas corretamente.

---

# O que você aprenderá nos próximos capítulos?

Nos próximos documentos deste manual você aprenderá:

* como reconhecer cada área da interface;
* como executar cada etapa do Workflow;
* como acompanhar o progresso da execução;
* como cancelar ou reiniciar um processamento;
* como resolver os problemas mais comuns.

Cada capítulo foi organizado para acompanhar a ordem natural de utilização da página.

---

# Próximo passo

Agora que você conhece o propósito do módulo **Fluxos**, o próximo capítulo apresenta a interface da página em detalhes, explicando a função de cada painel, botão e indicador.

---

# Conclusão

O módulo **Fluxos** é responsável por manter a biblioteca da Manhwateca organizada, atualizada e sincronizada. Compreender o funcionamento geral do Workflow facilita a interpretação das etapas seguintes e permite utilizar a aplicação de forma mais segura e eficiente.
