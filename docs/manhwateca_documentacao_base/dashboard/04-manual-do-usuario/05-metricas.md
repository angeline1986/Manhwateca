# Manual do Usuário — Dashboard

## 05 - Métricas

---

# Objetivo deste capítulo

Neste capítulo você aprenderá a interpretar corretamente as **Métricas** exibidas no Dashboard.

Esses indicadores apresentam um resumo da situação atual da sua biblioteca e ajudam a identificar rapidamente o que mudou desde a última atualização.

Embora sejam apresentados como simples números, cada métrica possui um significado específico e pode indicar diferentes ações necessárias.

---

# O que são as Métricas?

As Métricas são indicadores que resumem o estado da biblioteca.

Em vez de consultar várias telas para descobrir quantas obras existem, quantos capítulos novos foram encontrados ou quantas pendências ainda permanecem, essas informações são apresentadas de forma consolidada no Dashboard.

O objetivo é fornecer uma visão geral da biblioteca em poucos segundos.

---

# Onde as Métricas estão localizadas?

As Métricas aparecem logo abaixo do painel **Próximo Passo Recomendado**.

```text id="mtr001"
Cabeçalho

↓

Próximo Passo Recomendado

↓

Métricas

↓

Pendências
```

Essa posição permite que você consulte rapidamente os principais indicadores antes de analisar informações mais detalhadas.

---

# Conhecendo os quatro indicadores

O Dashboard apresenta quatro métricas principais.

```text id="mtr002"
┌────────────┬────────────┬────────────┬────────────┐
│ Obras      │ Novos Caps │ Sem ID     │ Notion     │
│ 347        │ 23         │ 8          │ 14         │
└────────────┴────────────┴────────────┴────────────┘
```

Cada indicador possui um propósito específico.

---

# Total de Obras

Este indicador informa quantas obras estão atualmente cadastradas na biblioteca.

Exemplo:

```text id="mtr003"
347
Obras cadastradas
```

Esse número representa o tamanho atual da sua coleção registrada na Manhwateca.

Ele aumenta sempre que novas obras são catalogadas e diminui apenas quando uma obra é removida da biblioteca.

---

## Quando observar essa métrica?

Ela é útil para:

* acompanhar o crescimento da coleção;
* confirmar se novas obras foram catalogadas corretamente;
* verificar rapidamente o tamanho da biblioteca.

---

# Novos Capítulos

Este indicador informa quantas obras possuem capítulos novos disponíveis desde a última atualização dos metadados.

Exemplo:

```text id="mtr004"
23
Novos capítulos
```

Esse número representa oportunidades de leitura.

Quanto maior o valor, maior a quantidade de obras que receberam atualizações.

---

## O que esse número significa?

Ele **não** representa o número total de capítulos.

Ele representa a quantidade de obras que possuem novidades.

Por exemplo:

| Situação                               | Resultado        |
| -------------------------------------- | ---------------- |
| Uma obra recebeu cinco capítulos novos | Conta como **1** |
| Cinco obras receberam um capítulo novo | Conta como **5** |

---

## Quando consultar essa métrica?

Principalmente quando você deseja descobrir rapidamente se existem novidades para leitura.

---

# Obras sem ID

Esse indicador informa quantas obras ainda não possuem identificação confirmada.

Exemplo:

```text id="mtr005"
8
Obras sem ID
```

Uma obra sem ID normalmente ainda não pode ter seus metadados atualizados corretamente.

Enquanto existirem obras nessa condição, parte do Workflow permanecerá incompleta.

---

## O que devo fazer?

Quando esse número for maior que zero, recomenda-se executar a etapa **Resolver IDs**.

Na maioria das vezes, o próprio Dashboard apresentará essa atividade como **Próximo Passo Recomendado**.

---

# Pendências do Notion

Essa métrica informa quantas alterações ainda aguardam sincronização.

Exemplo:

```text id="mtr006"
14
Pendências
```

Isso significa que existem informações modificadas na Manhwateca que ainda não foram enviadas ao Notion.

---

## Quando devo me preocupar?

Se esse número permanecer elevado por muito tempo.

Normalmente, após executar a sincronização, ele deverá diminuir ou retornar para zero.

---

# Como interpretar as métricas em conjunto?

As métricas tornam-se mais úteis quando analisadas em conjunto.

Exemplo:

| Obras | Novos Capítulos | Sem ID | Notion |
| ----- | --------------- | ------ | ------ |
| 347   | 23              | 8      | 14     |

Nesse cenário é possível concluir que:

* a biblioteca possui 347 obras;
* existem novidades para leitura;
* algumas obras ainda precisam ser identificadas;
* alterações aguardam sincronização.

O Dashboard utilizará essas informações para determinar a **Ação Recomendada**.

---

# As métricas mudam automaticamente?

As métricas são atualizadas quando:

* o Dashboard é aberto;
* você utiliza o botão **Recarregar**;
* retorna de uma operação concluída em outro módulo.

Se alguma informação parecer desatualizada, utilize **Recarregar** antes de tirar conclusões.

---

# O que acontece quando uma métrica vale zero?

Zero não significa necessariamente que existe um problema.

Veja alguns exemplos.

## Total de Obras

Uma biblioteca recém-configurada pode apresentar:

```text id="mtr007"
0
Obras cadastradas
```

Isso apenas indica que ainda não existem obras registradas.

---

## Novos Capítulos

```text id="mtr008"
0
Novos capítulos
```

Nesse caso, nenhuma obra recebeu atualizações desde a última consulta.

---

## Obras sem ID

```text id="mtr009"
0
Obras sem ID
```

Essa é a situação ideal.

Todas as obras possuem identificação confirmada.

---

## Pendências do Notion

```text id="mtr010"
0
Pendências
```

Também representa a situação ideal.

Todas as alterações foram sincronizadas.

---

# Situações comuns

## O número de obras aumentou

Provavelmente novas obras foram catalogadas.

---

## O número de capítulos aumentou

Existem novas leituras disponíveis.

---

## O número de obras sem ID aumentou

Novas obras foram adicionadas e ainda precisam ser identificadas.

---

## O número de pendências aumentou

Existem alterações aguardando sincronização.

---

# Boas práticas

Para interpretar corretamente as métricas:

* observe os quatro indicadores em conjunto;
* não utilize apenas um número para tomar decisões;
* consulte sempre a **Ação Recomendada** para entender qual métrica exige atenção;
* atualize o Dashboard antes de analisar mudanças recentes.

> **Dica:** As métricas mostram "o que está acontecendo". Para descobrir "o que fazer", consulte o painel **Próximo Passo Recomendado**.

---

# Perguntas Frequentes

### As métricas atualizam automaticamente?

Sim, durante o carregamento do Dashboard e sempre que você atualizar a página utilizando **Recarregar**.

---

### Posso clicar nas métricas?

Não.

Os indicadores possuem finalidade informativa.

Para realizar alguma ação, utilize o módulo correspondente ou siga a **Ação Recomendada**.

---

### Um número alto significa que existe um problema?

Nem sempre.

Um grande número de obras cadastradas é esperado.

Já um grande número de obras sem ID ou de pendências pode indicar que algumas etapas do Workflow ainda precisam ser concluídas.

---

# Resumo

Neste capítulo você aprendeu:

* o significado de cada uma das quatro métricas;
* como interpretar os indicadores em conjunto;
* quando um valor merece atenção;
* quando um valor igual a zero representa uma situação normal;
* como utilizar essas informações para acompanhar o estado geral da biblioteca.
