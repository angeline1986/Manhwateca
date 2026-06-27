# Manual do Usuário — Dashboard

## 10 - Atualizando o Dashboard

---

# Objetivo deste capítulo

Neste capítulo você aprenderá quando e como atualizar as informações exibidas no Dashboard.

Embora grande parte dos dados seja carregada automaticamente ao abrir a aplicação, existem situações em que é recomendável solicitar uma nova atualização para garantir que as informações reflitam o estado mais recente da biblioteca.

Ao final deste capítulo você saberá:

* quando atualizar o Dashboard;
* quais informações são atualizadas;
* o que acontece durante esse processo;
* o que não é alterado pela atualização;
* como identificar se a atualização foi concluída com sucesso.

---

# Por que atualizar o Dashboard?

A Manhwateca apresenta um resumo da situação da biblioteca em um determinado momento.

Sempre que alguma informação muda — como a conclusão de uma etapa do Workflow ou uma alteração nas configurações — esse resumo precisa ser atualizado.

A atualização garante que os dados exibidos correspondam ao estado atual da aplicação.

---

# Quando devo atualizar?

Existem situações em que a atualização é recomendada.

## Após concluir uma etapa do Workflow

Esse é o caso mais comum.

Depois de finalizar uma atividade como:

* Organizar Biblioteca;
* Catalogar Arquivos;
* Resolver IDs;
* Atualizar Metadados;
* Sincronizar Notion;

retorne ao Dashboard e atualize as informações.

Isso permitirá visualizar imediatamente o novo estado da biblioteca.

---

## Após alterar Configurações

Sempre que alguma configuração importante for modificada, recomenda-se atualizar o Dashboard.

Assim você poderá confirmar rapidamente se o problema foi resolvido.

---

## Após retornar da Biblioteca

Caso tenha realizado alterações que influenciem a organização da coleção, uma atualização permitirá visualizar os novos indicadores.

---

## Quando existir dúvida sobre os dados

Se alguma informação parecer antiga ou inconsistente, utilize a atualização antes de tomar qualquer decisão.

Na maioria das situações isso será suficiente para sincronizar os dados exibidos.

---

# Como atualizar o Dashboard

O procedimento é simples.

1. Abra o Dashboard.
2. Localize o botão **Recarregar** no Cabeçalho ou utilize a ação **Recarregar Dashboard**.
3. Clique no botão.
4. Aguarde alguns instantes.
5. Verifique a nova data da **Última atualização**.

Após esse processo, todos os componentes da página utilizarão os dados mais recentes.

---

# O que acontece durante a atualização?

Quando você solicita uma atualização, a aplicação executa o seguinte fluxo:

```text id="upd001"
Usuário

↓

Clique em Recarregar

↓

Dashboard solicita novos dados

↓

Sistema atualiza informações

↓

Dashboard exibe os novos dados
```

Todo esse processo ocorre automaticamente.

Você não precisa fechar a aplicação nem atualizar a página do navegador.

---

# O que é atualizado?

Todos os componentes do Dashboard são atualizados ao mesmo tempo.

Isso inclui:

* Ação Recomendada;
* Métricas;
* Pendências;
* Integrações;
* Workflow;
* data da última atualização.

Dessa forma, todas as informações permanecem consistentes entre si.

---

# O que NÃO é atualizado?

É importante compreender que atualizar o Dashboard **não executa tarefas operacionais**.

A atualização **não**:

* organiza a biblioteca;
* cataloga arquivos;
* resolve IDs;
* consulta novos capítulos;
* atualiza metadados;
* sincroniza o Notion.

Ela apenas consulta o estado atual da aplicação.

---

# Como saber se a atualização terminou?

Após a atualização você poderá observar alguns sinais.

## A data foi alterada

O horário da **Última atualização** será modificado.

---

## As métricas mudaram

Caso alguma informação tenha sido alterada, os indicadores refletirão os novos valores.

---

## O Próximo Passo mudou

Se uma etapa do Workflow foi concluída, a recomendação poderá indicar uma nova atividade.

---

## As pendências desapareceram

Situações resolvidas deixam de aparecer automaticamente.

---

## O Workflow avançou

As etapas concluídas serão refletidas imediatamente no resumo do Workflow.

---

# Quando nenhuma informação muda

Nem sempre a atualização produzirá mudanças visíveis.

Isso significa apenas que nenhuma alteração ocorreu desde a última consulta.

Essa situação é perfeitamente normal.

---

# Se ocorrer um erro

Caso a atualização não possa ser concluída, o Dashboard continuará exibindo as informações anteriormente carregadas.

Você poderá tentar novamente após alguns instantes.

Se o problema persistir, consulte:

* o painel **Integrações**;
* o módulo **Configurações**;
* o capítulo **12 - Solução de Problemas**.

---

# Situações comuns

## Acabei de sincronizar o Notion

Atualize o Dashboard para confirmar que as pendências foram removidas.

---

## Resolvi todos os IDs

Atualize o Dashboard para verificar se o Workflow avançou para a próxima etapa.

---

## Corrigi uma configuração

Atualize o Dashboard para confirmar que a integração voltou ao estado operacional.

---

## Nada mudou após atualizar

Isso normalmente significa que não houve alterações desde a última consulta.

---

# Boas práticas

Para manter o Dashboard sempre confiável:

* atualize a página após concluir atividades importantes;
* evite atualizar repetidamente em poucos segundos;
* consulte a data da última atualização antes de interpretar os indicadores;
* utilize a atualização como etapa final após retornar de outro módulo.

> **Dica:** Atualizar o Dashboard é uma forma rápida de confirmar que uma operação foi concluída com sucesso. Antes de repetir uma tarefa, faça uma atualização e verifique se a interface já reflete a alteração esperada.

---

# Perguntas Frequentes

### Preciso atualizar sempre?

Não.

Entretanto, recomenda-se atualizar após concluir operações importantes.

---

### Atualizar o Dashboard consulta novamente todos os serviços?

O Dashboard solicita um novo conjunto de informações consolidadas ao sistema.

Você não precisa iniciar manualmente cada consulta.

---

### Posso continuar utilizando a aplicação durante a atualização?

Sim.

A atualização é rápida e não impede a navegação.

---

### Atualizar o Dashboard modifica minha biblioteca?

Não.

Ela apenas atualiza as informações apresentadas na tela.

---

# Resumo

Neste capítulo você aprendeu:

* quando atualizar o Dashboard;
* como realizar a atualização;
* quais informações são atualizadas;
* quais operações **não** são executadas durante esse processo;
* como verificar se a atualização foi concluída com sucesso;
* boas práticas para manter as informações sempre atualizadas.
