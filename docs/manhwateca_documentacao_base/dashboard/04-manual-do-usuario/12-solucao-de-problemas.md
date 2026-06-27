# Manual do Usuário — Dashboard

## 12 - Solução de Problemas

---

# Objetivo deste capítulo

Mesmo com uma configuração correta, podem ocorrer situações em que alguma informação deixe de aparecer, uma integração fique indisponível ou uma etapa do Workflow não possa ser concluída.

Este capítulo apresenta um guia de diagnóstico para os problemas mais comuns encontrados no Dashboard.

O objetivo é ajudá-lo a identificar rapidamente a causa do problema e indicar qual deve ser a próxima ação.

Na maioria dos casos, não será necessário consultar documentação técnica.

---

# Antes de começar

Quando alguma informação parecer incorreta, siga sempre esta sequência:

1. Atualize o Dashboard utilizando **Recarregar**.
2. Consulte o painel **Integrações**.
3. Verifique o painel **Pendências**.
4. Confirme qual etapa do Workflow está ativa.
5. Somente depois procure alterar alguma configuração.

Essa sequência resolve grande parte das situações do dia a dia.

> **Importante:** Evite executar novamente uma operação apenas porque um indicador ainda não foi atualizado. Sempre utilize **Recarregar** antes de repetir qualquer atividade.

---

# Problema: O Dashboard não carrega

## Sintomas

* a tela permanece vazia;
* componentes não aparecem;
* informações não são exibidas.

## Possíveis causas

* aplicação ainda está iniciando;
* problema de conexão com o banco de dados;
* erro temporário de comunicação.

## O que fazer

1. Aguarde alguns segundos.
2. Utilize **Recarregar**.
3. Consulte o painel **Integrações**.
4. Verifique se o PostgreSQL está operacional.

Se o problema continuar, consulte o administrador da aplicação.

---

# Problema: As informações parecem antigas

## Sintomas

* métricas não mudam;
* pendências permanecem iguais;
* Workflow não avança.

## Possíveis causas

* Dashboard ainda não foi atualizado;
* operação anterior ainda está em processamento.

## O que fazer

1. Clique em **Recarregar**.
2. Aguarde a atualização.
3. Verifique a data da **Última atualização**.
4. Confirme se a operação anterior foi concluída com sucesso.

---

# Problema: O Workflow não avança

## Sintomas

* a mesma etapa continua ativa;
* o Próximo Passo permanece igual.

## Possíveis causas

* a atividade ainda não foi concluída;
* existe uma pendência bloqueante;
* ocorreu algum erro durante a execução.

## O que fazer

1. Consulte o painel **Pendências**.
2. Resolva pendências de alta prioridade.
3. Atualize o Dashboard.
4. Verifique novamente o Workflow.

---

# Problema: A pendência não desaparece

## Sintomas

* a mesma pendência continua aparecendo após a execução da atividade.

## Possíveis causas

* a operação não foi concluída;
* ainda existem itens pendentes;
* o Dashboard ainda não foi atualizado.

## O que fazer

1. Atualize o Dashboard.
2. Confirme o resultado da operação no módulo correspondente.
3. Execute novamente apenas se necessário.

---

# Problema: Existem obras sem ID

## Sintomas

A métrica **Obras sem ID** apresenta um valor maior que zero.

## O que significa?

Algumas obras ainda não possuem identificação confirmada.

Enquanto isso ocorrer, determinadas informações não poderão ser atualizadas.

## O que fazer

1. Abra **Fluxos**.
2. Execute **Resolver IDs**.
3. Retorne ao Dashboard.
4. Atualize a página.

---

# Problema: O Notion apresenta erro

## Sintomas

* integração em vermelho;
* sincronização indisponível.

## Possíveis causas

* token inválido;
* integração removida;
* banco de dados inacessível.

## O que fazer

1. Abra **Configurações**.
2. Revise a configuração da integração.
3. Salve as alterações.
4. Retorne ao Dashboard.
5. Atualize as informações.

---

# Problema: O PostgreSQL está indisponível

## Sintomas

O painel de Integrações apresenta:

```text
🔴 PostgreSQL
Indisponível
```

## Impacto

Essa é uma das situações mais críticas.

Grande parte das funcionalidades poderá ficar indisponível.

## O que fazer

1. Verifique se o banco está em execução.
2. Revise as configurações de conexão.
3. Retorne ao Dashboard.
4. Atualize as informações.

---

# Problema: A biblioteca não é encontrada

## Sintomas

* diretório inacessível;
* biblioteca indisponível.

## Possíveis causas

* pasta removida;
* caminho alterado;
* unidade externa desconectada.

## O que fazer

1. Confirme que o diretório ainda existe.
2. Verifique se a unidade está conectada.
3. Revise o caminho configurado.
4. Atualize o Dashboard.

---

# Problema: O MangaUpdates está indisponível

## Sintomas

O painel apresenta:

```text
🟡 Resposta lenta
```

ou

```text
🔴 Indisponível
```

## Impacto

A atualização dos metadados poderá falhar ou demorar mais que o habitual.

A consulta da biblioteca continua funcionando normalmente.

## O que fazer

Aguarde alguns minutos e tente novamente mais tarde.

---

# Problema: A sincronização com o Notion não termina

## Sintomas

As pendências permanecem inalteradas após a sincronização.

## O que fazer

1. Verifique o estado da integração com o Notion.
2. Confirme se a sincronização foi concluída.
3. Atualize o Dashboard.
4. Execute novamente apenas se necessário.

---

# Problema: O botão Recarregar não alterou nada

## O que significa?

Provavelmente nenhuma informação mudou desde a última atualização.

Esse comportamento é esperado.

Não é necessário repetir a atualização continuamente.

---

# Como interpretar as cores

| Cor         | Significado          | Ação recomendada                        |
| ----------- | -------------------- | --------------------------------------- |
| 🟢 Verde    | Funcionamento normal | Nenhuma ação necessária                 |
| 🟡 Amarelo  | Atenção              | Verifique a situação antes de continuar |
| 🔴 Vermelho | Problema             | Corrija antes de prosseguir             |

As cores servem como um guia visual para priorizar a resolução dos problemas.

---

# Fluxo recomendado de diagnóstico

Sempre que surgir algum comportamento inesperado, siga este fluxo.

```text
Problema identificado

↓

Recarregar Dashboard

↓

Consultar Integrações

↓

Consultar Pendências

↓

Verificar Workflow

↓

Abrir Configurações (se necessário)

↓

Problema resolvido
```

Essa sequência evita diagnósticos precipitados e reduz retrabalho.

---

# Quando procurar suporte?

Procure ajuda quando:

* o problema persistir após seguir este guia;
* uma integração permanecer indisponível por um longo período;
* ocorrerem mensagens de erro repetidas;
* a aplicação deixar de responder.

Ao solicitar suporte, informe:

* qual operação estava sendo executada;
* qual mensagem foi apresentada;
* quais integrações estavam indisponíveis;
* quais passos deste guia já foram realizados.

Essas informações facilitam a identificação da causa do problema.

---

# Boas práticas

Para reduzir a ocorrência de problemas:

* mantenha a biblioteca organizada;
* siga sempre a ordem do Workflow;
* atualize o Dashboard após concluir atividades importantes;
* consulte regularmente o painel de Integrações;
* resolva pendências de alta prioridade antes de iniciar novas tarefas.

> **Dica:** A maioria dos problemas encontrados no Dashboard está relacionada a pendências ainda não resolvidas ou integrações temporariamente indisponíveis. Antes de repetir uma operação, verifique esses dois componentes.

---

# Resumo

Neste capítulo você aprendeu:

* como diagnosticar os problemas mais comuns do Dashboard;
* quais verificações realizar antes de alterar configurações;
* como interpretar os estados das integrações;
* quando atualizar o Dashboard;
* quando procurar suporte;
* quais boas práticas ajudam a evitar problemas recorrentes.
