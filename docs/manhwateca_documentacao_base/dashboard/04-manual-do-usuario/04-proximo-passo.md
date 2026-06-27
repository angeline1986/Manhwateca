# Manual do Usuário — Dashboard

## 04 - Próximo Passo Recomendado

---

# Objetivo deste capítulo

Neste capítulo você aprenderá a utilizar o painel **Próximo Passo Recomendado**, o componente mais importante do Dashboard.

Ele foi desenvolvido para eliminar dúvidas sobre qual atividade deve ser realizada em seguida, orientando você durante todo o processo de organização da biblioteca.

Ao compreender esse componente, você poderá utilizar a Manhwateca de forma muito mais eficiente, seguindo sempre a prioridade definida pela própria aplicação.

---

# O que é o Próximo Passo Recomendado?

O painel **Próximo Passo Recomendado** é o principal destaque do Dashboard.

Seu objetivo é responder uma única pergunta:

> **Qual é a próxima atividade que devo executar?**

Sempre que existir alguma tarefa pendente, a aplicação analisará automaticamente a situação da biblioteca e indicará a ação mais importante naquele momento.

Isso evita que você precise analisar diversas métricas ou abrir outros módulos para decidir por onde começar.

---

# Onde ele está localizado?

O painel é exibido logo abaixo do Cabeçalho.

Sua posição de destaque permite que seja visualizado imediatamente ao abrir o Dashboard.

```text id="tszjtf"
Cabeçalho

↓

Próximo Passo Recomendado

↓

Métricas

↓

Demais componentes
```

Essa organização foi planejada para que você identifique rapidamente a prioridade do momento.

---

# Estrutura do Painel

O painel normalmente apresenta os seguintes elementos.

```text id="p3dz8m"
┌────────────────────────────────────────────────────────────┐
│ Próximo Passo Recomendado                                 │
│                                                            │
│ Resolver 8 obras sem ID                                   │
│                                                            │
│ Existem obras catalogadas que ainda precisam ser           │
│ identificadas antes da atualização dos metadados.          │
│                                                            │
│ [Continuar fluxo]     [Ver pendências]                     │
└────────────────────────────────────────────────────────────┘
```

Cada parte possui uma função específica.

---

# Título da Recomendação

O título informa a atividade que deve ser executada.

Exemplos:

* Organizar Biblioteca
* Catalogar Arquivos
* Resolver IDs
* Atualizar Metadados
* Sincronizar Notion

O título sempre representa uma ação concreta.

---

# Descrição

Abaixo do título é apresentada uma breve explicação.

Essa descrição responde:

* por que essa atividade foi escolhida;
* qual problema ela resolve;
* qual o impacto esperado.

Ela foi escrita para facilitar a tomada de decisão, sem utilizar termos excessivamente técnicos.

---

# Botão **Continuar Fluxo**

O botão **Continuar Fluxo** leva você diretamente ao módulo **Fluxos**, posicionando a aplicação na etapa correspondente à recomendação apresentada.

Você não precisa localizar manualmente a etapa correta.

Esse comportamento reduz a navegação e evita erros.

---

# Botão **Ver Pendências**

Quando disponível, o botão **Ver Pendências** permite consultar as pendências relacionadas à recomendação atual.

Ele é útil quando você deseja compreender melhor o motivo pelo qual determinada atividade foi priorizada.

---

# Como a recomendação é definida?

A Manhwateca analisa automaticamente o estado atual da biblioteca.

Entre os fatores considerados estão:

* existência de obras ainda não organizadas;
* arquivos ainda não catalogados;
* obras sem identificação;
* necessidade de atualização de metadados;
* pendências de sincronização;
* bloqueios do ambiente.

A partir dessas informações, apenas **uma recomendação principal** é apresentada.

Você não precisa escolher entre várias opções.

---

# Por que existe apenas uma recomendação?

O Dashboard foi projetado para reduzir a carga de decisão.

Em vez de apresentar diversas tarefas concorrentes, ele identifica aquela que possui maior prioridade.

Isso torna o fluxo de utilização mais simples e previsível.

> **Dica:** Sempre que possível, siga a recomendação apresentada antes de iniciar qualquer outra atividade.

---

# Exemplos de Recomendações

## Biblioteca recém-configurada

```text id="abk6mb"
Organizar Biblioteca
```

A biblioteca ainda precisa ser preparada para as próximas etapas.

---

## Novos arquivos adicionados

```text id="uhxpcx"
Catalogar Arquivos
```

Os novos arquivos precisam ser identificados e adicionados ao catálogo.

---

## Obras sem identificação

```text id="9dyjgs"
Resolver IDs
```

Algumas obras ainda não possuem identificação confirmada.

---

## Informações desatualizadas

```text id="4h0tto"
Atualizar Metadados
```

Os dados das obras precisam ser atualizados.

---

## Alterações pendentes

```text id="1h4d3m"
Sincronizar Notion
```

Existem modificações aguardando sincronização.

---

# Quando nenhuma ação for necessária

Caso todas as etapas do Workflow estejam concluídas, o painel informará que não existem atividades pendentes.

Exemplo:

```text id="v6hhnl"
Nenhuma ação pendente.

Sua biblioteca está atualizada.
```

Isso indica que não há nenhuma intervenção imediata necessária.

---

# Quando a recomendação não puder ser exibida

Em algumas situações, o sistema poderá não conseguir determinar a próxima atividade.

Isso pode ocorrer, por exemplo, quando existir um problema de infraestrutura.

Nesses casos, o painel apresentará uma mensagem apropriada e orientará você a verificar as configurações da aplicação.

---

# Fluxo recomendado de utilização

Sempre que abrir a Manhwateca, utilize o seguinte processo:

1. Leia o **Próximo Passo Recomendado**.
2. Compreenda o motivo da recomendação.
3. Clique em **Continuar Fluxo**.
4. Execute a atividade indicada.
5. Retorne ao Dashboard.
6. Atualize as informações utilizando **Recarregar**.
7. Consulte a nova recomendação.

Esse ciclo representa o fluxo de utilização esperado da aplicação.

---

# Situações comuns

## Existe mais de uma pendência

A aplicação selecionará automaticamente aquela com maior prioridade.

---

## Não concordo com a recomendação

Você pode acessar qualquer módulo manualmente.

Entretanto, recomenda-se seguir a ordem sugerida pelo Dashboard, pois ela respeita a sequência oficial do Workflow.

---

## A recomendação mudou

Isso é esperado.

Sempre que uma etapa for concluída, o Dashboard recalculará automaticamente a próxima atividade.

---

# Boas práticas

Para aproveitar melhor esse componente:

* consulte-o antes de iniciar qualquer atividade;
* siga a recomendação apresentada sempre que possível;
* conclua uma etapa antes de iniciar outra;
* atualize o Dashboard após finalizar cada atividade.

> **Dica:** O painel **Próximo Passo Recomendado** foi desenvolvido para ser o principal guia de utilização da Manhwateca. Quanto mais você seguir suas recomendações, mais simples será manter sua biblioteca organizada.

---

# Perguntas Frequentes

### Posso ignorar a recomendação?

Sim.

A aplicação permite navegar livremente entre os módulos.

No entanto, seguir a recomendação ajuda a evitar retrabalho e etapas executadas fora da ordem.

---

### A recomendação altera automaticamente minha biblioteca?

Não.

Ela apenas orienta qual atividade deve ser realizada.

---

### Por que a recomendação mudou?

Porque o estado da biblioteca foi alterado.

Sempre que uma etapa é concluída, o sistema recalcula automaticamente a próxima ação mais importante.

---

# Resumo

Neste capítulo você aprendeu:

* qual é a função do painel **Próximo Passo Recomendado**;
* como a aplicação determina a próxima atividade;
* como utilizar os botões disponíveis;
* por que existe apenas uma recomendação principal;
* como esse componente orienta todo o fluxo de utilização da Manhwateca.
