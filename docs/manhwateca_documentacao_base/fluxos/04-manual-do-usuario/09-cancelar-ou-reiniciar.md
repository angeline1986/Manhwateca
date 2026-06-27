# Cancelar ou Reiniciar

> Documento: **09-cancelar-ou-reiniciar.md**

---

# Objetivo

Embora o Workflow da Manhwateca tenha sido projetado para executar todas as etapas automaticamente, existem situações em que pode ser necessário interromper uma execução ou repetir uma etapa específica.

Este capítulo explica quando essas ações são recomendadas, como realizá-las com segurança e quais são seus efeitos sobre a biblioteca.

---

# Quando cancelar um Workflow?

Cancelar uma execução deve ser uma exceção.

Em condições normais, recomenda-se aguardar o término do processamento.

Entretanto, o cancelamento pode ser útil quando:

* o Workflow foi iniciado por engano;
* foi identificada uma configuração incorreta;
* a biblioteca foi alterada durante o processamento;
* alguma integração apresentou falhas que exigem correção antes de continuar.

> **Importante**
>
> Cancelar um Workflow não desfaz automaticamente as operações já concluídas.

---

# Como cancelar

Durante uma execução:

1. Acesse a página **Fluxos**.
2. Clique em **Cancelar Workflow**.
3. Confirme a operação.

A interface exibirá uma mensagem semelhante a:

```text
Deseja cancelar o Workflow?

As operações concluídas serão preservadas.

[Voltar]

[Cancelar Workflow]
```

Após a confirmação, o sistema iniciará o encerramento seguro da execução.

---

# O que acontece durante o cancelamento?

Ao solicitar o cancelamento, a Manhwateca:

* registra a solicitação;
* conclui a operação que estiver em andamento;
* salva todas as alterações já realizadas;
* encerra a etapa atual de forma segura;
* atualiza o estado do Workflow para **Cancelado**.

Esse comportamento evita inconsistências na base de dados.

---

# O que não acontece?

Cancelar o Workflow **não**:

* remove obras catalogadas;
* desfaz metadados já atualizados;
* exclui páginas criadas no Notion;
* apaga informações já gravadas no banco.

Todas as operações concluídas permanecem válidas.

---

# Reiniciando o Workflow

Após um cancelamento ou uma falha, você poderá iniciar uma nova execução normalmente.

Basta:

1. corrigir o problema identificado (quando necessário);
2. retornar à página **Fluxos**;
3. clicar em **Executar Workflow**.

A Manhwateca verificará automaticamente quais etapas ou obras ainda precisam ser processadas.

---

# Reexecutando apenas uma etapa

Nem sempre é necessário repetir todo o Workflow.

Você pode executar novamente apenas uma etapa específica.

Exemplos:

* **Resolver IDs**, após corrigir títulos de obras;
* **Atualizar Metadados**, quando desejar buscar informações mais recentes;
* **Sincronizar Notion**, após corrigir uma falha na integração.

Essa abordagem reduz o tempo de processamento e evita trabalho desnecessário.

---

# Situações comuns

## Falha no MangaUpdates

Se o MangaUpdates estiver temporariamente indisponível:

* aguarde a normalização do serviço;
* execute novamente apenas **Resolver IDs** ou **Atualizar Metadados**.

Não é necessário reorganizar ou catalogar novamente a biblioteca.

---

## Falha no Notion

Se a sincronização falhar:

* verifique a configuração da integração;
* confirme o acesso ao banco de dados do Notion;
* execute novamente apenas **Sincronizar Notion**.

As etapas anteriores permanecem válidas.

---

## Novas obras adicionadas

Caso novas obras sejam adicionadas após um Workflow concluído:

Recomenda-se executar novamente o **Workflow completo**.

Assim, todas as etapas serão executadas na ordem correta para as novas obras.

---

## Alterações em metadados

Caso apenas deseje atualizar informações oficiais das obras:

Execute somente **Atualizar Metadados**.

---

# Como saber se devo repetir uma etapa?

O resumo da execução ajuda a identificar a necessidade de reprocessamento.

Exemplos:

| Situação                 | Ação recomendada                   |
| ------------------------ | ---------------------------------- |
| Obras sem ID             | Reexecutar **Resolver IDs**        |
| Metadados desatualizados | Reexecutar **Atualizar Metadados** |
| Falha na sincronização   | Reexecutar **Sincronizar Notion**  |
| Biblioteca alterada      | Executar o Workflow completo       |

---

# Boas práticas

Para evitar cancelamentos e reprocessamentos desnecessários:

* não altere a biblioteca durante uma execução;
* mantenha a conexão com a internet estável;
* verifique as integrações antes de iniciar o Workflow;
* acompanhe os alertas exibidos pela interface.

Essas práticas tornam o processamento mais rápido e previsível.

---

# Perguntas frequentes

### Posso fechar a página durante a execução?

Sim.

O Workflow continuará sendo executado em segundo plano.

Ao retornar para a página **Fluxos**, o progresso será recuperado automaticamente.

---

### Posso iniciar outro Workflow enquanto um já está em execução?

Não.

A Manhwateca permite apenas uma execução do Workflow por vez.

---

### O cancelamento pode corromper meus dados?

Não.

O cancelamento foi projetado para ocorrer de forma segura, preservando todas as alterações já concluídas.

---

### É melhor repetir uma etapa ou todo o Workflow?

Depende da situação.

Sempre que possível, prefira repetir apenas a etapa afetada.

O Workflow completo é recomendado quando houver alterações estruturais na biblioteca.

---

# Próximo passo

No próximo capítulo, **Ajuda**, você encontrará respostas para as dúvidas mais comuns, orientações para resolver problemas frequentes e um glossário com os principais termos utilizados pela Manhwateca.

---

# Conclusão

Cancelar ou reiniciar um Workflow faz parte do uso normal da Manhwateca em situações específicas. Saber quando interromper uma execução, quando repetir apenas uma etapa e quando executar o Workflow completo ajuda a economizar tempo, reduzir processamento desnecessário e manter a biblioteca sempre consistente e atualizada.
