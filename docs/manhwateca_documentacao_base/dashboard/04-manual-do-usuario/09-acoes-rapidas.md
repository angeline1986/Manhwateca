# Manual do Usuário — Dashboard

## 09 - Ações Rápidas

---

# Objetivo deste capítulo

Neste capítulo você aprenderá a utilizar o painel **Ações Rápidas** do Dashboard.

Esse componente foi criado para facilitar a navegação entre os principais módulos da Manhwateca, permitindo iniciar uma atividade com poucos cliques.

Ao final deste capítulo você compreenderá:

* para que serve cada ação disponível;
* quando utilizar cada botão;
* para onde cada ação direciona;
* quando utilizar as Ações Rápidas em vez do menu lateral.

---

# O que são as Ações Rápidas?

As Ações Rápidas são atalhos para as funcionalidades mais utilizadas da Manhwateca.

Em vez de navegar pelo menu lateral, você pode utilizar esses botões para acessar rapidamente os módulos mais importantes da aplicação.

As Ações Rápidas não executam nenhuma tarefa diretamente.

Elas apenas levam você ao local apropriado.

---

# Onde elas estão localizadas?

As Ações Rápidas aparecem na parte inferior do Dashboard.

```text id="ar001"
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

Por estarem posicionadas ao final da página, elas funcionam como uma conclusão natural da análise do Dashboard.

Depois de entender a situação da biblioteca, basta utilizar o atalho adequado para iniciar a próxima atividade.

---

# Estrutura do painel

O painel apresenta quatro botões.

```text id="ar002"
┌──────────────────────────────────────────────┐
│ Ações Rápidas                                │
│                                              │
│ [ Biblioteca ]                               │
│ [ Fluxos ]                                   │
│ [ Recarregar Dashboard ]                     │
│ [ Configurações ]                            │
└──────────────────────────────────────────────┘
```

Cada botão possui uma finalidade específica.

---

# Biblioteca

## Para que serve?

Abre o módulo **Biblioteca**, onde você pode consultar sua coleção.

Esse módulo é utilizado para visualizar informações detalhadas sobre cada obra cadastrada.

---

## Quando utilizar?

Utilize esse botão quando desejar:

* localizar uma obra;
* consultar informações específicas;
* revisar dados cadastrados;
* navegar pela coleção.

---

## O que acontece ao clicar?

Você será direcionado para a página **Biblioteca**.

Nenhuma alteração será realizada automaticamente.

---

# Fluxos

## Para que serve?

Abre o módulo responsável pela execução do Workflow da Manhwateca.

Esse é o local onde são executadas atividades como:

* organizar biblioteca;
* catalogar arquivos;
* resolver IDs;
* atualizar metadados;
* sincronizar o Notion.

---

## Quando utilizar?

Sempre que desejar executar alguma etapa do Workflow.

Na maioria das situações, esse botão será utilizado após consultar o painel **Próximo Passo Recomendado**.

---

## O que acontece ao clicar?

Você será direcionado para a página **Fluxos**.

Quando existir uma recomendação ativa, a aplicação poderá abrir diretamente a etapa correspondente.

---

# Recarregar Dashboard

## Para que serve?

Atualiza todas as informações exibidas no Dashboard.

Esse botão possui o mesmo comportamento do botão **Recarregar** disponível no Cabeçalho.

---

## Quando utilizar?

Recomenda-se utilizar essa ação quando:

* concluir uma etapa do Workflow;
* retornar da Biblioteca;
* alterar alguma configuração;
* desejar consultar informações mais recentes.

---

## O que acontece ao clicar?

A aplicação consulta novamente os dados e atualiza todos os componentes do Dashboard.

Nenhuma operação é executada na biblioteca.

---

# Configurações

## Para que serve?

Abre o módulo responsável pelas configurações da aplicação.

Nele você poderá revisar parâmetros relacionados ao ambiente e às integrações.

---

## Quando utilizar?

Utilize esse botão quando precisar:

* revisar configurações;
* corrigir problemas de integração;
* alterar diretórios monitorados;
* verificar parâmetros da aplicação.

---

## O que acontece ao clicar?

Você será direcionado para a página **Configurações**.

O Dashboard permanecerá inalterado até que você retorne e realize uma atualização.

---

# Como escolher a ação correta?

A tabela abaixo resume quando utilizar cada botão.

| Situação                               | Ação recomendada         |
| -------------------------------------- | ------------------------ |
| Quero consultar minhas obras           | **Biblioteca**           |
| Preciso executar uma etapa do Workflow | **Fluxos**               |
| Quero atualizar as informações da tela | **Recarregar Dashboard** |
| Preciso alterar alguma configuração    | **Configurações**        |

---

# Fluxo recomendado

Uma utilização comum acontece da seguinte forma.

```text id="ar003"
Abrir Dashboard

↓

Consultar Próximo Passo

↓

Selecionar Fluxos

↓

Executar atividade

↓

Retornar ao Dashboard

↓

Recarregar Dashboard
```

Esse fluxo mantém as informações sempre atualizadas.

---

# Ações Rápidas ou Menu Lateral?

Ambos permitem acessar os mesmos módulos.

A diferença está na praticidade.

## Menu lateral

Ideal quando você deseja navegar livremente entre diferentes áreas da aplicação.

---

## Ações Rápidas

Ideais quando você já sabe qual atividade precisa executar.

Elas reduzem a quantidade de cliques necessários.

---

# Situações comuns

## Acabei de resolver uma pendência

Utilize **Recarregar Dashboard**.

---

## Quero localizar uma obra

Utilize **Biblioteca**.

---

## Preciso iniciar a próxima etapa do Workflow

Utilize **Fluxos**.

---

## O Dashboard informou um problema de integração

Utilize **Configurações**.

---

# Boas práticas

Para aproveitar melhor esse componente:

* consulte primeiro o Dashboard;
* utilize as Ações Rápidas apenas depois de identificar a atividade necessária;
* prefira **Fluxos** quando existir uma **Ação Recomendada**;
* atualize o Dashboard ao retornar de outro módulo.

> **Dica:** As Ações Rápidas foram criadas para reduzir a navegação. Elas funcionam melhor quando utilizadas em conjunto com o painel **Próximo Passo Recomendado**.

---

# Perguntas Frequentes

### As Ações Rápidas executam tarefas automaticamente?

Não.

Elas apenas direcionam você para outro módulo da aplicação.

---

### Posso acessar os mesmos módulos pelo menu lateral?

Sim.

As Ações Rápidas são apenas atalhos.

---

### Existe diferença entre "Recarregar Dashboard" e o botão "Recarregar"?

Não.

Ambos possuem exatamente o mesmo comportamento.

---

### Posso personalizar as Ações Rápidas?

Não.

Os atalhos disponíveis fazem parte da interface padrão da Manhwateca.

---

# Resumo

Neste capítulo você aprendeu:

* o objetivo das Ações Rápidas;
* quando utilizar cada botão;
* para onde cada ação direciona;
* a diferença entre utilizar as Ações Rápidas e o menu lateral;
* como integrar esse componente ao fluxo normal de utilização da aplicação.
