# Resolver IDs

> Documento: **05-resolver-ids.md**

---

# Objetivo

A etapa **Resolver IDs** é responsável por localizar e associar cada obra cadastrada na Manhwateca ao seu identificador oficial no **MangaUpdates**.

Esse identificador, conhecido como **MangaUpdates ID**, funciona como uma chave única que permite ao sistema recuperar informações oficiais da obra nas etapas seguintes do Workflow.

Sem um ID válido, a Manhwateca não consegue atualizar automaticamente os metadados nem sincronizar corretamente determinadas informações.

---

# O que é um ID?

Cada obra cadastrada no MangaUpdates possui um identificador exclusivo.

Exemplo:

```text
Solo Leveling

MangaUpdates ID:
151349
```

A partir desse identificador, a Manhwateca consegue consultar informações oficiais da obra sempre que necessário.

---

# Quando executar esta etapa?

A resolução de IDs deve ser executada quando:

* novas obras forem catalogadas;
* existirem obras sem ID;
* houver necessidade de corrigir associações incorretas;
* o Workflow completo estiver sendo executado.

No Workflow completo, essa etapa é iniciada automaticamente após **Catalogar Obras**.

---

# Como funciona a resolução?

Durante esta etapa, a Manhwateca:

1. identifica todas as obras sem MangaUpdates ID;
2. pesquisa possíveis correspondências;
3. compara os resultados encontrados;
4. seleciona a melhor correspondência;
5. registra o ID encontrado.

Sempre que possível, esse processo acontece automaticamente.

---

# Como iniciar

### Workflow completo

1. Acesse **Fluxos**.
2. Clique em **Executar Workflow**.

A etapa será iniciada automaticamente no momento adequado.

---

### Apenas Resolver IDs

Caso deseje executar somente esta etapa:

1. Localize **Resolver IDs**.
2. Clique em **Executar**.

A Manhwateca verificará automaticamente se existem obras elegíveis para processamento.

---

# Acompanhando a execução

Durante o processamento, a interface poderá apresentar informações semelhantes às seguintes:

```text
Resolvendo IDs

█████████░░░░░

72%

183 de 254 obras

Tempo: 01m53s
```

Esses dados são atualizados continuamente durante a execução.

---

# Possíveis resultados

## ID localizado

Exemplo:

```text
Omniscient Reader

ID encontrado.

151867
```

A obra seguirá automaticamente para a etapa **Atualizar Metadados**.

---

## Obra já possui ID

Exemplo:

```text
Solo Leveling

ID já cadastrado.
```

Nenhuma nova pesquisa será realizada.

---

## Nenhuma correspondência encontrada

Exemplo:

```text
A obra não foi localizada no MangaUpdates.
```

Essa obra permanecerá pendente até uma nova tentativa ou intervenção manual.

---

## Correspondências múltiplas

Quando mais de uma obra corresponder ao mesmo título, a Manhwateca poderá identificar uma situação ambígua.

Exemplo:

```text
Foram encontradas múltiplas correspondências.

Revisão necessária.
```

Nesses casos, a obra será marcada para revisão.

---

# Mensagens exibidas

Durante a resolução de IDs, podem aparecer mensagens como:

* "Pesquisando obra..."
* "Correspondência encontrada."
* "Nenhuma correspondência localizada."
* "ID associado com sucesso."
* "Resolução concluída."

---

# Alertas comuns

Alguns alertas exigem atenção.

Exemplos:

* título muito genérico;
* múltiplos resultados encontrados;
* obra inexistente no MangaUpdates;
* falha temporária de comunicação.

> **Importante**
>
> Uma obra sem ID continuará cadastrada na Manhwateca. Apenas não poderá receber atualizações automáticas de metadados enquanto permanecer sem uma associação válida.

---

# Posso executar novamente?

Sim.

Sempre que desejar, você poderá executar novamente apenas a etapa **Resolver IDs**.

Isso é útil quando:

* novas obras forem adicionadas;
* o MangaUpdates passar a possuir a obra;
* ocorrer uma falha temporária durante a pesquisa.

A etapa será executada apenas para as obras elegíveis.

---

# O que acontece depois?

Após concluir a resolução de IDs, a próxima etapa será iniciada automaticamente.

```text
Resolver IDs

↓

Atualizar Metadados
```

A partir desse momento, a Manhwateca utilizará os IDs encontrados para recuperar informações oficiais das obras.

---

# Boas práticas

Para aumentar a taxa de sucesso na resolução automática:

* mantenha os nomes das obras padronizados;
* evite abreviações excessivas;
* execute a catalogação antes da resolução;
* revise periodicamente as obras que permanecerem sem ID.

---

# Perguntas frequentes

### Todas as obras possuem MangaUpdates ID?

Não.

Algumas obras podem não estar cadastradas no MangaUpdates.

---

### Posso usar a Manhwateca sem resolver IDs?

Sim.

Entretanto, recursos como atualização automática de metadados dependerão de um ID válido.

---

### Uma obra sem ID impede o Workflow?

Não.

O Workflow continuará normalmente.

As obras sem ID apenas serão ignoradas nas etapas que dependem dessa informação.

---

### Posso corrigir um ID posteriormente?

Sim.

Após corrigir ou associar um ID, basta executar novamente as etapas **Resolver IDs** ou **Atualizar Metadados** para que a obra seja atualizada.

---

# Próximo passo

Após a resolução dos IDs, a próxima etapa será **Atualizar Metadados**, responsável por consultar o MangaUpdates e atualizar automaticamente informações como título, autores, artistas, gêneros, status e outros dados da obra.

---

# Conclusão

A etapa **Resolver IDs** conecta as obras cadastradas na Manhwateca às suas referências oficiais no MangaUpdates. Essa associação permite automatizar a obtenção de metadados e reduz significativamente a necessidade de manutenção manual da biblioteca, tornando as etapas seguintes do Workflow mais precisas e eficientes.
