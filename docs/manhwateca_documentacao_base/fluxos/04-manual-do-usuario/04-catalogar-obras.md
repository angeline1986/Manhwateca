# Catalogar Obras

> Documento: **04-catalogar-obras.md**

---

# Objetivo

A etapa **Catalogar Obras** é responsável por transformar as obras encontradas durante a organização da biblioteca em registros da Manhwateca.

Enquanto a etapa anterior apenas analisa a estrutura física da biblioteca, esta etapa registra e atualiza as informações necessárias para que cada obra possa ser gerenciada pela aplicação.

Após sua conclusão, todas as obras elegíveis passam a fazer parte da base de dados da Manhwateca.

---

# Quando executar esta etapa?

A catalogação deve ser executada sempre que:

* novas obras forem adicionadas à biblioteca;
* obras forem removidas;
* pastas forem renomeadas;
* a organização da biblioteca identificar alterações.

Quando o Workflow completo é executado, esta etapa é iniciada automaticamente após **Organizar Biblioteca**.

---

# O que acontece durante a catalogação?

Nesta etapa, a Manhwateca:

* identifica todas as obras organizadas;
* verifica se cada obra já existe no banco de dados;
* cria registros para novas obras;
* atualiza registros existentes quando necessário;
* registra informações básicas para as próximas etapas do Workflow.

Essa etapa não consulta serviços externos, como MangaUpdates ou Notion.

---

# Como iniciar

### Executando o Workflow completo

1. Acesse a página **Fluxos**.
2. Clique em **Executar Workflow**.

A etapa será iniciada automaticamente após a organização da biblioteca.

---

### Executando apenas a catalogação

Caso necessário:

1. Localize o cartão **Catalogar Obras**.
2. Clique em **Executar**.

A Manhwateca verificará se os pré-requisitos da etapa foram atendidos antes de iniciar o processamento.

---

# Acompanhando a execução

Durante a catalogação, o painel de execução exibirá informações semelhantes às seguintes:

```text
Catalogando Obras

████████░░░░░░

58%

396 de 684 obras

Tempo: 02m14s
```

Essas informações são atualizadas automaticamente durante o processamento.

---

# O que está sendo catalogado?

Para cada obra encontrada, a Manhwateca realiza verificações como:

* existência de registro anterior;
* nome principal da obra;
* localização na biblioteca;
* status de catalogação;
* informações mínimas obrigatórias.

Ao final, cada obra estará identificada como:

* nova;
* atualizada;
* inalterada;
* ignorada.

---

# Possíveis resultados

## Novas obras

Exemplo:

```text
18 novas obras catalogadas.
```

Essas obras seguirão normalmente para a etapa **Resolver IDs**.

---

## Obras já existentes

Exemplo:

```text
642 obras já catalogadas.
```

Os registros existentes serão reutilizados sempre que possível.

---

## Obras atualizadas

Exemplo:

```text
24 registros atualizados.
```

Isso normalmente ocorre quando houve alteração na estrutura da biblioteca.

---

## Nenhuma alteração

Exemplo:

```text
Nenhuma nova obra encontrada.
```

Mesmo sem alterações, o Workflow continuará normalmente.

---

# Mensagens exibidas

Durante a execução podem aparecer mensagens como:

* "Catalogando obras..."
* "Criando registros..."
* "Atualizando informações..."
* "Catalogação concluída."

Essas mensagens acompanham o andamento do processamento.

---

# Alertas comuns

Algumas situações podem gerar alertas.

Exemplos:

* obra duplicada;
* informações incompletas;
* estrutura inconsistente;
* registro não pôde ser atualizado.

> **Importante**
>
> Um alerta não significa que a catalogação foi interrompida. Na maioria dos casos, apenas algumas obras exigirão revisão posterior.

---

# O que acontece depois?

Ao concluir a catalogação, a próxima etapa será iniciada automaticamente.

```text
Catalogar Obras

↓

Resolver IDs
```

A partir desse momento, a Manhwateca começará a procurar os identificadores oficiais das obras.

---

# Posso cancelar?

Sim.

Caso clique em **Cancelar Workflow**, a aplicação concluirá a operação atualmente em execução antes de interromper o processamento.

Os registros já catalogados permanecerão salvos.

---

# Boas práticas

Para manter uma catalogação consistente:

* evite alterar a estrutura da biblioteca durante a execução;
* utilize nomes padronizados para as obras;
* execute primeiro a etapa **Organizar Biblioteca** caso tenha feito alterações recentes;
* revise periodicamente os alertas apresentados ao final do Workflow.

---

# Perguntas frequentes

### A catalogação altera meus arquivos?

Não.

Ela apenas cria ou atualiza registros internos da Manhwateca.

Nenhum arquivo da biblioteca é modificado.

---

### Preciso catalogar todas as obras novamente?

Não.

A Manhwateca identifica automaticamente quais obras precisam ser catalogadas ou atualizadas.

---

### Posso executar esta etapa isoladamente?

Sim.

Desde que a organização da biblioteca tenha sido executada anteriormente e os pré-requisitos estejam atendidos.

---

# Próximo passo

Após a catalogação, a próxima etapa será **Resolver IDs**, responsável por localizar automaticamente os identificadores oficiais de cada obra no MangaUpdates.

---

# Conclusão

A etapa **Catalogar Obras** cria a base de informações utilizada por todo o restante do Workflow. Ao registrar novas obras e manter os registros existentes atualizados, ela garante que as etapas seguintes trabalhem sobre dados consistentes e preparados para receber metadados e sincronizações externas.
