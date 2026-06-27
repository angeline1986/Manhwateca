# Estados e Mensagens

> Documento: **06-estados-e-mensagens.md**

---

# Objetivo

Este documento define todos os estados visuais e mensagens apresentados pela página **Fluxos** durante a execução do Workflow.

Seu objetivo é garantir que o usuário compreenda, em qualquer momento da execução:

* o estado atual do Workflow;
* o andamento de cada etapa;
* o resultado das operações;
* os problemas encontrados;
* as ações que podem ser realizadas.

As mensagens devem priorizar clareza, objetividade e orientação ao usuário.

---

# Princípios

Todo feedback apresentado pela interface deve seguir quatro princípios:

* ser imediato;
* ser compreensível;
* indicar claramente o impacto da situação;
* informar, quando possível, a próxima ação recomendada.

Mensagens técnicas, stack traces e códigos internos nunca devem ser exibidos ao usuário final.

---

# Estados do Workflow

O Workflow completo pode assumir os seguintes estados.

| Estado                | Descrição                             |
| --------------------- | ------------------------------------- |
| Não iniciado          | Nenhuma execução em andamento         |
| Preparando            | Validações iniciais                   |
| Em execução           | Workflow ativo                        |
| Pausado               | Execução temporariamente interrompida |
| Cancelando            | Encerrando operações em andamento     |
| Concluído             | Todas as etapas executadas            |
| Concluído com alertas | Finalizado com pendências             |
| Falhou                | Execução interrompida por erro        |

Cada estado deve possuir representação visual consistente.

---

# Estados das Etapas

Cada etapa do Workflow possui estado independente.

| Estado                | Significado                      |
| --------------------- | -------------------------------- |
| Aguardando            | Ainda não iniciada               |
| Validando             | Executando verificações iniciais |
| Processando           | Executando operações             |
| Concluída             | Finalizada com sucesso           |
| Concluída com alertas | Finalizada, porém com pendências |
| Ignorada              | Não elegível para execução       |
| Falhou                | Não pôde ser concluída           |
| Cancelada             | Interrompida pelo usuário        |

A mudança de estado deve ocorrer automaticamente durante a execução.

---

# Estados das Integrações

As integrações também possuem estados próprios.

| Estado       | Descrição                    |
| ------------ | ---------------------------- |
| Operacional  | Serviço disponível           |
| Verificando  | Estado sendo consultado      |
| Atenção      | Funcionamento degradado      |
| Indisponível | Comunicação impossível       |
| Desconhecido | Estado ainda não determinado |

Esses estados devem permanecer visíveis durante todo o Workflow.

---

# Indicadores Visuais

A interface deve utilizar elementos consistentes para representar estados.

| Estado      | Exemplo |
| ----------- | ------- |
| Concluído   | ✓       |
| Em execução | ▶       |
| Aguardando  | ○       |
| Atenção     | ⚠       |
| Erro        | ✕       |

Os ícones complementam o texto, nunca o substituem.

---

# Mensagens Informativas

Devem ser utilizadas para comunicar eventos normais da execução.

Exemplos:

* "Workflow iniciado."
* "Biblioteca validada."
* "Catalogação concluída."
* "Atualização de metadados finalizada."
* "Sincronização com o Notion concluída."

Não exigem ação do usuário.

---

# Mensagens de Progresso

Durante operações longas, a interface deve informar continuamente:

* etapa atual;
* obra em processamento;
* percentual concluído;
* quantidade processada;
* tempo decorrido.

Exemplo:

```text id="mt96tx"
Atualizando metadados...

248 de 731 obras

34%

Tempo decorrido: 02m18s
```

---

# Mensagens de Sucesso

Apresentadas quando uma operação é concluída conforme esperado.

Exemplos:

* "Workflow concluído com sucesso."
* "31 IDs associados."
* "612 metadados atualizados."
* "598 páginas sincronizadas."

Sempre que possível, devem apresentar dados quantitativos.

---

# Mensagens de Atenção

Utilizadas quando a operação foi concluída, mas existem situações que merecem revisão.

Exemplos:

* "15 obras não possuem MangaUpdates ID."
* "3 obras apresentaram títulos ambíguos."
* "7 páginas do Notion aguardam sincronização."

Essas mensagens não impedem a continuidade do Workflow.

---

# Mensagens de Erro

Utilizadas quando uma operação não pôde ser concluída.

Exemplos:

* "Não foi possível acessar o PostgreSQL."
* "A biblioteca configurada não foi encontrada."
* "Falha ao comunicar com o MangaUpdates."
* "Erro ao sincronizar com o Notion."

Cada mensagem deve indicar claramente qual operação foi afetada.

---

# Mensagens de Cancelamento

Quando o usuário interromper o Workflow.

Exemplos:

* "Cancelando execução..."
* "Workflow cancelado pelo usuário."
* "As alterações já concluídas foram preservadas."

---

# Mensagens de Confirmação

Operações potencialmente impactantes devem solicitar confirmação.

Exemplos:

## Executar Workflow

```text id="ej2m8m"
Deseja iniciar o Workflow completo?

[Cancelar]

[Executar]
```

---

## Reexecutar etapa

```text id="2vng7u"
Deseja executar novamente a etapa
Atualizar Metadados?

[Cancelar]

[Reexecutar]
```

---

## Cancelar execução

```text id="11m5w2"
Deseja cancelar o Workflow?

As operações concluídas serão preservadas.

[Continuar]

[Cancelar Workflow]
```

---

# Mensagens de Resumo

Ao término do Workflow, a interface deve apresentar um resumo consolidado.

Exemplo:

```text id="2c4nws"
Workflow concluído

684 obras analisadas

31 IDs resolvidos

612 metadados atualizados

598 sincronizações

3 alertas

Tempo total

08m42s
```

Esse resumo permanece visível até uma nova execução.

---

# Atualização das Mensagens

As mensagens devem ser atualizadas em tempo real durante o processamento.

A interface não deve exigir recarregamento da página para refletir mudanças de estado.

---

# Persistência

As mensagens transitórias podem desaparecer automaticamente.

Entretanto, o resultado final da execução deve permanecer acessível enquanto o usuário permanecer na página.

---

# Priorização

Quando existirem múltiplas mensagens simultâneas, a prioridade deve ser:

1. Erros.
2. Cancelamentos.
3. Alertas.
4. Sucessos.
5. Informações.
6. Progresso.

---

# Linguagem

Todas as mensagens devem utilizar linguagem:

* objetiva;
* profissional;
* orientada à ação;
* consistente em toda a aplicação.

Evitar:

* termos excessivamente técnicos;
* mensagens genéricas;
* ambiguidades.

Preferir:

> "Não foi possível acessar o MangaUpdates. Tente novamente mais tarde."

em vez de

> "Erro 500."

---

# Relação com outros documentos

| Documento                        | Conteúdo relacionado                  |
| -------------------------------- | ------------------------------------- |
| 02-interface-e-layout.md         | Estrutura visual da interface         |
| 03-etapas-do-workflow.md         | Estados das etapas                    |
| 04-processamento-e-validacoes.md | Validações que originam mensagens     |
| 05-integracoes.md                | Estados das integrações               |
| 07-regras-de-navegacao.md        | Comportamento após mudanças de estado |

---

# Conclusão

Os estados e mensagens da página **Fluxos** têm como objetivo fornecer feedback contínuo e confiável durante toda a execução do Workflow. Uma comunicação clara sobre progresso, sucessos, alertas e erros reduz incertezas, facilita a identificação de problemas e torna a operação mais previsível para o usuário, especialmente em processamentos longos e dependentes de múltiplas integrações.
