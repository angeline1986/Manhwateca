# Acompanhar o Workflow

> Documento: **08-acompanhar-o-workflow.md**

---

# Objetivo

Após iniciar um Workflow, a página **Fluxos** passa a funcionar como um painel de acompanhamento em tempo real.

Neste capítulo você aprenderá como interpretar todas as informações exibidas durante a execução, identificar possíveis problemas e entender o resultado final do processamento.

---

# Durante a execução

Assim que o Workflow é iniciado, a interface passa a atualizar automaticamente todas as informações do processamento.

Você poderá acompanhar:

* etapa atual;
* progresso geral;
* progresso da etapa;
* quantidade de obras processadas;
* tempo decorrido;
* mensagens informativas;
* alertas;
* possíveis erros.

Não é necessário atualizar a página manualmente.

---

# Barra de Progresso Geral

Na parte superior da página existe uma barra que representa o progresso do Workflow completo.

Exemplo:

```text
Workflow

██████████░░░░░░░░

52%

Etapa 3 de 5
```

Ela informa:

* percentual concluído;
* quantidade de etapas finalizadas;
* etapa atualmente em execução.

Essa barra representa todo o Workflow, e não apenas uma etapa específica.

---

# Identificando a Etapa Atual

A etapa em execução será destacada visualmente.

Exemplo:

```text
✓ Organizar Biblioteca

✓ Catalogar Obras

▶ Resolver IDs

○ Atualizar Metadados

○ Sincronizar Notion
```

Legenda:

* **✓** Etapa concluída.
* **▶** Etapa em execução.
* **○** Etapa ainda não iniciada.

Essa visualização facilita identificar rapidamente o ponto atual do processamento.

---

# Painel de Execução

Enquanto uma etapa estiver em andamento, o painel de execução exibirá informações detalhadas.

Exemplo:

```text
Etapa atual

Resolver IDs

Obra atual

Omniscient Reader

183 de 254 obras

72%

Tempo: 01m53s
```

Essas informações são atualizadas continuamente.

---

# Tempo de Execução

O tempo apresentado representa quanto tempo o Workflow está sendo executado.

Esse valor é útil para:

* acompanhar execuções longas;
* comparar diferentes processamentos;
* identificar possíveis lentidões.

O tempo pode variar conforme:

* quantidade de obras;
* velocidade do computador;
* acesso ao banco de dados;
* disponibilidade do MangaUpdates;
* disponibilidade do Notion.

---

# Mensagens Durante o Processamento

Ao longo da execução poderão aparecer mensagens informativas.

Exemplos:

* "Organizando biblioteca..."
* "Catalogando obras..."
* "Consultando MangaUpdates..."
* "Atualizando metadados..."
* "Sincronizando com Notion..."

Essas mensagens acompanham o andamento natural do Workflow.

---

# Alertas

Algumas situações exigem atenção, mas não impedem a conclusão do processamento.

Exemplos:

* obras sem MangaUpdates ID;
* múltiplas correspondências encontradas;
* informações incompletas;
* páginas do Notion que precisarão ser recriadas.

> **Importante**
>
> Um alerta indica que determinada obra ou operação merece revisão posterior. Ele não significa, necessariamente, que o Workflow falhou.

---

# Erros

Quando uma operação não puder ser concluída, uma mensagem de erro será apresentada.

Exemplos:

* PostgreSQL indisponível;
* MangaUpdates inacessível;
* erro de autenticação no Notion;
* biblioteca não encontrada.

Sempre que possível, a Manhwateca continuará processando as demais obras.

---

# Mudança entre Etapas

Quando uma etapa termina, a interface muda automaticamente para a próxima.

Exemplo:

```text
✓ Resolver IDs

↓

▶ Atualizar Metadados
```

Essa transição ocorre sem necessidade de intervenção do usuário.

---

# Navegando Durante a Execução

Você pode acessar outros módulos da aplicação enquanto o Workflow continua sendo executado.

Ao retornar para **Fluxos**, a página recuperará automaticamente:

* progresso atual;
* etapa em execução;
* mensagens recentes;
* estado das integrações.

O processamento continua normalmente em segundo plano.

---

# Conclusão do Workflow

Ao final da execução, um resumo será exibido.

Exemplo:

```text
Workflow concluído

684 obras analisadas

18 novas obras

31 IDs resolvidos

612 metadados atualizados

598 sincronizações

3 alertas

Tempo total

08m42s
```

Esse resumo permite avaliar rapidamente o resultado da execução.

---

# Como interpretar o resumo

Ao analisar o resumo final, observe principalmente:

* quantidade de obras processadas;
* número de novas obras catalogadas;
* quantidade de IDs encontrados;
* metadados atualizados;
* sincronizações realizadas;
* alertas;
* erros encontrados.

Caso existam alertas ou erros, recomenda-se revisá-los antes da próxima execução.

---

# Quando executar novamente?

Você poderá iniciar uma nova execução quando:

* adicionar novas obras;
* reorganizar a biblioteca;
* desejar atualizar metadados;
* sincronizar novamente com o Notion;
* corrigir problemas encontrados na execução anterior.

Cada nova execução substituirá o resumo exibido anteriormente.

---

# Boas práticas

Para acompanhar o Workflow de forma eficiente:

* aguarde a conclusão antes de iniciar uma nova execução;
* acompanhe os alertas apresentados ao final;
* revise os erros antes de repetir uma etapa;
* utilize o resumo para confirmar que todas as operações esperadas foram concluídas.

---

# Próximo passo

Caso seja necessário interromper uma execução ou repetir uma etapa do Workflow, consulte o próximo capítulo **Cancelar ou Reiniciar**, que explica como realizar essas operações com segurança.

---

# Conclusão

A página **Fluxos** fornece todas as informações necessárias para acompanhar o processamento da biblioteca em tempo real. Compreender o significado do progresso, das mensagens, dos alertas e do resumo final permite identificar rapidamente o estado da execução e decidir quando é necessário realizar novas ações ou reprocessamentos.
