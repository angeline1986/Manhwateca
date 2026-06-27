# Regras de Navegação

> Documento: **07-regras-de-navegacao.md**

---

# Objetivo

Este documento define o comportamento funcional da navegação da página **Fluxos**, estabelecendo como o usuário transita entre o Workflow e os demais módulos da Manhwateca, bem como as regras para preservar contexto, impedir ações inconsistentes e manter a continuidade da experiência durante o processamento.

---

# Objetivos da Navegação

A navegação deve garantir que o usuário consiga:

* iniciar um Workflow;
* acompanhar sua execução;
* consultar outros módulos quando permitido;
* retornar ao Workflow sem perda de contexto;
* identificar claramente sua localização na aplicação.

A navegação deve ser previsível, consistente e segura.

---

# Estrutura Geral

A página Fluxos faz parte da navegação principal da aplicação.

```text
Dashboard
    │
    ├────────► Biblioteca
    │
    ├────────► Fluxos
    │              │
    │              ├────────► Detalhes da Etapa
    │              ├────────► Histórico
    │              └────────► Configurações (quando aplicável)
    │
    └────────► Configurações
```

Fluxos deve permanecer acessível a partir do Dashboard e dos demais módulos principais.

---

# Entrada na Página

O usuário poderá acessar a página Fluxos por:

* Dashboard (ação recomendada);
* menu principal;
* atalho de navegação;
* link direto (deep link), quando suportado.

Ao entrar na página, o sistema deverá:

* carregar o estado atual do Workflow;
* recuperar a última execução;
* consultar o estado das integrações;
* apresentar imediatamente a etapa atual ou o resumo da última execução.

---

# Saída da Página

O usuário poderá sair da página para:

* Dashboard;
* Biblioteca;
* Configurações;
* outros módulos disponíveis.

A navegação deve respeitar o estado atual do Workflow.

---

# Navegação Durante o Workflow

## Sem execução em andamento

A navegação é totalmente livre.

O usuário poderá acessar qualquer módulo sem restrições.

---

## Execução em andamento

Quando existir um Workflow ativo, o sistema deve preservar a execução em segundo plano.

Ao tentar sair da página, a interface deve exibir uma confirmação.

Exemplo:

```text
Existe um Workflow em execução.

Deseja sair desta página?

O processamento continuará normalmente.

[Continuar na página]

[Sair]
```

O processamento nunca deve ser interrompido automaticamente pela navegação.

---

# Cancelamento

Caso o usuário escolha cancelar o Workflow, a confirmação deve ocorrer antes da interrupção.

Exemplo:

```text
Deseja cancelar o Workflow?

As etapas concluídas permanecerão registradas.

[Voltar]

[Cancelar Workflow]
```

Cancelar o Workflow é diferente de sair da página.

---

# Retorno à Página

Ao retornar para Fluxos durante uma execução ativa, a interface deve:

* recuperar automaticamente o estado atual;
* exibir a etapa em execução;
* atualizar o progresso;
* recuperar mensagens recentes.

O usuário nunca deve retornar para uma interface "zerada" enquanto houver processamento em andamento.

---

# Navegação para o Dashboard

Após a conclusão do Workflow, o usuário poderá retornar ao Dashboard.

Ao acessar o Dashboard, o sistema deverá apresentar os dados atualizados produzidos pelo Workflow.

Exemplos:

* métricas recalculadas;
* pendências reduzidas;
* nova ação recomendada;
* integrações atualizadas.

---

# Navegação para Biblioteca

Quando o Workflow modificar informações das obras, a Biblioteca deverá refletir essas alterações imediatamente após a conclusão da execução.

Não deve ser necessário reiniciar a aplicação.

---

# Deep Links

Quando suportado, a aplicação poderá abrir diretamente:

* uma etapa específica;
* o histórico da execução;
* detalhes de uma pendência.

Exemplos:

```text
/fluxos

/fluxos/ids

/fluxos/notion

/fluxos/historico
```

O sistema deve validar o contexto antes de permitir a navegação direta.

---

# Preservação de Estado

A navegação deve preservar:

* etapa atual;
* progresso;
* filtros aplicados;
* posição da rolagem (quando possível);
* mensagens relevantes da execução.

Essas informações devem ser restauradas automaticamente ao retornar para a página.

---

# Atualização da Interface

Sempre que o usuário retornar para Fluxos, o sistema deve verificar:

* estado do Workflow;
* estado das integrações;
* existência de novas mensagens;
* conclusão de etapas.

Caso existam alterações, a interface deve ser atualizada automaticamente.

---

# Navegação após Falhas

Quando uma etapa falhar, o usuário poderá:

* consultar os detalhes da falha;
* reexecutar apenas a etapa afetada (quando permitido);
* retornar ao Dashboard;
* acessar Configurações para verificar integrações.

Não deve ser necessário reiniciar todo o Workflow para corrigir falhas pontuais.

---

# Navegação após Conclusão

Ao concluir o Workflow, a interface deve oferecer ações rápidas como:

* visualizar resumo da execução;
* abrir Dashboard;
* acessar Biblioteca;
* sincronizar novamente (quando aplicável);
* iniciar nova execução.

Essas ações facilitam a continuidade do fluxo de trabalho.

---

# Breadcrumb

Quando utilizado, o breadcrumb deve indicar claramente a localização do usuário.

Exemplo:

```text
Dashboard
>
Fluxos
```

Se houver visualização de detalhes:

```text
Dashboard

>

Fluxos

>

Resolver IDs
```

---

# Consistência

A navegação deve obedecer aos seguintes princípios:

* nenhuma operação concluída pode ser perdida ao trocar de página;
* o usuário sempre deve saber onde está;
* mudanças de módulo não devem interromper o Workflow;
* toda navegação deve preservar a integridade do processamento.

---

# Relação com outros documentos

| Documento                        | Conteúdo relacionado          |
| -------------------------------- | ----------------------------- |
| 02-interface-e-layout.md         | Organização da interface      |
| 03-etapas-do-workflow.md         | Sequência das etapas          |
| 04-processamento-e-validacoes.md | Continuidade do processamento |
| 05-integracoes.md                | Dependências externas         |
| 06-estados-e-mensagens.md        | Mensagens durante a navegação |

---

# Conclusão

A navegação da página **Fluxos** foi concebida para acompanhar a natureza operacional do módulo. Como o Workflow pode executar tarefas longas e depender de múltiplas integrações, a interface deve preservar contexto, manter o processamento independente da navegação do usuário e garantir que o estado da execução seja sempre recuperado corretamente ao retornar à página. Dessa forma, a experiência permanece contínua, previsível e segura durante todo o ciclo operacional.
