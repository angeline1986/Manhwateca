# Dashboard — Especificação Funcional

## 10 - Atualização do Dashboard

---

# Objetivo do Documento

Este documento especifica o comportamento funcional do processo de atualização do Dashboard da Manhwateca.

A atualização permite que o usuário obtenha a versão mais recente das informações exibidas na página sem necessidade de recarregar toda a aplicação.

Esta documentação implementa a **US-008 — Atualizar os dados do Dashboard**.

---

# Objetivo da Funcionalidade

A atualização do Dashboard deve:

* consultar novamente os dados consolidados da aplicação;
* atualizar todos os componentes da página de forma consistente;
* preservar a navegação e o estado visual da interface;
* evitar a necessidade de recarregar o navegador.

A atualização não executa nenhuma etapa do Workflow.

---

# User Story Relacionada

| ID     | Título                          |
| ------ | ------------------------------- |
| US-008 | Atualizar os dados do Dashboard |

---

# Escopo

Esta funcionalidade é responsável apenas por atualizar as informações exibidas na página.

Ela **não deve**:

* organizar a biblioteca;
* catalogar arquivos;
* resolver IDs;
* atualizar metadados;
* sincronizar o Notion;
* alterar configurações.

Toda atualização é exclusivamente de leitura.

---

# Ponto de Entrada

A atualização pode ser iniciada pelos seguintes eventos:

| Origem                | Descrição                                                         |
| --------------------- | ----------------------------------------------------------------- |
| Botão "Recarregar"    | Atualização manual iniciada pelo usuário                          |
| Abertura do Dashboard | Carregamento inicial da página                                    |
| Retorno de um módulo  | Atualização após concluir uma operação em Fluxos ou Configurações |

Independentemente da origem, o comportamento deve ser o mesmo.

---

# Fluxo Funcional

```text id="3v3ij6"
Usuário

↓

Solicita atualização

↓

GET /api/dashboard

↓

Backend consolida os dados

↓

Resposta recebida

↓

Dashboard atualiza todos os componentes

↓

Fim
```

---

# Fonte de Dados

O Dashboard deve consumir exclusivamente um endpoint agregador.

```http
GET /api/dashboard
```

Este endpoint é responsável por fornecer todas as informações necessárias para renderizar a página.

O Dashboard não deve realizar múltiplas chamadas independentes para atualizar componentes individuais.

---

# Componentes Atualizados

Durante a atualização, todos os componentes devem receber novos dados.

| Componente                | Atualizado |
| ------------------------- | ---------- |
| Cabeçalho                 | Sim        |
| Próximo Passo Recomendado | Sim        |
| Métricas                  | Sim        |
| Pendências                | Sim        |
| Integrações               | Sim        |
| Workflow                  | Sim        |

A atualização deve ser atômica.

---

# Atualização Atômica

O Dashboard não deve atualizar componentes individualmente à medida que as respostas forem chegando.

O fluxo correto é:

1. solicitar os dados;
2. aguardar a resposta completa;
3. substituir o estado atual da página;
4. renderizar novamente todos os componentes.

Isso evita inconsistências visuais.

---

# Estados da Atualização

## Idle

Nenhuma atualização em andamento.

---

## Refreshing

A atualização está sendo executada.

Durante esse estado:

* botão Recarregar permanece desabilitado;
* indicador de carregamento é exibido;
* os dados atuais permanecem visíveis.

---

## Success

Atualização concluída.

O Dashboard passa a utilizar o novo conjunto de dados.

A data de última atualização é atualizada.

---

## Error

A atualização falhou.

O Dashboard continua exibindo os dados anteriormente carregados.

---

# Regras Funcionais

## RF-001

A atualização nunca deve executar processos operacionais.

---

## RF-002

A atualização deve consumir exclusivamente o endpoint agregador.

---

## RF-003

Não deve existir mais de uma atualização simultânea.

---

## RF-004

Uma nova solicitação de atualização deve ser ignorada enquanto outra estiver em andamento.

---

## RF-005

Em caso de erro, o estado anterior da interface deve ser preservado.

---

## RF-006

Todos os componentes devem ser atualizados utilizando o mesmo conjunto de dados.

---

## RF-007

A atualização não deve provocar mudança de rota.

---

## RF-008

A posição de rolagem da página deve ser preservada.

---

## RF-009

A atualização não deve reinicializar componentes da interface desnecessariamente.

---

## RF-010

O Dashboard deve permanecer utilizável durante a atualização.

---

# Eventos

## EVT-001

Usuário seleciona **Recarregar**.

Resultado:

Nova atualização iniciada.

---

## EVT-002

Resposta recebida com sucesso.

Resultado:

Todos os componentes são atualizados.

---

## EVT-003

Erro durante a atualização.

Resultado:

Os dados anteriores permanecem visíveis.

---

# Mensagens

## Atualização iniciada

```text
Atualizando informações...
```

---

## Atualização concluída

```text
Dashboard atualizado com sucesso.
```

---

## Erro

```text
Não foi possível atualizar as informações.
```

---

## Sem alterações

```text
Nenhuma alteração encontrada.
```

---

# Responsividade

O comportamento da atualização deve ser idêntico em todas as resoluções.

A única diferença permitida é a posição do indicador visual de carregamento, conforme o layout definido para Desktop, Tablet ou Mobile.

---

# Acessibilidade

Durante a atualização:

* o botão Recarregar deve indicar claramente que está desabilitado;
* tecnologias assistivas devem ser notificadas quando a atualização iniciar e terminar;
* mensagens de erro devem ser anunciadas de forma acessível.

---

# Dependências

Esta funcionalidade depende de:

* Dashboard API;
* Sistema de Navegação;
* Componentes do Dashboard.

Nenhum componente deve iniciar atualizações independentes.

---

# Critérios de Aceite

A funcionalidade será considerada conforme esta especificação quando:

* atualizar todos os componentes da página utilizando uma única chamada à API;
* impedir atualizações simultâneas;
* preservar a posição da página durante o processo;
* manter os dados anteriores em caso de falha;
* atualizar a informação de "Última atualização" após sucesso;
* não executar processos operacionais;
* manter a interface utilizável durante toda a atualização.
