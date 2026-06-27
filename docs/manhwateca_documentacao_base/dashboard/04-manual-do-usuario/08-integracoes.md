# Manual do Usuário — Dashboard

## 08 - Integrações

---

# Objetivo deste capítulo

Neste capítulo você aprenderá a interpretar corretamente o painel **Integrações** do Dashboard.

Esse componente informa se os principais serviços utilizados pela Manhwateca estão funcionando corretamente e ajuda a identificar rapidamente problemas de configuração ou indisponibilidade.

Ao final da leitura você será capaz de:

* entender o significado de cada integração;
* interpretar os diferentes estados apresentados;
* identificar quando um problema impede o funcionamento da aplicação;
* saber quando é necessário acessar o módulo **Configurações**.

---

# O que são Integrações?

A Manhwateca utiliza diferentes serviços para executar suas funcionalidades.

Esses serviços são chamados de **integrações**.

Cada integração possui uma responsabilidade específica e, em conjunto, permitem que a aplicação organize a biblioteca, consulte informações externas e sincronize dados.

O painel **Integrações** apresenta um resumo do estado atual desses serviços.

---

# Onde o painel está localizado?

O painel de Integrações é exibido abaixo das Pendências e antes do Workflow.

```text id="int001"
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
```

Essa posição permite verificar rapidamente se existe algum problema no ambiente antes de iniciar uma atividade.

---

# Estrutura do painel

Cada integração é apresentada em uma linha independente.

Exemplo:

```text id="int002"
┌──────────────────────────────────────────────┐
│ PostgreSQL       🟢 Operacional              │
│ Biblioteca       🟢 Acessível                │
│ MangaUpdates     🟡 Resposta lenta           │
│ Notion           🔴 Token inválido           │
└──────────────────────────────────────────────┘
```

Cada linha contém:

* nome da integração;
* indicador visual;
* descrição resumida do estado.

---

# Integrações monitoradas

O Dashboard acompanha quatro integrações principais.

## PostgreSQL

O PostgreSQL é responsável por armazenar o catálogo da biblioteca e outras informações utilizadas pela aplicação.

Sem ele, a Manhwateca não consegue consultar nem registrar dados.

### Quando tudo está funcionando

```text id="int003"
🟢 PostgreSQL
Operacional
```

### Quando existe um problema

```text id="int004"
🔴 PostgreSQL
Indisponível
```

Nessa situação, algumas funcionalidades poderão deixar de funcionar até que o problema seja corrigido.

---

## Biblioteca

Essa integração representa o acesso ao diretório onde suas obras estão armazenadas.

A Manhwateca precisa conseguir localizar esse diretório para organizar e catalogar os arquivos.

### Estado esperado

```text id="int005"
🟢 Biblioteca
Diretório acessível
```

### Possíveis problemas

* diretório removido;
* caminho alterado;
* permissões insuficientes;
* unidade desconectada.

Quando isso ocorrer, consulte o módulo **Configurações** para revisar o caminho configurado.

---

## MangaUpdates

O MangaUpdates fornece informações complementares sobre as obras cadastradas.

Esses dados são utilizados principalmente durante a atualização dos metadados.

### Estado esperado

```text id="int006"
🟢 MangaUpdates
Operacional
```

### Situações possíveis

```text id="int007"
🟡 Resposta lenta
```

ou

```text id="int008"
🔴 Indisponível
```

Uma indisponibilidade temporária normalmente afeta apenas a atualização dos metadados.

Sua biblioteca continua acessível.

---

## Notion

A integração com o Notion permite sincronizar informações entre a Manhwateca e sua base de dados.

### Estado esperado

```text id="int009"
🟢 Notion
Conectado
```

### Possíveis problemas

* token inválido;
* integração removida;
* permissões insuficientes;
* banco de dados não encontrado.

Quando isso ocorrer, será necessário revisar a configuração da integração.

---

# Como interpretar os indicadores

Cada integração apresenta um indicador visual.

## 🟢 Operacional

A integração está funcionando normalmente.

Nenhuma ação é necessária.

---

## 🟡 Atenção

A integração continua funcionando, porém existe alguma limitação.

Exemplos:

* resposta mais lenta que o normal;
* comunicação temporariamente instável.

Normalmente não é necessário interromper o uso da aplicação.

---

## 🔴 Erro

A integração não está disponível.

Dependendo do serviço afetado, algumas funcionalidades poderão ficar indisponíveis.

Nesses casos, recomenda-se verificar as **Configurações** antes de continuar utilizando a aplicação.

---

# Quando devo verificar o painel?

Consulte as Integrações sempre que:

* alguma funcionalidade deixar de funcionar;
* surgir uma pendência relacionada ao ambiente;
* ocorrer um erro inesperado;
* uma sincronização falhar;
* a atualização de metadados não puder ser concluída.

Na maioria das vezes, o painel ajudará a identificar rapidamente a origem do problema.

---

# Exemplos práticos

## Exemplo 1

```text id="int010"
🟢 PostgreSQL

🟢 Biblioteca

🟢 MangaUpdates

🟢 Notion
```

Todas as integrações estão operacionais.

A aplicação está pronta para uso.

---

## Exemplo 2

```text id="int011"
🔴 PostgreSQL
```

O banco de dados não está disponível.

Nesse cenário, algumas funcionalidades da aplicação poderão ficar indisponíveis.

---

## Exemplo 3

```text id="int012"
🔴 Notion
```

A sincronização com o Notion não poderá ser executada até que a configuração seja corrigida.

Entretanto, as demais funcionalidades da biblioteca continuarão disponíveis.

---

## Exemplo 4

```text id="int013"
🟡 MangaUpdates
Resposta lenta
```

A atualização dos metadados poderá demorar mais que o habitual.

Não é necessário interromper o uso da aplicação.

---

# O que fazer quando existir um erro?

Sempre siga esta sequência.

1. Leia a mensagem apresentada.
2. Identifique qual integração está com problema.
3. Acesse **Configurações**, quando indicado.
4. Corrija a configuração necessária.
5. Retorne ao Dashboard.
6. Clique em **Recarregar**.
7. Confirme se o estado voltou para **Operacional**.

---

# Boas práticas

Para evitar problemas com integrações:

* mantenha a configuração da biblioteca atualizada;
* não altere manualmente os diretórios monitorados sem atualizar a aplicação;
* revise periodicamente a configuração do Notion;
* consulte o painel antes de executar grandes atualizações.

> **Dica:** Um problema em uma integração nem sempre impede o uso da Manhwateca. Observe qual serviço foi afetado antes de interromper sua rotina.

---

# Perguntas Frequentes

### Todas as integrações precisam estar operacionais?

Depende da atividade que você pretende executar.

Por exemplo, um problema no Notion impede apenas a sincronização, enquanto um problema no PostgreSQL pode afetar diversas funcionalidades.

---

### Posso continuar utilizando a biblioteca se o MangaUpdates estiver indisponível?

Sim.

Você poderá consultar sua biblioteca normalmente.

Apenas operações que dependem desse serviço poderão ficar indisponíveis.

---

### O painel corrige problemas automaticamente?

Não.

Ele apenas informa o estado das integrações.

A correção deve ser realizada no módulo **Configurações**.

---

### Por que uma integração ficou amarela?

Isso normalmente indica uma situação temporária, como lentidão ou instabilidade.

Nem sempre representa um erro.

---

# Resumo

Neste capítulo você aprendeu:

* quais integrações são monitoradas pelo Dashboard;
* a função de cada serviço utilizado pela Manhwateca;
* como interpretar os indicadores de estado;
* quando consultar esse painel;
* como agir diante de problemas de infraestrutura;
* quando acessar o módulo **Configurações** para corrigir uma integração.
