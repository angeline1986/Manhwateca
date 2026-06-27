# Dashboard — Documentação Técnica

## 14 - Checklist de Code Review

---

# Objetivo

Este documento define os critérios oficiais de revisão de código (Code Review) para o módulo **Dashboard** da Manhwateca.

Seu propósito é garantir que toda alteração submetida ao repositório mantenha os padrões arquiteturais, de qualidade, desempenho, segurança e manutenibilidade estabelecidos para o projeto.

O checklist deve ser utilizado por revisores técnicos antes da aprovação de qualquer Pull Request relacionado ao Dashboard.

---

# Como utilizar este checklist

Cada item deve ser validado durante a revisão.

Legenda:

* ☐ Não verificado
* ☑ Conforme
* ⚠ Requer ajustes
* ❌ Reprovado
* N/A Não aplicável

Nenhum Pull Request deve ser aprovado com itens críticos marcados como ❌.

---

# 1. Arquitetura

## Separação de Responsabilidades

* ☐ Controllers não implementam regras de negócio.
* ☐ Controllers não executam SQL.
* ☐ Services concentram a lógica de negócio.
* ☐ Repositories apenas acessam dados.
* ☐ Frontend não contém lógica de negócio.
* ☐ DashboardAggregationService permanece como ponto único de agregação.

---

## Dependências

* ☐ Não há dependências circulares.
* ☐ Não foram introduzidos acoplamentos desnecessários.
* ☐ As dependências são injetadas, não instanciadas diretamente.
* ☐ Novas abstrações seguem o padrão arquitetural existente.

---

# 2. API

## Endpoint

* ☐ O contrato da API permaneceu compatível.
* ☐ Não houve remoção de campos públicos.
* ☐ Novos campos são opcionais ou versionados.
* ☐ O endpoint continua retornando um único DashboardViewModel.

---

## Serialização

* ☐ Datas em ISO-8601.
* ☐ Arrays vazios retornam `[]`.
* ☐ Objetos vazios retornam `{}` quando apropriado.
* ☐ Não existem valores `null` desnecessários.
* ☐ Tipos primitivos permanecem consistentes.

---

# 3. Backend

## DashboardAggregationService

* ☐ Não contém SQL.
* ☐ Não contém código de apresentação.
* ☐ Trata falhas parciais corretamente.
* ☐ Mantém a agregação centralizada.

---

## Repositories

* ☐ Consultas otimizadas.
* ☐ Sem duplicação de SQL.
* ☐ Sem consultas N+1.
* ☐ Índices considerados nas novas consultas.
* ☐ Apenas operações de persistência.

---

# 4. Frontend

## Componentes

* ☐ Responsabilidade única.
* ☐ Sem dependência entre componentes irmãos.
* ☐ Componentes reutilizáveis.
* ☐ Sem chamadas HTTP diretas fora da camada apropriada.

---

## Estados

* ☐ Loading implementado.
* ☐ Success implementado.
* ☐ Empty quando aplicável.
* ☐ Error quando aplicável.
* ☐ Refreshing implementado na DashboardPage.

---

# 5. Navegação

* ☐ Rotas continuam consistentes.
* ☐ Deep links permanecem válidos.
* ☐ Navegação não quebra histórico.
* ☐ Destinos continuam sendo definidos pelo Backend quando necessário.

---

# 6. Performance

* ☐ Não foram introduzidas consultas desnecessárias.
* ☐ Não existem loops com consultas ao banco.
* ☐ Não existe carregamento de entidades completas para métricas.
* ☐ Cache permanece consistente.
* ☐ Não há múltiplas chamadas ao endpoint do Dashboard.

---

# 7. Tratamento de Erros

* ☐ Exceções específicas utilizadas.
* ☐ Logs estruturados preservados.
* ☐ Nenhuma exceção silenciosamente ignorada.
* ☐ Mensagens ao usuário permanecem amigáveis.
* ☐ Informações sensíveis não são expostas.

---

# 8. Segurança

* ☐ Não há credenciais no código.
* ☐ Dados internos não são expostos na API.
* ☐ Entradas são validadas.
* ☐ Tratamento seguro de exceções.

---

# 9. Acessibilidade

* ☐ HTML semântico preservado.
* ☐ Navegação por teclado funcional.
* ☐ Foco visível.
* ☐ ARIA utilizada apenas quando necessário.
* ☐ Componentes continuam compatíveis com leitores de tela.

---

# 10. Testes

## Unitários

* ☐ Novas funcionalidades possuem testes.
* ☐ Casos de erro testados.
* ☐ Casos de borda testados.

---

## Integração

* ☐ API validada.
* ☐ Banco validado.
* ☐ Integrações simuladas corretamente.

---

## Frontend

* ☐ Componentes renderizam corretamente.
* ☐ Estados cobertos.
* ☐ Navegação validada.

---

## Regressão

* ☐ Nenhuma funcionalidade existente foi impactada.
* ☐ Fluxo principal do Dashboard permanece funcional.

---

# 11. Qualidade do Código

* ☐ Código legível.
* ☐ Nomes claros.
* ☐ Métodos curtos.
* ☐ Classes coesas.
* ☐ Comentários apenas quando agregam valor.
* ☐ Sem código morto.
* ☐ Sem duplicação significativa.

---

# 12. Observabilidade

* ☐ Logs continuam consistentes.
* ☐ Request ID preservado.
* ☐ Métricas de execução registradas.
* ☐ Erros críticos monitoráveis.

---

# 13. Documentação

Antes da aprovação, verificar se a alteração exige atualização da documentação.

## User Stories

* ☐ Atualizadas quando necessário.

## Especificação Funcional

* ☐ Atualizada quando houve alteração funcional.

## Documentação Técnica

* ☐ Atualizada quando houve alteração arquitetural.

## Manual do Usuário

* ☐ Atualizado quando houve alteração perceptível ao usuário.

---

# 14. Critérios de Aprovação

O Pull Request somente deve ser aprovado quando:

* ☑ Todos os testes passarem.
* ☑ O contrato da API permanecer compatível.
* ☑ A cobertura mínima de testes for mantida.
* ☑ O Dashboard continuar atendendo aos requisitos de desempenho.
* ☑ Não houver regressões conhecidas.
* ☑ A documentação estiver consistente.
* ☑ Todos os itens críticos deste checklist estiverem conformes.

---

# Perguntas para o Revisor

Antes de aprovar o código, responda às seguintes perguntas:

1. A alteração respeita a arquitetura definida para o Dashboard?
2. O código seria facilmente compreendido por outro desenvolvedor da equipe?
3. Há alguma simplificação possível sem perda de clareza?
4. Existe duplicação que possa ser eliminada?
5. A alteração impacta desempenho ou escalabilidade?
6. O tratamento de erros continua consistente?
7. A experiência do usuário foi preservada?
8. A alteração exige atualização de documentação?
9. Existem riscos para futuras evoluções do módulo?
10. Eu me sentiria confortável em manter este código pelos próximos anos?

Se qualquer resposta indicar um risco significativo, a revisão deve solicitar ajustes antes da aprovação.

---

# Critérios para Merge

Um Pull Request poderá ser integrado à branch principal apenas quando:

* todas as verificações automatizadas forem aprovadas;
* todos os comentários obrigatórios da revisão forem resolvidos;
* o checklist estiver concluído;
* não existirem bloqueios funcionais, arquiteturais ou de segurança;
* houver pelo menos uma aprovação técnica.

---

# Referências

Este checklist complementa:

* `01-visao-geral.md`
* `02-arquitetura.md`
* `03-api-dashboard.md`
* `04-modelo-de-dados.md`
* `05-componentes.md`
* `06-estados.md`
* `07-navegacao.md`
* `08-atualizacao.md`
* `09-tratamento-de-erros.md`
* `10-performance.md`
* `11-acessibilidade.md`
* `12-testes.md`
* `13-checklist-de-implementacao.md`

---

# Conclusão

O processo de Code Review é uma etapa fundamental para garantir a qualidade contínua do Dashboard. Este checklist padroniza os critérios de avaliação, reduz subjetividades e assegura que toda alteração preserve a arquitetura, a performance, a segurança e a experiência do usuário definidas para a Manhwateca. Um Pull Request somente deve ser considerado apto para merge quando atender integralmente aos requisitos técnicos e documentais aqui estabelecidos.
