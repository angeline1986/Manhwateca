# Histórias de Usuário — Módulo Fluxos

## Objetivo

Este diretório reúne todas as Histórias de Usuário do módulo **Fluxos** da Manhwateca.

Os Fluxos representam o núcleo operacional da aplicação. É neste módulo que o usuário executa todas as atividades responsáveis por transformar uma biblioteca de arquivos em uma coleção organizada, catalogada, enriquecida com metadados e sincronizada com o Notion.

Cada história de usuário descreve um conjunto de funcionalidades relacionadas a uma etapa específica do Workflow operacional, contendo:

* valor de negócio;
* objetivos do usuário;
* critérios de aceite;
* regras de negócio;
* pré-condições;
* pós-condições;
* exceções relevantes.

Este conjunto de documentos serve como base para a Especificação Funcional, Documentação Técnica, implementação e testes.

---

# Estrutura das Histórias

O Workflow do módulo Fluxos está dividido em seis grandes áreas funcionais.

| Documento                       | Etapa                                                   |
| ------------------------------- | ------------------------------------------------------- |
| 01-organizacao-da-biblioteca.md | Organização inicial da biblioteca                       |
| 02-catalogacao.md               | Catalogação das obras identificadas                     |
| 03-resolucao-de-ids.md          | Associação de IDs externos (MangaUpdates)               |
| 04-atualizacao-de-metadados.md  | Atualização de informações das obras                    |
| 05-sincronizacao-com-notion.md  | Sincronização com o banco de dados do Notion            |
| 06-finalizacao-do-workflow.md   | Encerramento, validação e consolidação do processamento |

Cada documento agrupa diversas Histórias de Usuário relacionadas ao mesmo domínio funcional, reduzindo fragmentação e facilitando a manutenção da documentação.

---

# Fluxo Operacional

O Workflow completo segue a sequência abaixo.

```text
Organizar Biblioteca
        │
        ▼
Catalogar Obras
        │
        ▼
Resolver IDs
        │
        ▼
Atualizar Metadados
        │
        ▼
Sincronizar Notion
        │
        ▼
Finalizar Workflow
```

Cada etapa depende da conclusão da etapa anterior, embora algumas possam ser executadas novamente de forma independente para corrigir inconsistências ou atualizar informações.

---

# Objetivos do Módulo

O módulo Fluxos possui os seguintes objetivos:

* organizar automaticamente a estrutura da biblioteca;
* identificar corretamente cada obra;
* localizar e validar identificadores externos;
* enriquecer o catálogo com metadados atualizados;
* sincronizar as informações com o Notion;
* reduzir atividades manuais do usuário;
* garantir rastreabilidade durante todo o processamento.

---

# Escopo

As Histórias de Usuário deste módulo abrangem:

* organização física dos arquivos;
* catalogação das obras;
* resolução de conflitos de identificação;
* integração com MangaUpdates;
* sincronização com Notion;
* acompanhamento do Workflow;
* reprocessamentos;
* validações de consistência.

Não fazem parte deste módulo:

* Dashboard;
* Configurações;
* Biblioteca (consulta);
* Relatórios.

Esses módulos possuem documentação própria.

---

# Convenções

Todas as histórias seguem a estrutura:

1. Objetivo.
2. Histórias de Usuário ("Como / Quero / Para que").
3. Critérios de Aceite.
4. Regras de Negócio.
5. Fluxo Principal.
6. Fluxos Alternativos.
7. Exceções.
8. Dependências.
9. Impactos em outros módulos.

Essa padronização facilita a rastreabilidade entre requisitos funcionais, implementação e testes.

---

# Rastreabilidade

As Histórias de Usuário servem como origem para os demais artefatos da documentação.

```text
Histórias de Usuário
        │
        ▼
Especificação Funcional
        │
        ▼
Documentação Técnica
        │
        ▼
Implementação
        │
        ▼
Testes
        │
        ▼
Manual do Usuário
```

Toda funcionalidade implementada deve possuir origem em uma História de Usuário correspondente.

---

# Dependências

As funcionalidades descritas neste diretório dependem da integração com:

* PostgreSQL;
* Google Drive (biblioteca de arquivos);
* MangaUpdates;
* Notion;
* Workflow Engine da Manhwateca.

Essas integrações são detalhadas na Documentação Técnica.

---

# Leitura Recomendada

A sequência recomendada para leitura da documentação do módulo Fluxos é:

1. Histórias de Usuário (este diretório).
2. Especificação Funcional.
3. Documentação Técnica.
4. Manual do Usuário.

Essa ordem acompanha a evolução natural do projeto, desde os requisitos de negócio até a utilização do sistema.

---

# Convenções de Evolução

Ao adicionar novas funcionalidades ao módulo Fluxos:

* novas Histórias de Usuário devem ser incorporadas ao documento da etapa correspondente;
* alterações de comportamento devem atualizar os critérios de aceite existentes;
* mudanças arquiteturais devem refletir na Documentação Técnica;
* alterações visíveis ao usuário devem atualizar o Manual do Usuário.

Essa estratégia mantém toda a documentação sincronizada e reduz divergências entre requisitos, implementação e operação.

---

# Documentos deste diretório

| Documento                       | Conteúdo                                                                    |
| ------------------------------- | --------------------------------------------------------------------------- |
| 01-organizacao-da-biblioteca.md | Organização e preparação da biblioteca para processamento                   |
| 02-catalogacao.md               | Identificação e catalogação das obras                                       |
| 03-resolucao-de-ids.md          | Associação e validação de identificadores externos                          |
| 04-atualizacao-de-metadados.md  | Atualização das informações das obras                                       |
| 05-sincronizacao-com-notion.md  | Integração e sincronização com o Notion                                     |
| 06-finalizacao-do-workflow.md   | Encerramento do Workflow, validações finais e consolidação do processamento |

---

# Conclusão

As Histórias de Usuário do módulo Fluxos representam a base funcional do principal processo operacional da Manhwateca. Elas descrevem o comportamento esperado do sistema sob a perspectiva do usuário e estabelecem os requisitos que orientarão todas as demais camadas da documentação e da implementação.
