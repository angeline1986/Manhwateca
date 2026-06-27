# Sincronizar com Notion

> Documento: **07-sincronizar-com-notion.md**

---

# Objetivo

A etapa **Sincronizar com Notion** é a última fase do Workflow da Manhwateca.

Seu objetivo é refletir no banco de dados do **Notion** todas as alterações realizadas durante as etapas anteriores, garantindo que a biblioteca local e a base do Notion permaneçam sincronizadas.

Ao término desta etapa, o Workflow estará concluído.

---

# O que é sincronizado?

Durante esta etapa, a Manhwateca compara as informações armazenadas no banco de dados local com as existentes no Notion.

Dependendo da situação de cada obra, o sistema poderá:

* criar novas páginas;
* atualizar páginas existentes;
* preencher propriedades vazias;
* atualizar propriedades alteradas;
* registrar a data da última sincronização.

A sincronização ocorre automaticamente, sem necessidade de edição manual.

---

# Quando executar esta etapa?

A sincronização deve ser executada quando:

* novas obras forem adicionadas;
* metadados forem atualizados;
* informações forem alteradas na Manhwateca;
* desejar garantir que o Notion reflita o estado atual da biblioteca;
* executar o Workflow completo.

No Workflow completo, esta é sempre a última etapa.

---

# Como funciona?

Para cada obra elegível, a Manhwateca executa o seguinte processo:

1. localiza a página correspondente no Notion;
2. verifica as propriedades existentes;
3. identifica diferenças entre o banco local e o Notion;
4. cria ou atualiza a página quando necessário;
5. registra o resultado da sincronização.

Esse processo é repetido automaticamente para todas as obras elegíveis.

---

# Como iniciar

### Workflow completo

1. Acesse **Fluxos**.
2. Clique em **Executar Workflow**.

A sincronização ocorrerá automaticamente ao final das demais etapas.

---

### Executando apenas a sincronização

Caso deseje apenas atualizar o Notion:

1. Localize **Sincronizar Notion**.
2. Clique em **Executar**.

A Manhwateca sincronizará apenas os registros elegíveis.

---

# Acompanhando a execução

Durante a sincronização, a interface exibirá informações semelhantes às seguintes:

```text
Sincronizando com Notion

████████████░░

82%

541 de 661 páginas

Tempo: 04m03s
```

Esses indicadores são atualizados automaticamente durante todo o processamento.

---

# Possíveis resultados

## Página criada

Exemplo:

```text
The Beginning After The End

Página criada no Notion.
```

---

## Página atualizada

Exemplo:

```text
Omniscient Reader

Propriedades atualizadas.
```

---

## Nenhuma alteração

Exemplo:

```text
Solo Leveling

Nenhuma atualização necessária.
```

Quando não houver diferenças entre o banco local e o Notion, nenhuma alteração será enviada.

---

## Página não localizada

Exemplo:

```text
Página não encontrada.

Uma nova página será criada.
```

A obra continuará elegível para sincronização.

---

# O que normalmente é atualizado?

Entre as propriedades que podem ser sincronizadas estão:

* título;
* capa;
* autores;
* artistas;
* gêneros;
* status;
* capítulos;
* progresso de leitura;
* avaliação;
* favoritos;
* datas de atualização;
* demais propriedades configuradas na base do Notion.

A lista exata depende da configuração utilizada na Manhwateca.

---

# Mensagens exibidas

Durante a sincronização poderão aparecer mensagens como:

* "Consultando Notion..."
* "Criando página..."
* "Atualizando propriedades..."
* "Sincronização concluída."

Essas mensagens informam o andamento da etapa.

---

# Alertas comuns

Algumas situações podem exigir atenção.

Exemplos:

* banco do Notion indisponível;
* token inválido;
* limite temporário da API;
* página removida manualmente;
* propriedade inexistente na base do Notion.

> **Importante**
>
> Um alerta normalmente afeta apenas as obras envolvidas. As demais continuam sendo sincronizadas normalmente.

---

# Posso executar novamente?

Sim.

É comum executar novamente esta etapa quando:

* houver alterações recentes no banco local;
* ocorrer falha temporária da API;
* novas propriedades forem adicionadas ao Notion;
* páginas forem removidas ou recriadas.

Somente os registros elegíveis serão processados.

---

# O que acontece ao final?

Quando a sincronização terminar:

* o Workflow será finalizado;
* o resumo da execução será exibido;
* o Dashboard será atualizado;
* o histórico da execução será registrado.

Você poderá iniciar uma nova execução sempre que desejar.

---

# Boas práticas

Para obter melhores resultados:

* execute todas as etapas anteriores antes da sincronização;
* evite alterar manualmente páginas durante o processamento;
* mantenha a integração configurada corretamente;
* revise os alertas apresentados ao final da execução.

Essas práticas reduzem conflitos e tornam a sincronização mais eficiente.

---

# Perguntas frequentes

### A sincronização altera minhas informações no Notion?

Sim.

Ela atualiza apenas as propriedades gerenciadas pela Manhwateca.

Informações que não fazem parte da sincronização permanecem inalteradas.

---

### Posso editar páginas manualmente?

Sim.

No entanto, alterações em propriedades sincronizadas poderão ser substituídas na próxima sincronização, de acordo com as regras configuradas na aplicação.

---

### Preciso sincronizar sempre?

Não obrigatoriamente.

Porém, sincronizar após alterações importantes mantém o Notion consistente com a biblioteca local.

---

### A sincronização apaga páginas?

Não.

Ela cria ou atualiza páginas conforme necessário.

Caso uma obra deixe de existir na biblioteca, o tratamento dependerá das configurações definidas para a sincronização.

---

# Próximo passo

Após concluir a sincronização, consulte o capítulo **Acompanhar o Workflow** para aprender a interpretar o resumo da execução, analisar alertas e acompanhar o histórico dos processamentos realizados.

---

# Conclusão

A etapa **Sincronizar com Notion** encerra o Workflow da Manhwateca garantindo que as informações armazenadas localmente sejam refletidas na sua base do Notion. Dessa forma, você mantém uma única fonte de dados consistente e atualizada, aproveitando os recursos de organização e visualização oferecidos pelo Notion sem precisar realizar atualizações manuais.
