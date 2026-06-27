# Manual do Usuário — Dashboard

## 11 - Perguntas Frequentes (FAQ)

---

# Objetivo deste capítulo

Este capítulo reúne as dúvidas mais comuns sobre o Dashboard da Manhwateca.

Antes de procurar suporte ou consultar a documentação técnica, recomenda-se verificar esta seção.

Muitas situações do dia a dia podem ser esclarecidas rapidamente através das perguntas e respostas abaixo.

---

# Sobre o Dashboard

## O que é o Dashboard?

O Dashboard é a tela principal da Manhwateca.

Ele funciona como um **centro de comando**, reunindo informações sobre a biblioteca, o Workflow, as integrações e as atividades que exigem sua atenção.

Ele não executa tarefas diretamente.

Seu objetivo é orientar o uso da aplicação.

---

## Preciso acessar o Dashboard sempre?

Não é obrigatório.

Entretanto, é altamente recomendado.

Consultar o Dashboard antes de iniciar qualquer atividade ajuda a identificar pendências, verificar o estado da biblioteca e acompanhar o Workflow.

---

## O Dashboard modifica minha biblioteca?

Não.

Ele apenas apresenta informações.

Qualquer alteração na biblioteca ocorre em módulos específicos, como **Fluxos**, **Biblioteca** ou **Configurações**.

---

# Sobre a Ação Recomendada

## Por que existe apenas uma recomendação?

A aplicação identifica automaticamente a atividade mais importante naquele momento.

Isso evita que você precise decidir entre diversas tarefas simultaneamente.

---

## Posso ignorar a recomendação?

Sim.

Você pode acessar qualquer módulo manualmente.

No entanto, seguir a recomendação normalmente reduz retrabalho e mantém o Workflow na sequência correta.

---

## A recomendação mudou. Isso é normal?

Sim.

Sempre que a situação da biblioteca muda, a Manhwateca recalcula automaticamente a próxima atividade recomendada.

---

# Sobre as Métricas

## O número de obras mudou. O que aconteceu?

Provavelmente:

* novas obras foram catalogadas;
* alguma obra foi removida;
* a biblioteca foi reorganizada.

---

## Por que existem obras sem ID?

Isso significa que essas obras ainda não possuem identificação confirmada.

Enquanto isso acontecer, algumas informações não poderão ser atualizadas.

---

## Ter muitos novos capítulos significa que há um problema?

Não.

Isso apenas indica que várias obras receberam atualizações desde a última consulta.

---

## Posso clicar nas métricas?

Não.

As métricas possuem finalidade exclusivamente informativa.

---

# Sobre Pendências

## O que é uma pendência?

É uma situação que exige ou recomenda alguma ação do usuário.

Nem toda pendência representa um erro.

---

## Posso remover uma pendência manualmente?

Não.

Ela desaparecerá automaticamente quando a situação correspondente for resolvida.

---

## Resolvi o problema, mas a pendência continua aparecendo.

Retorne ao Dashboard e utilize **Recarregar**.

Caso a pendência permaneça, confirme se a operação foi concluída com sucesso.

---

## Por que apareceu uma nova pendência?

Porque a situação da biblioteca mudou.

Por exemplo:

* novas obras foram adicionadas;
* novos capítulos foram encontrados;
* uma sincronização ficou pendente.

Esse comportamento é esperado.

---

# Sobre o Workflow

## Preciso executar todas as etapas sempre?

Não.

Apenas as etapas necessárias para refletir as alterações realizadas na biblioteca.

---

## Posso executar as etapas fora da ordem?

Tecnicamente algumas etapas podem ser iniciadas manualmente.

Entretanto, isso não é recomendado.

Cada etapa prepara os dados para a seguinte.

---

## O Dashboard executa o Workflow?

Não.

O Dashboard apenas apresenta o progresso.

A execução ocorre no módulo **Fluxos**.

---

## O Workflow voltou para uma etapa anterior. Isso é um erro?

Não.

Isso normalmente acontece quando novas obras são adicionadas ou alguma informação precisa ser atualizada novamente.

---

# Sobre Integrações

## Todas as integrações precisam estar verdes?

Depende da atividade.

Por exemplo:

* um problema no Notion afeta apenas a sincronização;
* um problema no PostgreSQL pode afetar praticamente toda a aplicação.

---

## O MangaUpdates está indisponível. Posso continuar utilizando a biblioteca?

Sim.

Você poderá consultar normalmente as obras já cadastradas.

Apenas operações que dependem desse serviço poderão ficar indisponíveis.

---

## Como corrijo um problema de integração?

Acesse o módulo **Configurações**, revise a configuração correspondente e, em seguida, retorne ao Dashboard para atualizar as informações.

---

# Sobre Atualização

## Preciso atualizar o Dashboard manualmente?

Na maioria das vezes, apenas após concluir uma atividade importante ou quando desejar consultar informações mais recentes.

---

## Atualizar o Dashboard é o mesmo que atualizar a página do navegador?

Não.

O botão **Recarregar** solicita novos dados ao sistema sem recarregar toda a interface.

---

## Atualizar o Dashboard altera minha biblioteca?

Não.

Ele apenas atualiza as informações exibidas.

---

## Cliquei em Recarregar e nada mudou.

Isso normalmente significa que nenhuma alteração ocorreu desde a última atualização.

---

# Sobre Navegação

## Qual a diferença entre o menu lateral e as Ações Rápidas?

Ambos acessam os mesmos módulos.

As Ações Rápidas apenas reduzem a quantidade de cliques.

---

## Posso acessar o módulo Fluxos sem utilizar a Ação Recomendada?

Sim.

Você pode acessar qualquer módulo livremente.

---

## Existe alguma funcionalidade disponível apenas pelas Ações Rápidas?

Não.

Elas são apenas atalhos.

---

# Situações comuns

## O Dashboard está vazio.

Verifique se:

* a biblioteca foi configurada;
* existem obras catalogadas;
* ocorreu algum erro de carregamento.

Caso necessário, utilize **Recarregar**.

---

## O Dashboard parece desatualizado.

Atualize as informações utilizando **Recarregar**.

Se o problema persistir, consulte o painel **Integrações**.

---

## Algumas informações desapareceram.

Isso pode ocorrer quando:

* uma pendência foi resolvida;
* o Workflow avançou;
* uma sincronização foi concluída.

Esse comportamento normalmente é esperado.

---

## Recebi uma mensagem de erro.

Consulte primeiro:

1. painel **Integrações**;
2. painel **Pendências**;
3. capítulo **12 - Solução de Problemas**.

---

# Dicas de utilização

> Consulte o Dashboard sempre antes de iniciar qualquer atividade.

> Após concluir uma etapa do Workflow, retorne ao Dashboard e utilize **Recarregar**.

> Não ignore pendências de alta prioridade.

> Sempre que possível, siga a **Ação Recomendada** apresentada pela aplicação.

---

# Ainda não encontrou sua resposta?

Se sua dúvida não estiver respondida neste FAQ:

1. Consulte o capítulo relacionado ao componente em questão.
2. Verifique o capítulo **12 - Solução de Problemas**.
3. Caso o problema persista, consulte a documentação técnica ou os canais de suporte do projeto.

---

# Resumo

Neste capítulo você encontrou respostas para as dúvidas mais frequentes sobre:

* funcionamento do Dashboard;
* interpretação das métricas;
* pendências;
* Workflow;
* integrações;
* atualização das informações;
* navegação;
* situações comuns do dia a dia.

O próximo capítulo apresentará procedimentos práticos para diagnosticar e resolver os problemas mais comuns encontrados durante a utilização do Dashboard.
