# Documentação Técnica — Módulo Fluxos

> Documento: **README.md**

---

# Objetivo

Este diretório reúne toda a documentação técnica do módulo **Fluxos** da Manhwateca.

Enquanto as **Histórias de Usuário** definem os requisitos de negócio e a **Especificação Funcional** descreve o comportamento esperado da interface, esta documentação especifica **como o módulo deve ser implementado**.

Seu foco é fornecer informações suficientes para que desenvolvedores possam implementar, manter e evoluir o Workflow sem depender de conhecimento implícito do projeto.

---

# Escopo

A Documentação Técnica descreve:

* arquitetura do módulo;
* organização dos componentes;
* contratos entre Backend e Frontend;
* fluxo de processamento;
* integrações externas;
* requisitos de desempenho;
* estratégias de tratamento de erros;
* testes;
* checklists de implementação e revisão.

Não fazem parte deste diretório:

* requisitos de negócio;
* comportamento visual da interface;
* manual de utilização.

---

# Estrutura da Documentação

| Documento                               | Conteúdo                                                                 |
| --------------------------------------- | ------------------------------------------------------------------------ |
| 01-visao-geral.md                       | Escopo técnico, objetivos de engenharia e visão arquitetural             |
| 02-arquitetura.md                       | Componentes, responsabilidades, fluxo de dados e padrões arquiteturais   |
| 03-api-e-contratos.md                   | Endpoints, contratos JSON e comunicação entre Backend e Frontend         |
| 04-processamento.md                     | Pipeline interno do Workflow, processamento, concorrência e persistência |
| 05-integracoes.md                       | PostgreSQL, Biblioteca, MangaUpdates e Notion                            |
| 06-performance-e-tratamento-de-erros.md | Performance, resiliência, recuperação e observabilidade                  |
| 07-testes.md                            | Estratégia de testes unitários, integração, E2E e cobertura              |
| 08-checklists.md                        | Checklist de implementação e checklist de code review                    |

---

# Arquitetura Geral

O módulo Fluxos atua como orquestrador do processamento da biblioteca.

```text id="3ksd5e"
                 Interface Web
                       │
                       ▼
              Workflow Controller
                       │
                       ▼
             Workflow Orchestrator
                       │
     ┌─────────────────┼──────────────────┐
     ▼                 ▼                  ▼
 PostgreSQL     MangaUpdates API     Notion API
     │
     ▼
Biblioteca (Google Drive)
```

A interface nunca acessa diretamente banco de dados ou APIs externas.

Toda comunicação passa pela camada de orquestração do Workflow.

---

# Organização em Camadas

A implementação deve seguir separação clara de responsabilidades.

```text id="8xgj1g"
UI

↓

Controllers

↓

Workflow Orchestrator

↓

Services

↓

Repositories

↓

PostgreSQL

↓

APIs Externas
```

Cada camada possui responsabilidades bem definidas e baixo acoplamento.

---

# Pipeline de Processamento

Todo Workflow segue o mesmo ciclo.

```text id="msb8j8"
Receber solicitação

↓

Validar ambiente

↓

Executar etapa

↓

Persistir resultados

↓

Atualizar progresso

↓

Registrar logs

↓

Finalizar execução
```

Esse pipeline deve ser utilizado independentemente da etapa executada.

---

# Serviços Externos

O módulo depende dos seguintes serviços.

| Serviço                   | Finalidade                  |
| ------------------------- | --------------------------- |
| PostgreSQL                | Persistência principal      |
| Biblioteca (Google Drive) | Fonte física das obras      |
| MangaUpdates              | IDs e metadados             |
| Notion                    | Sincronização da biblioteca |

Cada integração deve ser desacoplada e substituível.

---

# Comunicação com a Interface

A interface deve consumir exclusivamente os endpoints públicos do módulo Fluxos.

Não é permitido:

* acesso direto ao banco;
* leitura direta de arquivos;
* chamadas diretas às APIs externas.

Todo acesso deve ocorrer por meio do Backend.

---

# Princípios Arquiteturais

O módulo Fluxos deve seguir os seguintes princípios:

* responsabilidade única por componente;
* separação entre orquestração e processamento;
* baixo acoplamento entre integrações;
* processamento resiliente;
* operações idempotentes sempre que possível;
* tratamento explícito de falhas;
* observabilidade completa.

---

# Estratégia de Evolução

Novas funcionalidades devem ser incorporadas respeitando a arquitetura existente.

Sempre que uma nova etapa ou integração for adicionada:

1. atualizar a Documentação Técnica;
2. revisar os contratos da API;
3. atualizar os testes;
4. revisar os checklists.

---

# Relação com os demais artefatos

```text id="yymj6b"
Histórias de Usuário

↓

Especificação Funcional

↓

Documentação Técnica

↓

Implementação

↓

Testes

↓

Manual do Usuário
```

Esta documentação serve como referência direta para implementação e manutenção do módulo.

---

# Público-alvo

Este diretório destina-se a:

* Desenvolvedores Back-end;
* Desenvolvedores Front-end;
* Arquitetos de Software;
* Tech Leads;
* QA;
* DevOps.

---

# Convenções

Ao longo da documentação serão utilizados os seguintes termos.

| Termo        | Significado                                          |
| ------------ | ---------------------------------------------------- |
| Workflow     | Processo completo de execução dos Fluxos             |
| Orchestrator | Componente responsável por coordenar todas as etapas |
| Etapa        | Unidade funcional do Workflow                        |
| Service      | Camada de regras de negócio                          |
| Repository   | Camada de acesso a dados                             |
| DTO          | Objeto de transferência entre camadas                |
| ViewModel    | Estrutura enviada para a interface                   |

---

# Leitura Recomendada

A leitura deve seguir esta ordem:

1. 01-visao-geral.md
2. 02-arquitetura.md
3. 03-api-e-contratos.md
4. 04-processamento.md
5. 05-integracoes.md
6. 06-performance-e-tratamento-de-erros.md
7. 07-testes.md
8. 08-checklists.md

Essa sequência acompanha o aprofundamento natural da arquitetura do módulo.

---

# Conclusão

A Documentação Técnica do módulo **Fluxos** estabelece a base de engenharia para implementação do principal processo operacional da Manhwateca. Ao definir arquitetura, contratos, processamento, integrações, requisitos de qualidade e estratégias de validação, ela fornece um guia completo para o desenvolvimento, manutenção e evolução do Workflow, garantindo consistência entre implementação e requisitos de negócio.
