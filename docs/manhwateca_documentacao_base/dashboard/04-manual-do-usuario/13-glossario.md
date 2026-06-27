# Manual do Usuário — Dashboard

## 13 - Glossário

---

# Objetivo deste capítulo

Ao utilizar a Manhwateca, você encontrará alguns termos técnicos e conceitos específicos relacionados à organização da biblioteca, sincronização de dados e integração com serviços externos.

Este glossário reúne as principais definições utilizadas ao longo da aplicação e deste manual.

Seu objetivo é facilitar a compreensão da interface e padronizar o significado dos termos utilizados.

> **Dica:** Sempre que encontrar uma palavra desconhecida durante a utilização da Manhwateca, consulte este glossário antes de procurar outras referências.

---

# A

## Ação Recomendada

Painel do Dashboard responsável por indicar automaticamente qual deve ser a próxima atividade do usuário.

Seu objetivo é orientar a utilização da aplicação e reduzir dúvidas sobre qual etapa executar.

---

## Atualização

Processo de obtenção das informações mais recentes da aplicação.

No Dashboard, atualizar significa consultar novamente o estado atual da biblioteca, das integrações e do Workflow.

A atualização **não executa** tarefas operacionais.

---

# B

## Biblioteca

Conjunto de mangás, manhwas ou novels armazenados no diretório monitorado pela Manhwateca.

Também é o nome do módulo utilizado para consultar e visualizar as obras cadastradas.

---

## Banco de Dados

Local onde a Manhwateca armazena informações sobre a biblioteca.

Atualmente o sistema utiliza o **PostgreSQL** como banco de dados principal.

---

# C

## Catalogar Arquivos

Etapa do Workflow responsável por identificar as obras existentes na biblioteca e registrá-las no catálogo da aplicação.

Essa etapa deve ser executada sempre que novas obras forem adicionadas ou removidas.

---

## Catálogo

Conjunto de todas as obras cadastradas na Manhwateca.

O catálogo representa a visão organizada da biblioteca e serve como base para todas as demais funcionalidades.

---

# D

## Dashboard

Tela principal da Manhwateca.

Funciona como um centro de comando, reunindo informações sobre a biblioteca, Workflow, pendências, integrações e ações recomendadas.

Seu papel é informar e orientar, não executar tarefas.

---

# F

## Fluxos

Módulo responsável pela execução das etapas do Workflow.

É nele que são realizadas atividades como organizar a biblioteca, catalogar arquivos, resolver IDs, atualizar metadados e sincronizar o Notion.

---

# I

## ID

Identificador único utilizado para associar uma obra cadastrada ao seu registro oficial em uma fonte de metadados.

Esse identificador permite atualizar automaticamente informações da obra.

---

## Integrações

Serviços utilizados pela Manhwateca para oferecer funcionalidades adicionais.

As integrações atualmente monitoradas pelo Dashboard são:

* PostgreSQL;
* Biblioteca;
* MangaUpdates;
* Notion.

---

# M

## MangaUpdates

Serviço utilizado pela Manhwateca para obter informações sobre as obras cadastradas.

Esses dados são utilizados principalmente durante a atualização dos metadados.

---

## Metadados

Informações descritivas sobre uma obra.

Exemplos:

* título;
* autor;
* artista;
* gêneros;
* status;
* número de capítulos;
* capa.

Esses dados ajudam a manter a biblioteca organizada e atualizada.

---

## Métricas

Indicadores numéricos apresentados no Dashboard.

As métricas resumem a situação atual da biblioteca e auxiliam no acompanhamento do progresso da coleção.

---

# N

## Notion

Plataforma utilizada para armazenar ou sincronizar informações da biblioteca.

A Manhwateca pode enviar automaticamente alterações para uma base de dados do Notion quando a sincronização é executada.

---

# P

## Pendência

Situação identificada pela aplicação que exige ou recomenda alguma ação do usuário.

Nem toda pendência representa um erro.

Ela pode indicar apenas que determinada etapa do Workflow ainda não foi concluída.

---

## PostgreSQL

Sistema gerenciador de banco de dados utilizado pela Manhwateca.

Responsável pelo armazenamento das informações da aplicação.

---

## Próximo Passo Recomendado

Painel do Dashboard que apresenta automaticamente a atividade considerada mais importante naquele momento.

É o principal guia de utilização da aplicação.

---

# R

## Recarregar

Ação utilizada para atualizar as informações exibidas no Dashboard.

Essa operação consulta novamente os dados da aplicação, mas não modifica a biblioteca.

---

# S

## Sincronização

Processo de envio ou atualização de informações entre a Manhwateca e outro serviço.

No contexto atual, refere-se principalmente à sincronização com o Notion.

---

## Status

Condição atual de um componente, integração ou etapa do Workflow.

Exemplos:

* operacional;
* em andamento;
* concluído;
* bloqueado;
* erro.

---

# W

## Workflow

Sequência oficial de etapas utilizada para organizar e manter a biblioteca.

O Workflow da Manhwateca é composto por cinco etapas:

1. Organizar Biblioteca;
2. Catalogar Arquivos;
3. Resolver IDs;
4. Atualizar Metadados;
5. Sincronizar Notion.

Cada etapa prepara a biblioteca para a seguinte.

---

# Termos relacionados

A tabela abaixo apresenta alguns conceitos que normalmente aparecem em conjunto.

| Termo       | Relacionado a                      |
| ----------- | ---------------------------------- |
| Dashboard   | Centro de comando                  |
| Workflow    | Organização da biblioteca          |
| Fluxos      | Execução do Workflow               |
| Pendências  | Situações que exigem atenção       |
| Integrações | Serviços utilizados pela aplicação |
| Metadados   | Informações das obras              |
| IDs         | Identificação das obras            |
| Notion      | Sincronização                      |
| PostgreSQL  | Banco de dados                     |
| Biblioteca  | Coleção de obras                   |

---

# Conceitos importantes

Durante a utilização da Manhwateca, vale lembrar alguns princípios fundamentais.

* O Dashboard informa; ele não executa tarefas.
* O Workflow define a ordem correta das atividades.
* As Pendências indicam o que exige atenção.
* As Métricas mostram a situação atual da biblioteca.
* As Integrações informam a saúde do ambiente.
* O botão **Recarregar** atualiza apenas as informações exibidas.
* O módulo **Fluxos** é responsável pela execução das atividades operacionais.

Esses conceitos aparecem com frequência em toda a documentação da aplicação.

---

# Resumo

Ao concluir este glossário, você já conhece o significado dos principais termos utilizados pela Manhwateca.

Sempre que encontrar um conceito desconhecido durante a utilização da aplicação, retorne a este capítulo.

Manter uma terminologia consistente facilita o entendimento da interface e reduz dúvidas durante o uso do sistema.

---

# Encerramento do Manual

Parabéns!

Você concluiu o **Manual do Usuário do Dashboard da Manhwateca**.

Ao longo deste guia foram apresentados:

* o propósito do Dashboard;
* a função de cada componente;
* a interpretação das métricas e pendências;
* o funcionamento do Workflow;
* as integrações monitoradas;
* as ações rápidas;
* o processo de atualização das informações;
* respostas para dúvidas frequentes;
* procedimentos de solução de problemas;
* os principais conceitos utilizados pela aplicação.

Recomenda-se consultar este manual sempre que surgir alguma dúvida sobre a utilização do Dashboard ou ao conhecer uma nova funcionalidade da Manhwateca.
