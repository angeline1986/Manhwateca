# Manual do Usuário — Dashboard

## 07 - Workflow

---

# Objetivo deste capítulo

Neste capítulo você aprenderá como funciona o **Workflow** da Manhwateca.

O Workflow representa a sequência oficial de etapas utilizada para organizar, enriquecer e manter sua biblioteca atualizada.

Ao compreender esse processo, você conseguirá utilizar a aplicação de forma muito mais eficiente, evitando executar atividades fora de ordem ou repetir tarefas desnecessariamente.

---

# O que é o Workflow?

O Workflow é o fluxo operacional da Manhwateca.

Ele organiza todas as atividades necessárias para transformar uma coleção de arquivos em uma biblioteca completa, contendo informações organizadas, metadados atualizados e sincronização com o Notion.

Cada etapa depende da conclusão da etapa anterior.

Por esse motivo, recomenda-se seguir sempre a sequência definida pela aplicação.

---

# Onde o Workflow está localizado?

No Dashboard, o Workflow é apresentado como um resumo visual do progresso da biblioteca.

Ele normalmente aparece após os painéis de Pendências e Integrações.

```text id="wf001"
Cabeçalho

↓

Próximo Passo

↓

Métricas

↓

Pendências

↓

Integrações

↓

Workflow

↓

Ações Rápidas
```

Esse componente permite acompanhar rapidamente o andamento geral da organização da biblioteca.

---

# Estrutura do Workflow

O Workflow é composto por cinco etapas fixas.

```text id="wf002"
✔ Organizar Biblioteca

✔ Catalogar Arquivos

► Resolver IDs

○ Atualizar Metadados

○ Sincronizar Notion
```

Cada etapa possui um objetivo específico e prepara a biblioteca para a etapa seguinte.

---

# As cinco etapas do Workflow

## 1. Organizar Biblioteca

Esta é a primeira etapa do processo.

Seu objetivo é analisar o diretório configurado da biblioteca e preparar a estrutura utilizada pela aplicação.

Durante essa etapa, a Manhwateca identifica a organização dos arquivos e verifica se a biblioteca está acessível.

### Quando executar?

* após configurar uma nova biblioteca;
* após reorganizar manualmente as pastas;
* quando solicitado pelo Dashboard.

---

## 2. Catalogar Arquivos

Após organizar a biblioteca, a aplicação identifica todas as obras encontradas.

Cada arquivo compatível passa a fazer parte do catálogo interno da Manhwateca.

### O que acontece?

* novas obras são cadastradas;
* obras removidas deixam de aparecer;
* o catálogo passa a refletir o conteúdo atual da biblioteca.

### Quando executar?

Sempre que novos arquivos forem adicionados ou removidos.

---

## 3. Resolver IDs

Depois que as obras são catalogadas, a aplicação precisa confirmar sua identificação.

Essa etapa associa cada obra ao seu identificador oficial.

Essa identificação é indispensável para consultar informações atualizadas.

### Quando executar?

Sempre que existirem obras sem identificação.

Normalmente o Dashboard apresentará essa etapa como **Próximo Passo Recomendado**.

---

## 4. Atualizar Metadados

Depois que todas as obras possuem identificação válida, a aplicação pode atualizar suas informações.

Entre os dados normalmente atualizados estão:

* título oficial;
* autores;
* artistas;
* gêneros;
* status da obra;
* número de capítulos;
* capa;
* outras informações disponíveis.

Essa etapa mantém a biblioteca atualizada.

---

## 5. Sincronizar Notion

A última etapa envia para o Notion as alterações realizadas na Manhwateca.

Ela garante que ambas as plataformas permaneçam sincronizadas.

Após essa etapa, o Workflow estará concluído.

---

# Estados das etapas

Cada etapa pode apresentar diferentes estados.

## Não iniciada

A atividade ainda não foi executada.

Representação:

```text id="wf003"
○
```

---

## Em andamento

A etapa está sendo executada.

Representação:

```text id="wf004"
►
```

---

## Concluída

A atividade foi finalizada com sucesso.

Representação:

```text id="wf005"
✔
```

---

## Bloqueada

A etapa não pode continuar porque existe alguma dependência pendente.

Exemplo:

Resolver IDs ainda não concluído.

Enquanto isso acontecer, a atualização de metadados permanecerá bloqueada.

---

## Erro

A etapa foi iniciada, mas não pôde ser concluída.

Nessa situação, recomenda-se consultar o painel de Pendências ou o módulo Configurações.

---

# Como acompanhar o progresso

O Workflow foi projetado para responder rapidamente a uma pergunta:

> **Em que etapa minha biblioteca está neste momento?**

Você não precisa abrir o módulo Fluxos para obter essa informação.

O Dashboard apresenta um resumo do progresso.

---

# Exemplo de evolução

## Biblioteca recém-configurada

```text id="wf006"
○ Organizar Biblioteca

○ Catalogar Arquivos

○ Resolver IDs

○ Atualizar Metadados

○ Sincronizar Notion
```

---

## Após organizar a biblioteca

```text id="wf007"
✔ Organizar Biblioteca

► Catalogar Arquivos

○ Resolver IDs

○ Atualizar Metadados

○ Sincronizar Notion
```

---

## Após identificar todas as obras

```text id="wf008"
✔ Organizar Biblioteca

✔ Catalogar Arquivos

✔ Resolver IDs

► Atualizar Metadados

○ Sincronizar Notion
```

---

## Workflow concluído

```text id="wf009"
✔ Organizar Biblioteca

✔ Catalogar Arquivos

✔ Resolver IDs

✔ Atualizar Metadados

✔ Sincronizar Notion
```

Essa é a situação ideal.

---

# Como utilizar o Workflow no dia a dia

Uma rotina recomendada é:

1. Abra o Dashboard.
2. Consulte o Workflow.
3. Identifique a etapa atual.
4. Execute a atividade correspondente em **Fluxos**.
5. Retorne ao Dashboard.
6. Clique em **Recarregar**.
7. Verifique se a próxima etapa foi liberada.

Esse processo reduz erros e mantém a biblioteca organizada.

---

# Posso executar as etapas fora de ordem?

Tecnicamente, algumas etapas podem ser iniciadas manualmente.

Entretanto, isso não é recomendado.

O Workflow foi planejado para que cada etapa utilize o resultado da etapa anterior.

Executar atividades fora da sequência pode resultar em informações incompletas ou desatualizadas.

> **Dica:** Sempre siga a ordem apresentada pelo Workflow ou pela **Ação Recomendada**. Essa é a forma mais segura e eficiente de utilizar a aplicação.

---

# Situações comuns

## O Workflow não avança

Verifique se existe alguma pendência bloqueante.

Na maioria das vezes, uma etapa anterior ainda precisa ser concluída.

---

## Uma etapa voltou a aparecer

Isso pode acontecer quando novas obras são adicionadas à biblioteca.

Nesse caso, algumas atividades precisam ser executadas novamente.

Esse comportamento é esperado.

---

## O Workflow está completo

Parabéns!

Sua biblioteca encontra-se organizada e sincronizada.

A partir desse momento, normalmente será necessário executar apenas as etapas relacionadas às novidades que surgirem.

---

# Perguntas Frequentes

### Preciso executar todas as etapas sempre?

Não.

Você executará apenas as etapas necessárias para refletir as alterações realizadas na biblioteca.

---

### O Workflow é automático?

Não completamente.

A Manhwateca orienta qual etapa deve ser executada, mas a decisão de iniciar cada processo permanece sob controle do usuário.

---

### Posso pular uma etapa?

Não é recomendado.

Cada etapa prepara os dados para a seguinte.

---

### O Dashboard executa o Workflow?

Não.

O Dashboard apenas apresenta o progresso.

A execução ocorre no módulo **Fluxos**.

---

# Resumo

Neste capítulo você aprendeu:

* o que é o Workflow da Manhwateca;
* quais são as cinco etapas oficiais do processo;
* o objetivo de cada etapa;
* como interpretar os estados do Workflow;
* como acompanhar o progresso da biblioteca;
* por que seguir a sequência oficial proporciona uma organização mais consistente.
