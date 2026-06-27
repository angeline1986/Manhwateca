# Manual do Usuário — Dashboard

## 06 - Pendências

---

# Objetivo deste capítulo

Neste capítulo você aprenderá a interpretar corretamente o painel **Pendências**, um dos componentes mais importantes do Dashboard.

Ele foi criado para informar tudo o que exige sua atenção antes que algum problema afete a organização da biblioteca ou impeça a continuidade do Workflow.

Ao final deste capítulo você saberá:

* quando uma pendência exige ação imediata;
* como interpretar os diferentes níveis de prioridade;
* para onde cada pendência direciona;
* quando uma pendência pode ser ignorada;
* como resolver as situações mais comuns.

---

# O que são Pendências?

Pendências são situações identificadas pela Manhwateca que ainda precisam ser resolvidas.

Uma pendência não representa necessariamente um erro.

Na maioria das vezes, ela apenas indica que existe alguma atividade aguardando sua intervenção.

Exemplos:

* novas obras ainda não catalogadas;
* obras sem identificação;
* metadados desatualizados;
* sincronizações pendentes;
* problemas de configuração.

O objetivo do painel é impedir que essas situações passem despercebidas.

---

# Onde o painel está localizado?

O painel de Pendências é exibido na área central do Dashboard.

Ele aparece logo após as Métricas e antes do resumo do Workflow.

```text
Cabeçalho

↓

Próximo Passo

↓

Métricas

↓

Pendências

↓

Workflow
```

Essa posição foi escolhida para que você visualize os problemas antes de iniciar qualquer atividade.

---

# Estrutura do painel

Cada pendência possui uma estrutura semelhante.

```text
┌────────────────────────────────────────────────────────────┐
│ 🔴 Resolver 8 obras sem ID                                 │
│                                                            │
│ Algumas obras ainda não possuem identificação confirmada.  │
│                                                            │
│                           [Abrir Fluxos]                   │
└────────────────────────────────────────────────────────────┘
```

Cada item contém:

* indicador de prioridade;
* título da pendência;
* descrição resumida;
* botão para acessar o módulo responsável.

---

# Como interpretar uma pendência

Sempre leia a pendência na seguinte ordem:

## 1. Prioridade

Observe o indicador visual.

Ele informa a gravidade da situação.

---

## 2. Título

O título resume o problema encontrado.

Exemplo:

```text
Resolver 8 obras sem ID
```

---

## 3. Descrição

A descrição explica o motivo da pendência e qual será o impacto caso ela permaneça sem resolução.

---

## 4. Botão de ação

O botão leva diretamente ao módulo onde aquela situação pode ser resolvida.

O Dashboard apenas orienta.

A correção ocorre em outro módulo.

---

# Níveis de prioridade

As pendências são classificadas por prioridade.

## 🔴 Alta prioridade

Exigem atenção imediata.

Normalmente impedem o avanço do Workflow.

Exemplos:

* obras sem ID;
* banco de dados indisponível;
* biblioteca inacessível.

Sempre resolva essas situações antes de iniciar novas atividades.

---

## 🟡 Média prioridade

Não impedem o funcionamento da aplicação, mas podem gerar inconsistências ou atrasar o processo.

Exemplos:

* metadados desatualizados;
* sincronizações pendentes;
* capítulos novos aguardando atualização.

Recomenda-se resolvê-las assim que possível.

---

## 🔵 Baixa prioridade

Representam informações ou recomendações.

Normalmente não exigem ação imediata.

Podem ser resolvidas posteriormente.

---

# Principais pendências

## Organizar Biblioteca

Significa que a biblioteca ainda precisa ser preparada para utilização.

Normalmente ocorre após configurar um novo diretório.

### O que fazer?

Clique em **Abrir Fluxos** e execute a etapa **Organizar Biblioteca**.

---

## Catalogar Arquivos

Indica que novos arquivos foram encontrados e ainda não fazem parte do catálogo.

### O que fazer?

Acesse o módulo **Fluxos** e execute **Catalogar Arquivos**.

---

## Resolver IDs

Essa é uma das pendências mais comuns.

Ela indica que algumas obras ainda não possuem identificação confirmada.

Enquanto essa etapa não for concluída, nem todas as funcionalidades estarão disponíveis.

### O que fazer?

Execute a etapa **Resolver IDs**.

---

## Atualizar Metadados

Indica que existem informações desatualizadas.

### O que fazer?

Execute a atualização dos metadados.

---

## Sincronizar Notion

Existem alterações locais que ainda não foram enviadas para o Notion.

### O que fazer?

Execute a sincronização.

---

# Pendências de infraestrutura

Algumas pendências não estão relacionadas ao Workflow.

Elas indicam problemas no ambiente da aplicação.

Exemplos:

* PostgreSQL indisponível;
* biblioteca não encontrada;
* token do Notion inválido;
* diretório inacessível.

Nesses casos, o botão normalmente direcionará para **Configurações**.

---

# Quando devo resolver uma pendência?

Na maioria das situações, a própria aplicação responde essa pergunta.

Se uma pendência aparecer como **Próximo Passo Recomendado**, ela deve ser resolvida antes das demais.

Caso contrário, siga esta ordem:

1. Bloqueios do ambiente.
2. Resolver IDs.
3. Atualizar Metadados.
4. Sincronizar Notion.
5. Demais recomendações.

---

# O que acontece após resolver uma pendência?

Após concluir a atividade correspondente:

1. Retorne ao Dashboard.
2. Clique em **Recarregar**.
3. Aguarde a atualização.

Se a operação tiver sido concluída corretamente, a pendência desaparecerá automaticamente.

Caso contrário, ela permanecerá visível até que a situação seja resolvida.

---

# Posso ignorar uma pendência?

Depende.

Algumas pendências são apenas recomendações.

Outras impedem o funcionamento correto da aplicação.

Como regra geral:

* pendências vermelhas não devem ser ignoradas;
* pendências amarelas devem ser resolvidas em breve;
* pendências informativas podem ser tratadas posteriormente.

---

# Situações comuns

## A mesma pendência continua aparecendo

Isso normalmente significa que a atividade correspondente ainda não foi concluída.

Verifique se a operação terminou com sucesso e atualize o Dashboard.

---

## Uma nova pendência apareceu

Isso é esperado.

Sempre que a situação da biblioteca muda, novas pendências podem ser identificadas.

---

## A pendência desapareceu

Significa que a situação foi resolvida ou deixou de exigir intervenção.

---

## Não existem pendências

Essa é a situação ideal.

O painel exibirá uma mensagem semelhante a:

```text
Nenhuma pendência encontrada.

Sua biblioteca está em dia.
```

---

# Boas práticas

Para utilizar corretamente esse painel:

* consulte-o sempre após verificar as Métricas;
* resolva primeiro as pendências de maior prioridade;
* utilize o botão **Abrir Fluxos** para acessar diretamente a etapa correta;
* atualize o Dashboard após concluir cada atividade.

> **Dica:** Não tente resolver todas as pendências ao mesmo tempo. Siga a ordem recomendada pelo Dashboard e avance uma etapa por vez. Isso reduz erros e facilita o acompanhamento do Workflow.

---

# Perguntas Frequentes

### As pendências são erros?

Nem sempre.

Muitas delas representam apenas atividades que ainda precisam ser realizadas.

---

### Posso remover uma pendência manualmente?

Não.

Ela desaparecerá automaticamente quando a situação correspondente for resolvida.

---

### Por que uma pendência voltou?

Pode ter surgido uma nova situação semelhante.

Por exemplo, após adicionar novas obras, a pendência **Resolver IDs** poderá reaparecer.

Isso faz parte do funcionamento normal da aplicação.

---

### O Dashboard resolve pendências automaticamente?

Não.

Ele apenas identifica e informa quais ações precisam ser realizadas.

---

# Resumo

Neste capítulo você aprendeu:

* o que são pendências;
* como interpretar cada item do painel;
* quais são os níveis de prioridade;
* como resolver as principais situações encontradas;
* quando uma pendência exige atenção imediata;
* como acompanhar a resolução das atividades através do Dashboard.
