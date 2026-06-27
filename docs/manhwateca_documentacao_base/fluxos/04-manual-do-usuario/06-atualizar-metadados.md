# Atualizar Metadados

> Documento: **06-atualizar-metadados.md**

---

# Objetivo

A etapa **Atualizar Metadados** é responsável por consultar o **MangaUpdates** e atualizar automaticamente as informações oficiais das obras cadastradas na Manhwateca.

Após essa etapa, a biblioteca passa a conter informações mais completas e atualizadas, reduzindo a necessidade de edição manual.

Ela depende da etapa **Resolver IDs**, pois somente obras que possuem um **MangaUpdates ID** podem ter seus metadados atualizados automaticamente.

---

# O que são metadados?

Metadados são informações descritivas sobre uma obra.

Dependendo da disponibilidade no MangaUpdates, a Manhwateca poderá atualizar automaticamente informações como:

* título oficial;
* títulos alternativos;
* autores;
* artistas;
* ano de publicação;
* status da publicação;
* país de origem;
* gêneros;
* categorias;
* descrição (sinopse);
* quantidade de capítulos;
* capa da obra (quando suportado pela aplicação).

Essas informações enriquecem o catálogo e facilitam pesquisas, filtros e organização da biblioteca.

---

# Quando executar esta etapa?

Execute esta etapa quando:

* novos IDs forem associados às obras;
* desejar atualizar informações antigas;
* suspeitar que houve alterações no MangaUpdates;
* executar o Workflow completo.

No Workflow completo, esta etapa é iniciada automaticamente após **Resolver IDs**.

---

# Como funciona?

Para cada obra elegível, a Manhwateca:

1. verifica se existe um MangaUpdates ID;
2. consulta o MangaUpdates;
3. recupera os metadados disponíveis;
4. compara as informações com os dados atuais;
5. atualiza apenas os campos necessários;
6. registra a data da atualização.

Todo esse processo acontece automaticamente.

---

# Como iniciar

### Workflow completo

1. Acesse **Fluxos**.
2. Clique em **Executar Workflow**.

A atualização ocorrerá automaticamente quando o Workflow atingir esta etapa.

---

### Atualizar apenas os metadados

Caso deseje executar somente esta etapa:

1. Localize **Atualizar Metadados**.
2. Clique em **Executar**.

O sistema processará apenas as obras elegíveis.

---

# Acompanhando a execução

Durante a atualização, a interface exibirá informações semelhantes às seguintes:

```text
Atualizando Metadados

███████████░░░

76%

514 de 673 obras

Tempo: 03m26s
```

Esses indicadores são atualizados automaticamente durante o processamento.

---

# O que é atualizado?

Entre os dados normalmente sincronizados estão:

| Informação                 | Atualização automática |
| -------------------------- | ---------------------- |
| Título oficial             | Sim                    |
| Títulos alternativos       | Sim                    |
| Autor                      | Sim                    |
| Artista                    | Sim                    |
| Status da obra             | Sim                    |
| Gêneros                    | Sim                    |
| Categorias                 | Sim                    |
| Quantidade de capítulos    | Sim                    |
| Sinopse                    | Sim                    |
| Data da última atualização | Sim                    |

A disponibilidade de cada informação depende do que estiver disponível no MangaUpdates.

---

# Possíveis resultados

## Metadados atualizados

Exemplo:

```text
Omniscient Reader

Metadados atualizados com sucesso.
```

---

## Nenhuma alteração encontrada

Exemplo:

```text
Solo Leveling

Os metadados já estavam atualizados.
```

Nenhuma modificação será realizada.

---

## Obra sem ID

Exemplo:

```text
A obra não possui MangaUpdates ID.

Atualização ignorada.
```

Essas obras permanecerão pendentes até que um ID válido seja associado.

---

## Falha temporária

Exemplo:

```text
Não foi possível consultar o MangaUpdates.

Nova tentativa poderá ser realizada posteriormente.
```

O restante do Workflow continuará normalmente.

---

# Mensagens exibidas

Durante o processamento poderão aparecer mensagens como:

* "Consultando MangaUpdates..."
* "Atualizando metadados..."
* "Nenhuma alteração encontrada."
* "Metadados atualizados."
* "Atualização concluída."

Essas mensagens informam apenas o andamento da etapa.

---

# Alertas comuns

Algumas situações podem gerar alertas.

Exemplos:

* obra sem MangaUpdates ID;
* informações indisponíveis;
* timeout na comunicação;
* limite temporário de requisições;
* inconsistências encontradas na resposta.

> **Importante**
>
> Esses alertas normalmente afetam apenas as obras envolvidas e não interrompem o restante da execução.

---

# Posso executar novamente?

Sim.

Você pode atualizar os metadados sempre que desejar.

Isso é recomendado quando:

* novas informações forem adicionadas ao MangaUpdates;
* uma obra receber novos capítulos;
* houver alteração no status de publicação;
* ocorrer falha temporária durante uma execução anterior.

Somente os registros elegíveis serão processados.

---

# O que acontece depois?

Quando esta etapa terminar, o Workflow continuará automaticamente com:

```text
Atualizar Metadados

↓

Sincronizar Notion
```

A sincronização enviará ao Notion todas as informações atualizadas durante o processamento.

---

# Boas práticas

Para obter melhores resultados:

* resolva todos os IDs antes desta etapa;
* mantenha a conexão com a internet estável;
* execute atualizações periódicas;
* revise os alertas apresentados ao final da execução.

Essas práticas ajudam a manter sua biblioteca sempre atualizada.

---

# Perguntas frequentes

### A atualização altera minhas informações de leitura?

Não.

Esta etapa atualiza apenas metadados oficiais da obra.

Informações pessoais, como progresso de leitura, avaliações e favoritos, permanecem inalteradas.

---

### Todas as obras recebem atualização?

Não.

Apenas obras que possuem um MangaUpdates ID válido.

---

### Posso interromper esta etapa?

Sim.

Ao clicar em **Cancelar Workflow**, a Manhwateca concluirá a operação em andamento antes de interromper o processamento.

As atualizações já realizadas serão preservadas.

---

### Preciso atualizar os metadados sempre?

Não obrigatoriamente.

Entretanto, realizar atualizações periódicas garante que sua biblioteca permaneça alinhada às informações mais recentes disponíveis no MangaUpdates.

---

# Próximo passo

Após concluir a atualização dos metadados, o Workflow iniciará a etapa **Sincronizar com Notion**, responsável por refletir todas as alterações realizadas na base de dados do Notion.

---

# Conclusão

A etapa **Atualizar Metadados** mantém a biblioteca da Manhwateca alinhada às informações oficiais disponíveis no MangaUpdates. Ao atualizar automaticamente títulos, autores, gêneros, status e outros dados relevantes, ela reduz a manutenção manual e garante que as informações utilizadas pela aplicação permaneçam consistentes e atualizadas.
