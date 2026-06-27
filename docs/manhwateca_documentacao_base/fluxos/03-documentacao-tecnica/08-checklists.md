# Checklists

> Documento: **08-checklists.md**

---

# Objetivo

Este documento consolida os checklists técnicos utilizados durante o desenvolvimento do módulo **Fluxos** da Manhwateca.

Seu objetivo é padronizar critérios de implementação, revisão de código, testes e publicação, garantindo consistência entre diferentes desenvolvedores e reduzindo a probabilidade de regressões.

Os checklists aqui descritos devem ser utilizados durante todo o ciclo de vida do módulo, desde a implementação de novas funcionalidades até sua disponibilização em produção.

---

# Checklist de Implementação

Antes de considerar uma funcionalidade concluída, verifique os itens abaixo.

## Arquitetura

* [ ] A responsabilidade da funcionalidade está na camada correta.
* [ ] Não foram adicionadas regras de negócio ao Controller.
* [ ] O Workflow Orchestrator apenas coordena a execução.
* [ ] Services implementam apenas regras da própria etapa.
* [ ] Repositories realizam somente acesso aos dados.
* [ ] Não existe acoplamento direto entre UI e banco de dados.
* [ ] Dependências externas são acessadas apenas por Clients especializados.

---

## Workflow

* [ ] A nova funcionalidade respeita a ordem das etapas.
* [ ] Não altera o comportamento das demais etapas.
* [ ] Atualiza corretamente o progresso.
* [ ] Atualiza corretamente o estado da execução.
* [ ] Permite reprocessamento quando aplicável.
* [ ] Trata cancelamento corretamente.
* [ ] Mantém idempotência sempre que possível.

---

## Persistência

* [ ] Operações utilizam Repository.
* [ ] Transações possuem escopo mínimo.
* [ ] Persistência incremental implementada quando necessária.
* [ ] Não existem consultas SQL duplicadas.
* [ ] Não existem consultas dentro de loops sem necessidade.
* [ ] Índices utilizados continuam adequados.

---

## Integrações

* [ ] Timeout configurado.
* [ ] Retry configurado apenas para erros temporários.
* [ ] Tratamento adequado de respostas inválidas.
* [ ] Tokens e credenciais não aparecem em logs.
* [ ] Erros das integrações são encapsulados.
* [ ] Clients permanecem desacoplados do restante da aplicação.

---

## Interface

* [ ] Estados atualizados corretamente.
* [ ] Barra de progresso consistente.
* [ ] Mensagens compreensíveis.
* [ ] Nenhuma mensagem técnica exposta ao usuário.
* [ ] Navegação preserva o estado do Workflow.

---

# Checklist de Code Review

Toda Pull Request deve ser avaliada utilizando os critérios abaixo.

## Arquitetura

* [ ] Código segue a arquitetura definida.
* [ ] Não introduz novas dependências desnecessárias.
* [ ] Responsabilidades permanecem separadas.
* [ ] Componentes continuam reutilizáveis.

---

## Código

* [ ] Métodos possuem responsabilidade única.
* [ ] Complexidade ciclomática adequada.
* [ ] Nomes claros e consistentes.
* [ ] Código duplicado evitado.
* [ ] Comentários apenas quando agregam contexto.

---

## Tratamento de Erros

* [ ] Todas as exceções relevantes são tratadas.
* [ ] Nenhuma exceção é silenciosamente ignorada.
* [ ] Logs possuem contexto suficiente.
* [ ] Mensagens ao usuário permanecem compreensíveis.

---

## Performance

* [ ] Não existem consultas redundantes.
* [ ] Não existem loops desnecessários.
* [ ] Recursos externos são reutilizados quando possível.
* [ ] Objetos temporários são liberados adequadamente.

---

## Segurança

* [ ] Entradas são validadas.
* [ ] Nenhuma credencial aparece no código.
* [ ] Dados sensíveis não são registrados em logs.
* [ ] Contratos públicos permanecem compatíveis.

---

# Checklist de Testes

Antes da aprovação final:

## Testes Unitários

* [ ] Novos serviços possuem testes.
* [ ] Novos métodos possuem cobertura.
* [ ] Casos de erro foram testados.
* [ ] Casos limite foram considerados.

---

## Testes de Integração

* [ ] PostgreSQL validado.
* [ ] Biblioteca validada.
* [ ] MangaUpdates validado.
* [ ] Notion validado.

---

## Testes End-to-End

* [ ] Workflow completo executado.
* [ ] Cancelamento validado.
* [ ] Reprocessamento validado.
* [ ] Cenários de falha executados.

---

# Checklist de Documentação

* [ ] Histórias de Usuário atualizadas.
* [ ] Especificação Funcional revisada.
* [ ] Documentação Técnica atualizada.
* [ ] Manual do Usuário atualizado.
* [ ] Diagramas revisados (quando aplicável).

---

# Checklist para Publicação

Antes de disponibilizar uma nova versão:

## Validação

* [ ] Todos os testes aprovados.
* [ ] Cobertura mínima mantida.
* [ ] Sem falhas críticas abertas.
* [ ] Sem pendências bloqueantes.

---

## Workflow

* [ ] Execução completa validada.
* [ ] Integrações funcionando.
* [ ] Dashboard atualizado corretamente.
* [ ] Histórico funcionando.
* [ ] Logs produzidos corretamente.

---

## Qualidade

* [ ] Lint sem erros.
* [ ] Formatação aplicada.
* [ ] Dependências atualizadas.
* [ ] Versão documentada.

---

# Critérios de Aceitação

Uma funcionalidade do módulo Fluxos somente poderá ser considerada concluída quando:

* toda implementação estiver de acordo com a arquitetura definida;
* todos os testes obrigatórios forem aprovados;
* a documentação estiver atualizada;
* o comportamento do Workflow permanecer consistente;
* não houver regressões identificadas;
* a revisão de código for aprovada.

---

# Relação com os Demais Documentos

| Documento                               | Complementa                           |
| --------------------------------------- | ------------------------------------- |
| 02-arquitetura.md                       | Critérios arquiteturais               |
| 03-api-e-contratos.md                   | Validação dos contratos públicos      |
| 04-processamento.md                     | Fluxo interno do Workflow             |
| 05-integracoes.md                       | Boas práticas das integrações         |
| 06-performance-e-tratamento-de-erros.md | Critérios de desempenho e resiliência |
| 07-testes.md                            | Estratégia de validação               |

---

# Conclusão

Os checklists apresentados neste documento formalizam os critérios mínimos de qualidade para o desenvolvimento do módulo **Fluxos**. Sua utilização sistemática durante implementação, revisão, testes e publicação contribui para manter a arquitetura consistente, reduzir regressões e garantir que novas funcionalidades sejam incorporadas ao Workflow de maneira segura, previsível e alinhada aos padrões definidos para a Manhwateca.
