Entendido. Prosseguindo com o próximo arquivo.

# Manual do Usuário — Dashboard

## 02 - Conhecendo o Dashboard

---

# Objetivo deste capítulo

Neste capítulo você conhecerá a organização visual do Dashboard e aprenderá a localizar rapidamente cada informação apresentada pela Manhwateca.

Ao final da leitura, você será capaz de identificar a função de cada área da tela e compreender como elas trabalham em conjunto para auxiliar no gerenciamento da sua biblioteca.

---

# Visão Geral da Tela

O Dashboard foi projetado para apresentar apenas as informações necessárias para tomada de decisão.

Os componentes estão organizados em uma sequência lógica de leitura, permitindo que você compreenda rapidamente a situação da biblioteca.

A estrutura geral da página é semelhante ao exemplo abaixo.

```text
┌─────────────────────────────────────────────────────────────┐
│ Cabeçalho                                                   │
├─────────────────────────────────────────────────────────────┤
│ Próximo Passo Recomendado                                   │
├─────────────────────────────────────────────────────────────┤
│ Métricas                                                    │
├───────────────────────────────┬─────────────────────────────┤
│ Pendências                    │ Integrações                │
├───────────────────────────────┴─────────────────────────────┤
│ Workflow                                                   │
├─────────────────────────────────────────────────────────────┤
│ Ações Rápidas                                              │
└─────────────────────────────────────────────────────────────┘
```

Cada bloco possui uma função específica e independente.

---

# Como ler o Dashboard

A melhor forma de utilizar o Dashboard é seguir a ordem natural da tela.

Essa sequência foi definida para reduzir o tempo necessário para compreender a situação da biblioteca.

Recomenda-se seguir este fluxo:

1. Verifique a **Ação Recomendada**.
2. Consulte as **Métricas**.
3. Analise as **Pendências**.
4. Confirme o estado das **Integrações**.
5. Observe o progresso do **Workflow**.
6. Utilize as **Ações Rápidas**, quando necessário.

Seguindo essa ordem, você normalmente conseguirá identificar qualquer necessidade de ação em poucos segundos.

---

# Cabeçalho

O cabeçalho ocupa a parte superior do Dashboard.

Ele possui três funções principais:

* identificar a página atual;
* informar quando os dados foram atualizados pela última vez;
* permitir a atualização manual das informações através do botão **Recarregar**.

O cabeçalho permanece sempre visível e serve como referência durante toda a utilização da página.

---

# Ação Recomendada

Logo abaixo do cabeçalho encontra-se o componente mais importante do Dashboard.

Essa área informa automaticamente qual deve ser a próxima atividade a ser executada.

Sempre que houver uma etapa prioritária, ela será apresentada em destaque.

> **Dica:** Antes de analisar qualquer outro componente, consulte a **Ação Recomendada**. Ela foi criada para orientar sua rotina e reduzir dúvidas sobre qual atividade executar.

---

# Métricas

As métricas apresentam um resumo numérico da biblioteca.

Esses indicadores permitem acompanhar rapidamente informações importantes sem necessidade de abrir outros módulos.

Normalmente você encontrará informações como:

* quantidade total de obras;
* novos capítulos encontrados;
* obras sem identificação;
* alterações aguardando sincronização.

Esses números ajudam a medir o estado geral da biblioteca.

---

# Pendências

O painel de Pendências reúne situações que exigem atenção.

Quando alguma atividade impedir o avanço do Workflow ou exigir intervenção do usuário, ela será apresentada nessa área.

Cada pendência informa:

* o problema identificado;
* uma breve explicação;
* um botão para acessar o módulo responsável pela resolução.

O Dashboard não resolve pendências diretamente.

Ele apenas informa onde elas devem ser tratadas.

---

# Integrações

O painel de Integrações informa se os principais serviços utilizados pela aplicação estão funcionando corretamente.

Entre eles:

* Banco de Dados;
* Biblioteca local;
* MangaUpdates;
* Notion.

Esse painel é especialmente útil quando alguma funcionalidade deixa de funcionar inesperadamente.

Antes de procurar outras causas, consulte o estado das integrações.

---

# Workflow

O Workflow apresenta um resumo visual das etapas de organização da biblioteca.

Ele permite acompanhar:

* quais etapas já foram concluídas;
* qual etapa está em andamento;
* quais atividades ainda permanecem pendentes.

Esse componente facilita o acompanhamento do progresso geral da biblioteca.

---

# Ações Rápidas

Na parte inferior do Dashboard estão disponíveis os atalhos para os principais módulos da aplicação.

Esses botões permitem acessar rapidamente:

* Biblioteca;
* Fluxos;
* Configurações;
* Atualização do Dashboard.

As Ações Rápidas não executam tarefas diretamente.

Elas apenas direcionam você para o local apropriado.

---

# Como os componentes trabalham juntos

Embora cada componente tenha uma função específica, todos trabalham de forma integrada.

Um exemplo de utilização é apresentado abaixo.

```text
Dashboard

↓

Ação Recomendada

↓

Pendência encontrada

↓

Workflow identifica a etapa

↓

Fluxos executa a atividade

↓

Retorno ao Dashboard

↓

Atualização das informações
```

Esse fluxo representa a utilização mais comum da aplicação.

---

# Ordem de importância

Os componentes foram organizados de acordo com sua importância durante o uso da aplicação.

| Prioridade | Componente       | Objetivo                            |
| ---------- | ---------------- | ----------------------------------- |
| Muito Alta | Ação Recomendada | Informar a próxima atividade.       |
| Alta       | Métricas         | Resumir a situação da biblioteca.   |
| Alta       | Pendências       | Destacar problemas que exigem ação. |
| Média      | Integrações      | Informar a saúde do ambiente.       |
| Média      | Workflow         | Mostrar o progresso da organização. |
| Baixa      | Ações Rápidas    | Facilitar a navegação.              |

Essa organização ajuda o usuário a localizar rapidamente as informações mais relevantes.

---

# Quando consultar cada área

| Situação                         | Área recomendada |
| -------------------------------- | ---------------- |
| Não sei qual atividade executar  | Ação Recomendada |
| Quero saber quantas obras possuo | Métricas         |
| Algo deixou de funcionar         | Integrações      |
| Quero acompanhar o progresso     | Workflow         |
| Existem problemas na biblioteca  | Pendências       |
| Preciso acessar outro módulo     | Ações Rápidas    |

Essa tabela pode servir como referência rápida durante a utilização da aplicação.

---

# Boas práticas

Para aproveitar melhor o Dashboard:

* siga sempre a ordem natural da tela;
* consulte primeiro a Ação Recomendada;
* verifique regularmente o painel de Pendências;
* acompanhe o Workflow após concluir tarefas importantes;
* utilize as Ações Rápidas para reduzir a navegação entre módulos.

> **Dica:** Evite interpretar um único componente isoladamente. O Dashboard foi projetado para que todos os blocos se complementem e forneçam uma visão completa da situação da biblioteca.

---

# Resumo

Neste capítulo você aprendeu:

* como o Dashboard está organizado;
* qual é a função de cada bloco visual;
* a melhor sequência para analisar as informações;
* como os componentes trabalham em conjunto;
* quando consultar cada área da tela.

Esse conhecimento servirá como base para os próximos capítulos, que explicarão cada componente individualmente com mais detalhes.