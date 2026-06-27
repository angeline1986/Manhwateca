# Testes

> Documento: **07-testes.md**

---

# Objetivo

Este documento define a estratégia de testes do módulo **Fluxos**, estabelecendo como cada camada da arquitetura deve ser validada para garantir confiabilidade, previsibilidade e segurança durante a evolução da Manhwateca.

Os testes devem assegurar que o Workflow opere corretamente tanto em cenários normais quanto em situações de erro, preservando a integridade dos dados e das integrações externas.

---

# Objetivos da Estratégia de Testes

A suíte de testes deve garantir que:

* todas as etapas do Workflow executem corretamente;
* alterações em uma etapa não impactem as demais;
* integrações externas possam ser simuladas;
* regressões sejam detectadas rapidamente;
* erros sejam reproduzíveis.

---

# Pirâmide de Testes

A estratégia adotada segue a pirâmide clássica.

```text
                Testes E2E
                     ▲
                     │
          Testes de Integração
                     ▲
                     │
            Testes Unitários
```

A maior parte da cobertura deve estar concentrada nos testes unitários.

---

# Testes Unitários

## Objetivo

Validar individualmente cada componente sem dependência de banco de dados, APIs externas ou sistema de arquivos.

Cada teste deve isolar completamente a unidade sob teste.

---

## Componentes Cobertos

* WorkflowOrchestrator
* OrganizationService
* CatalogService
* IdResolutionService
* MetadataService
* NotionSyncService
* Repository Layer
* Clients
* Helpers
* Validators

---

## Dependências

Todas as dependências externas devem ser substituídas por:

* Mock
* Stub
* Fake

Nunca utilizar serviços reais em testes unitários.

---

## Exemplos

### WorkflowOrchestrator

Validar:

* sequência correta das etapas;
* interrupção quando necessário;
* atualização do progresso;
* tratamento de exceções.

---

### MetadataService

Validar:

* atualização de metadados;
* tratamento de respostas inválidas;
* preservação de dados locais;
* elegibilidade das obras.

---

### NotionSyncService

Validar:

* criação de páginas;
* atualização de páginas;
* tratamento de conflitos;
* registro de falhas.

---

# Testes de Integração

## Objetivo

Validar a comunicação entre componentes reais da aplicação.

Esses testes verificam contratos, persistência e integração entre camadas.

---

## Cenários

### PostgreSQL

Validar:

* leitura;
* escrita;
* transações;
* rollback;
* consultas.

---

### MangaUpdates

Validar:

* consulta por ID;
* consulta por título;
* atualização de metadados;
* tratamento de timeout.

Preferencialmente utilizando ambiente de testes ou respostas simuladas.

---

### Notion

Validar:

* criação de páginas;
* atualização;
* consulta;
* autenticação;
* tratamento de erros.

---

### Biblioteca

Validar:

* leitura dos diretórios;
* detecção de novas obras;
* alterações estruturais.

Utilizar diretórios temporários durante os testes.

---

# Testes End-to-End (E2E)

## Objetivo

Validar o comportamento completo do Workflow sob a perspectiva do usuário.

Esses testes percorrem todas as camadas da aplicação.

---

## Fluxo Principal

```text
Usuário inicia Workflow

↓

Organização

↓

Catalogação

↓

Resolução de IDs

↓

Atualização de Metadados

↓

Sincronização

↓

Resumo Final
```

O teste deve validar que todas as etapas foram concluídas corretamente.

---

# Cenários Obrigatórios

## Execução completa

Resultado esperado:

* Workflow concluído;
* todas as etapas executadas;
* Dashboard atualizado.

---

## Biblioteca vazia

Resultado esperado:

* nenhuma obra processada;
* Workflow concluído sem erro.

---

## Sem conexão com PostgreSQL

Resultado esperado:

* Workflow não iniciado;
* mensagem adequada.

---

## MangaUpdates indisponível

Resultado esperado:

* Organização e Catalogação concluídas;
* Resolução de IDs interrompida;
* Workflow encerrado com alertas.

---

## Notion indisponível

Resultado esperado:

* etapas anteriores preservadas;
* falha restrita à sincronização.

---

## Cancelamento

Resultado esperado:

* operação interrompida com segurança;
* progresso preservado;
* histórico atualizado.

---

# Testes de Regressão

Sempre que uma alteração for realizada em qualquer etapa do Workflow, devem ser executados:

* todos os testes unitários da etapa;
* testes de integração relacionados;
* testes E2E principais.

Nenhuma alteração deve ser entregue sem validação da regressão.

---

# Cobertura

Metas recomendadas.

| Camada       | Cobertura mínima |
| ------------ | ---------------: |
| Services     |              90% |
| Orchestrator |              95% |
| Repositories |              85% |
| Clients      |              80% |
| Controllers  |              80% |

Cobertura não substitui qualidade dos cenários.

---

# Dados de Teste

Os testes devem utilizar conjuntos de dados controlados.

Exemplos:

* biblioteca pequena;
* biblioteca grande;
* obras sem ID;
* obras duplicadas;
* metadados incompletos;
* páginas inexistentes no Notion.

Os dados devem ser determinísticos para permitir repetibilidade.

---

# Testes de Performance

Executar cenários representativos para medir:

* tempo total do Workflow;
* tempo por etapa;
* consumo de memória;
* número de consultas ao banco;
* quantidade de chamadas às APIs.

Esses testes não precisam ser executados em toda alteração, mas devem fazer parte do ciclo de validação periódica.

---

# Automação

Todos os testes devem ser executados automaticamente no pipeline de integração contínua.

Fluxo recomendado:

```text
Commit

↓

Lint

↓

Testes Unitários

↓

Testes de Integração

↓

Testes E2E

↓

Build
```

Uma falha em qualquer etapa deve impedir a publicação da aplicação.

---

# Critérios de Aprovação

Uma alteração poderá ser considerada pronta quando:

* todos os testes forem aprovados;
* nenhuma regressão for identificada;
* cobertura mínima for mantida;
* contratos públicos permanecerem compatíveis;
* novas funcionalidades possuírem testes correspondentes.

---

# Relação com os Demais Documentos

| Documento             | Complementa                          |
| --------------------- | ------------------------------------ |
| 02-arquitetura.md     | Componentes testados                 |
| 03-api-e-contratos.md | Validação dos contratos              |
| 04-processamento.md   | Fluxos executados                    |
| 05-integracoes.md     | Estratégia de mocks e integrações    |
| 08-checklists.md      | Critérios de implementação e revisão |

---

# Conclusão

A estratégia de testes do módulo **Fluxos** busca garantir um Workflow confiável, evolutivo e de fácil manutenção. A combinação de testes unitários, de integração, End-to-End, regressão e desempenho fornece uma cobertura abrangente sobre todas as camadas da arquitetura, reduzindo riscos de falhas em produção e assegurando que a evolução do sistema preserve o comportamento esperado.
