# Visão Geral

> Documento: **01-visao-geral.md**

---

# Objetivo

A página **Fluxos** constitui o principal módulo operacional da Manhwateca. É por meio dela que todas as atividades de processamento da biblioteca são executadas de forma controlada, rastreável e previsível.

Enquanto o Dashboard responde à pergunta **"Qual é o estado atual da biblioteca?"**, a página Fluxos responde **"O que deve ser processado agora?"** e **"Como esse processamento será executado?"**.

Seu objetivo é centralizar todas as operações responsáveis por transformar uma biblioteca de arquivos em uma coleção estruturada, enriquecida e sincronizada com os serviços externos utilizados pela aplicação.

---

# Papel dentro da Manhwateca

A arquitetura funcional da aplicação pode ser representada da seguinte forma:

```text
                    Dashboard
                        │
                        ▼
                   Página Fluxos
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
 PostgreSQL      MangaUpdates       Notion
```

O Dashboard atua como centro de monitoramento.

A página Fluxos atua como centro de execução.

Os demais módulos consomem os resultados produzidos pelo Workflow.

---

# Objetivos Funcionais

O módulo Fluxos possui cinco objetivos principais:

* organizar automaticamente a biblioteca;
* identificar corretamente todas as obras;
* localizar e validar identificadores externos;
* atualizar metadados oficiais;
* sincronizar as informações com o Notion.

Esses objetivos são executados por meio de um Workflow sequencial.

---

# Workflow Operacional

O processamento completo segue a seguinte sequência:

```text
1. Organizar Biblioteca
          │
          ▼
2. Catalogar Obras
          │
          ▼
3. Resolver IDs
          │
          ▼
4. Atualizar Metadados
          │
          ▼
5. Sincronizar Notion
```

Cada etapa produz informações consumidas pela etapa seguinte.

Embora seja possível executar etapas individualmente, o fluxo completo representa o cenário operacional recomendado.

---

# Responsabilidades do Módulo

O módulo Fluxos é responsável por:

* preparar a biblioteca para processamento;
* manter o banco PostgreSQL consistente;
* integrar informações do MangaUpdates;
* sincronizar dados com o Notion;
* registrar histórico das execuções;
* produzir indicadores para o Dashboard;
* disponibilizar feedback contínuo ao usuário.

Não é responsabilidade deste módulo:

* exibir indicadores globais da aplicação;
* configurar integrações;
* consultar a biblioteca de forma analítica;
* gerar relatórios gerenciais.

---

# Estrutura da Página

A interface é composta por quatro áreas principais.

## Cabeçalho

Apresenta:

* título da página;
* descrição da funcionalidade;
* última execução;
* ações globais.

---

## Workflow

Área central responsável por exibir as cinco etapas do processamento.

Cada etapa apresenta:

* nome;
* descrição;
* estado atual;
* progresso;
* ação disponível.

---

## Painel de Execução

Durante o processamento, esta área apresenta:

* progresso global;
* progresso da etapa atual;
* mensagens de execução;
* estatísticas em tempo real.

---

## Resumo

Ao término da execução, apresenta:

* obras processadas;
* erros encontrados;
* alertas;
* duração;
* resultado final.

---

# Princípios Funcionais

A interface segue os seguintes princípios:

## Execução orientada

O usuário deve compreender claramente:

* qual etapa está sendo executada;
* o que já foi concluído;
* o que ainda falta.

---

## Transparência

Toda operação deve informar:

* início;
* progresso;
* conclusão;
* falha;
* motivo da falha quando aplicável.

---

## Não bloqueio

Sempre que possível:

* falhas localizadas não interrompem o Workflow;
* apenas a etapa afetada deve ser sinalizada;
* o restante do processamento continua normalmente.

---

## Reprocessamento

O sistema deve permitir que etapas sejam executadas novamente.

Exemplos:

* pesquisar novamente IDs;
* atualizar metadados;
* sincronizar novamente com o Notion.

Não é necessário reiniciar todo o Workflow para corrigir uma única etapa.

---

# Dependências

A execução do Workflow depende de:

| Serviço          | Obrigatório              |
| ---------------- | ------------------------ |
| PostgreSQL       | Sim                      |
| Biblioteca local | Sim                      |
| MangaUpdates     | Apenas para etapas 3 e 4 |
| Notion           | Apenas para etapa 5      |

Caso uma integração esteja indisponível, apenas as etapas dependentes deverão ser afetadas.

---

# Relação entre as Etapas

| Etapa                | Depende da anterior |
| -------------------- | ------------------- |
| Organizar Biblioteca | Não                 |
| Catalogar Obras      | Sim                 |
| Resolver IDs         | Sim                 |
| Atualizar Metadados  | Sim                 |
| Sincronizar Notion   | Sim                 |

Essa dependência garante consistência entre os dados produzidos por cada fase do processamento.

---

# Integração com o Dashboard

Após cada execução do Workflow, o Dashboard deve refletir automaticamente as alterações realizadas.

Exemplos:

* redução da quantidade de obras sem ID;
* atualização das integrações;
* atualização das pendências;
* atualização das métricas operacionais;
* atualização da próxima ação recomendada.

---

# Critérios Gerais de Funcionamento

O módulo deve garantir que:

* apenas uma execução completa ocorra por vez;
* o progresso seja continuamente atualizado;
* falhas sejam registradas;
* logs sejam preservados;
* o histórico da execução permaneça disponível;
* o usuário possa identificar facilmente o resultado de cada etapa.

---

# Relação com os demais documentos

| Documento                        | Conteúdo                               |
| -------------------------------- | -------------------------------------- |
| 02-interface-e-layout.md         | Organização visual da página           |
| 03-etapas-do-workflow.md         | Funcionamento de cada etapa            |
| 04-processamento-e-validacoes.md | Regras funcionais e validações         |
| 05-integracoes.md                | Comportamento das integrações          |
| 06-estados-e-mensagens.md        | Feedback visual e estados da interface |
| 07-regras-de-navegacao.md        | Fluxos de navegação                    |

---

# Conclusão

A página **Fluxos** representa o núcleo operacional da Manhwateca. Sua responsabilidade é conduzir, de forma segura e rastreável, todo o processamento necessário para transformar uma biblioteca local em um catálogo estruturado, enriquecido e sincronizado com os serviços externos da aplicação. Todas as demais funcionalidades do sistema dependem, direta ou indiretamente, da correta execução deste Workflow.
