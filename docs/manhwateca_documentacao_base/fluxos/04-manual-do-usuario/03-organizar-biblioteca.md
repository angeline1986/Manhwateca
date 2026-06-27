# Organizar Biblioteca

> Documento: **03-organizar-biblioteca.md**

---

# Objetivo

A etapa **Organizar Biblioteca** é a primeira fase do Workflow da Manhwateca.

Seu objetivo é analisar a estrutura física da biblioteca, identificar alterações realizadas desde a última execução e preparar todas as obras para as etapas seguintes do processamento.

Nenhuma informação é enviada ao MangaUpdates ou ao Notion nesta etapa. O foco é exclusivamente validar e organizar a biblioteca local.

---

# Quando executar esta etapa?

Execute esta etapa sempre que houver alterações na estrutura da biblioteca, como:

* inclusão de novas obras;
* remoção de obras existentes;
* renomeação de pastas;
* reorganização de diretórios;
* movimentação de arquivos entre categorias.

> **Dica**
>
> Se você não tem certeza se houve alguma alteração, pode executar o Workflow completo. A Manhwateca processará apenas o que for necessário.

---

# O que acontece durante a organização?

Ao iniciar esta etapa, a Manhwateca realiza automaticamente diversas verificações.

Entre elas:

* localiza a biblioteca configurada;
* verifica se os diretórios estão acessíveis;
* percorre todas as pastas;
* identifica novas obras;
* detecta obras removidas;
* identifica alterações de estrutura;
* prepara os dados para a catalogação.

Todo esse processo ocorre automaticamente.

---

# Como iniciar

1. Acesse a página **Fluxos**.
2. Localize a etapa **Organizar Biblioteca**.
3. Clique em **Executar** ou **Executar Workflow**.

Após o início, o sistema começará a analisar sua biblioteca.

---

# Acompanhando a execução

Durante a organização, a interface exibirá informações semelhantes às seguintes:

```text
Organizando Biblioteca

██████████░░░░░░

64%

418 de 651 pastas analisadas

Tempo: 01m42s
```

Esses números são atualizados automaticamente.

---

# O que está sendo analisado?

Durante esta etapa, a Manhwateca verifica diversos aspectos da biblioteca.

Exemplos:

* existência das pastas;
* nomes das obras;
* estrutura dos diretórios;
* alterações desde a última execução;
* possíveis inconsistências.

Essas verificações permitem que apenas as obras realmente necessárias sejam processadas nas etapas seguintes.

---

# Possíveis resultados

Ao término da organização, diferentes situações podem ser encontradas.

## Nenhuma alteração

Exemplo:

```text
Biblioteca organizada.

Nenhuma alteração encontrada.
```

Nesse caso, o Workflow continuará normalmente.

---

## Novas obras encontradas

Exemplo:

```text
12 novas obras identificadas.
```

Essas obras serão catalogadas automaticamente na próxima etapa.

---

## Obras removidas

Exemplo:

```text
5 obras não foram localizadas.
```

Essas informações serão registradas para posterior tratamento pela aplicação.

---

## Alterações estruturais

Exemplo:

```text
18 obras apresentaram alterações de localização.
```

Essas alterações serão refletidas automaticamente nas etapas seguintes.

---

# Mensagens que podem aparecer

Durante a execução você poderá visualizar mensagens como:

* "Analisando diretórios..."
* "Verificando estrutura da biblioteca..."
* "Novas obras identificadas."
* "Organização concluída."

Essas mensagens servem apenas para informar o andamento do processamento.

---

# Alertas comuns

Alguns alertas podem exigir sua atenção.

Exemplos:

* diretório não encontrado;
* biblioteca inacessível;
* permissão insuficiente;
* estrutura inconsistente.

> **Importante**
>
> Quando um alerta impedir a organização da biblioteca, as etapas seguintes poderão não ser executadas.

---

# Posso interromper essa etapa?

Sim.

Enquanto a organização estiver em andamento, você poderá clicar em **Cancelar Workflow**.

A Manhwateca concluirá a operação em andamento antes de interromper o processamento, preservando as informações já registradas.

---

# O que acontece depois?

Quando a organização terminar com sucesso, a próxima etapa será iniciada automaticamente.

```text
Organizar Biblioteca

↓

Catalogar Obras
```

Você não precisa iniciar manualmente a próxima etapa quando estiver executando o Workflow completo.

---

# Boas práticas

Para obter melhores resultados:

* mantenha a estrutura da biblioteca organizada;
* evite mover pastas durante o processamento;
* aguarde a conclusão da etapa antes de realizar novas alterações;
* execute novamente a organização após mudanças significativas.

Essas práticas reduzem inconsistências e agilizam o processamento.

---

# Perguntas frequentes

### Preciso executar esta etapa sempre?

Sempre que houver alterações na biblioteca, sim.

Caso contrário, o Workflow completo também poderá ser utilizado normalmente.

---

### Esta etapa altera minhas obras?

Não.

Ela apenas analisa e organiza as informações utilizadas pela Manhwateca.

Nenhum arquivo da sua biblioteca é modificado.

---

### Posso continuar usando a aplicação?

Sim.

Você pode navegar para outros módulos enquanto a organização continua sendo executada.

---

# Próximo passo

Após concluir a organização da biblioteca, a Manhwateca iniciará a etapa **Catalogar Obras**, responsável por registrar novas obras e atualizar os registros existentes no banco de dados.

---

# Conclusão

A etapa **Organizar Biblioteca** prepara todo o ambiente para o restante do Workflow. Ao identificar alterações na estrutura da biblioteca e validar os diretórios configurados, ela garante que apenas informações consistentes avancem para as etapas seguintes, reduzindo erros e tornando o processamento mais eficiente.
