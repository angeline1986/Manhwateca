# Dashboard — Documentação Técnica

## 13 - Checklist de Implementação

---

# Objetivo

Este documento apresenta o checklist oficial para implementação do módulo **Dashboard** da Manhwateca.

Seu objetivo é servir como guia de execução para desenvolvedores durante a construção do módulo, garantindo que todos os requisitos arquiteturais, funcionais e não funcionais definidos na documentação sejam atendidos antes da conclusão da implementação.

Este checklist não substitui as User Stories nem a Especificação Funcional. Ele consolida os requisitos técnicos que devem ser verificados durante o desenvolvimento.

---

# Como utilizar este checklist

Cada item deve ser marcado apenas após validação efetiva da implementação.

Legenda:

* ☐ Não iniciado
* ◐ Em andamento
* ☑ Concluído
* N/A Não aplicável

---

# 1. Estrutura do Projeto

## Organização

* ☐ Estrutura de diretórios criada conforme padrão do projeto.
* ☐ Controller do Dashboard implementado.
* ☐ DashboardAggregationService implementado.
* ☐ Repositories reutilizados, sem duplicação de código.
* ☐ ViewModel do Dashboard criado.
* ☐ Separação clara entre Controller, Services e Repositories.

---

# 2. API

## Endpoint

* ☐ Endpoint `GET /api/dashboard` criado.
* ☐ Endpoint retorna apenas JSON.
* ☐ Endpoint utiliza DashboardAggregationService.
* ☐ Não existem endpoints individuais para métricas, workflow ou integrações.

## Contrato

* ☐ Campo `generatedAt`.
* ☐ Campo `version`.
* ☐ Campo `status`.
* ☐ Campo `nextAction`.
* ☐ Campo `metrics`.
* ☐ Campo `workflow`.
* ☐ Campo `pendingActions`.
* ☐ Campo `integrations`.
* ☐ Campo `quickActions`.

---

# 3. DashboardAggregationService

* ☐ Consolida todos os serviços.
* ☐ Não executa SQL diretamente.
* ☐ Não acessa APIs externas diretamente.
* ☐ Constrói um único DashboardViewModel.
* ☐ Trata falhas parciais.
* ☐ Produz resposta consistente.

---

# 4. Repositories

## Banco de Dados

* ☐ Consultas agregadas implementadas.
* ☐ Não existem consultas duplicadas.
* ☐ Não existe `SELECT *` desnecessário.
* ☐ Índices necessários foram criados.
* ☐ Sem consultas N+1.

---

# 5. Frontend

## Página

* ☐ DashboardPage implementada.
* ☐ Apenas uma requisição HTTP.
* ☐ Componentes independentes.

---

## Header

* ☐ Título.
* ☐ Subtítulo.
* ☐ Data da última atualização.
* ☐ Botão Recarregar.

---

## Próxima Ação

* ☐ Card implementado.
* ☐ Navegação funcionando.
* ☐ Prioridade exibida corretamente.

---

## Métricas

* ☐ Biblioteca.
* ☐ Novos capítulos.
* ☐ Obras sem ID.
* ☐ Sincronizações pendentes.

---

## Workflow

* ☐ Barra de progresso.
* ☐ Estados das etapas.
* ☐ Destaque da etapa atual.

---

## Pendências

* ☐ Lista renderizada.
* ☐ Ordenação proveniente do Backend.
* ☐ Navegação funcionando.

---

## Integrações

* ☐ PostgreSQL.
* ☐ MangaUpdates.
* ☐ Notion.
* ☐ Biblioteca.

---

## Ações Rápidas

* ☐ Biblioteca.
* ☐ Fluxos.
* ☐ Configurações.
* ☐ Recarregar.

---

# 6. Estados

Cada componente deve implementar:

| Estado     | Validado          |
| ---------- | ----------------- |
| Loading    | ☐                 |
| Success    | ☐                 |
| Empty      | ☐                 |
| Error      | ☐                 |
| Refreshing | ☐ (DashboardPage) |

---

# 7. Navegação

* ☐ Rotas implementadas.
* ☐ Deep links funcionando.
* ☐ Histórico preservado.
* ☐ Retorno ao Dashboard.
* ☐ Refresh após retorno.

---

# 8. Atualização

* ☐ Refresh manual.
* ☐ Refresh automático.
* ☐ Atualização atômica.
* ☐ Apenas uma atualização simultânea.
* ☐ Cache utilizado corretamente.
* ☐ Invalidação implementada.

---

# 9. Tratamento de Erros

* ☐ Exceções tipadas.
* ☐ Logs estruturados.
* ☐ Falhas isoladas.
* ☐ Retry implementado.
* ☐ Mensagens amigáveis.
* ☐ Dashboard permanece operacional quando possível.

---

# 10. Performance

* ☐ Consultas agregadas.
* ☐ Índices criados.
* ☐ Sem consultas N+1.
* ☐ Cache configurado.
* ☐ Paralelismo implementado.
* ☐ Tempo da API ≤ 300 ms.
* ☐ Refresh ≤ 500 ms.

---

# 11. Acessibilidade

* ☐ HTML semântico.
* ☐ Navegação por teclado.
* ☐ Foco visível.
* ☐ Compatibilidade com leitores de tela.
* ☐ Contraste WCAG AA.
* ☐ Uso correto de ARIA.
* ☐ Componentes acessíveis.

---

# 12. Testes

## Unitários

* ☐ Repositories.
* ☐ Services.
* ☐ DashboardAggregationService.
* ☐ Controller.

---

## Integração

* ☐ API.
* ☐ PostgreSQL.
* ☐ Integrações.

---

## Frontend

* ☐ Componentes.
* ☐ Estados.
* ☐ Navegação.

---

## End-to-End

* ☐ Fluxo completo do Dashboard.
* ☐ Workflow.
* ☐ Refresh.
* ☐ Integrações.

---

# 13. Observabilidade

* ☐ Logs estruturados.
* ☐ Request ID implementado.
* ☐ Tempo de execução registrado.
* ☐ Erros registrados.
* ☐ Métricas de performance coletadas.

---

# 14. Segurança

* ☐ Dados sensíveis não retornados pela API.
* ☐ Mensagens técnicas ocultadas do usuário.
* ☐ Validação das entradas do endpoint.
* ☐ Tratamento seguro de exceções.

---

# 15. Documentação

Verificar se todos os documentos estão atualizados.

## User Stories

* ☐ Atualizadas.

## Especificação Funcional

* ☐ Atualizada.

## Documentação Técnica

* ☐ Atualizada.

## Manual do Usuário

* ☐ Atualizado.

---

# 16. Critérios para conclusão da implementação

O Dashboard somente poderá ser considerado concluído quando:

* ☑ Todas as User Stories estiverem implementadas.
* ☑ Todos os critérios de aceite estiverem atendidos.
* ☑ Todos os testes obrigatórios estiverem aprovados.
* ☑ O contrato da API estiver validado.
* ☑ A documentação estiver atualizada.
* ☑ O checklist de Code Review for aprovado.
* ☑ Não existirem bugs críticos ou bloqueadores.
* ☑ O módulo estiver apto para integração com os demais componentes da Manhwateca.

---

# Referências

Este checklist deve ser utilizado em conjunto com:

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
* `14-checklist-code-review.md`

---

# Conclusão

Este checklist consolida todos os requisitos técnicos necessários para a implementação do Dashboard. Seu uso reduz omissões durante o desenvolvimento, padroniza entregas entre diferentes desenvolvedores e garante que o módulo atenda aos padrões arquiteturais, funcionais, de qualidade e de desempenho definidos para a Manhwateca.
