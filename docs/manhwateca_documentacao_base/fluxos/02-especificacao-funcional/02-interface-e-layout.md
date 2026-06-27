# Interface e Layout

> Documento: **02-interface-e-layout.md**

---

# Objetivo

Este documento define a organização visual e o comportamento funcional da interface da página **Fluxos**.

Seu objetivo é estabelecer uma estrutura consistente para a execução do Workflow da Manhwateca, permitindo que o usuário compreenda facilmente o estado atual do processamento, acompanhe sua evolução e execute ações de forma segura e previsível.

O layout deve privilegiar clareza, orientação e feedback contínuo.

---

# Estrutura Geral da Página

A interface é composta por cinco regiões principais.

```text
┌──────────────────────────────────────────────────────────────┐
│ Cabeçalho                                                    │
├──────────────────────────────────────────────────────────────┤
│ Barra de Progresso Global                                    │
├──────────────────────────────────────────────────────────────┤
│ Workflow                                                     │
│                                                              │
│ ① Organizar Biblioteca                                       │
│ ② Catalogar Obras                                            │
│ ③ Resolver IDs                                               │
│ ④ Atualizar Metadados                                        │
│ ⑤ Sincronizar Notion                                         │
├──────────────────────────────────────────────────────────────┤
│ Painel de Execução                                            │
├──────────────────────────────────────────────────────────────┤
│ Resumo da Execução                                            │
└──────────────────────────────────────────────────────────────┘
```

Cada região possui responsabilidades específicas e deve permanecer visível durante toda a execução do Workflow.

---

# Cabeçalho

A região superior deve apresentar:

* título da página;
* descrição resumida;
* data e horário da última execução;
* botão **Executar Workflow**;
* botão **Cancelar Execução** (quando houver processamento ativo).

Exemplo:

```text
Fluxos

Execute e acompanhe todas as etapas de processamento da biblioteca.

Última execução:
26/06/2026 20:35

[Executar Workflow]
```

---

# Barra de Progresso Global

Logo abaixo do cabeçalho deve existir uma barra representando o progresso geral do Workflow.

Ela deve informar:

* percentual concluído;
* etapa atual;
* quantidade de etapas concluídas.

Exemplo:

```text
Workflow

████████░░░░░░░░░░

40%

Etapa 2 de 5
```

Esta barra representa o progresso da execução completa e não de uma etapa específica.

---

# Área Principal do Workflow

Esta é a região central da página.

Cada etapa deve ser apresentada como um cartão independente.

Exemplo:

```text
────────────────────────────

① Organizar Biblioteca

Status:
Concluído

Organiza e valida a estrutura da biblioteca.

[Executar novamente]

────────────────────────────
```

Cada cartão deve permanecer visível durante toda a execução.

---

# Estrutura de um Cartão

Todos os cartões seguem a mesma composição.

## Cabeçalho

* número da etapa;
* nome;
* estado atual.

---

## Corpo

* descrição;
* informações relevantes;
* métricas da etapa.

---

## Rodapé

Dependendo do estado:

* Executar
* Reexecutar
* Cancelar
* Ver detalhes

---

# Sequenciamento Visual

As etapas devem ser exibidas exatamente nesta ordem.

```text
① Organizar Biblioteca

↓

② Catalogar Obras

↓

③ Resolver IDs

↓

④ Atualizar Metadados

↓

⑤ Sincronizar Notion
```

A ordem não pode ser alterada pela interface.

---

# Destaque da Etapa Atual

Durante a execução:

* somente uma etapa poderá estar ativa;
* a etapa ativa deve receber destaque visual;
* etapas futuras permanecem neutras;
* etapas concluídas permanecem marcadas como concluídas.

Exemplo:

```text
✓ Organizar

▶ Catalogar

○ Resolver IDs

○ Metadados

○ Notion
```

---

# Painel de Execução

Enquanto o Workflow estiver em andamento, um painel deve exibir informações em tempo real.

Informações mínimas:

* etapa atual;
* obra em processamento;
* percentual da etapa;
* quantidade processada;
* tempo decorrido;
* mensagens operacionais.

Exemplo:

```text
Etapa

Catalogação

Obra atual

Omniscient Reader

Processadas

152 de 684
```

O conteúdo deve ser atualizado continuamente sem recarregar a página.

---

# Resumo da Execução

Após a conclusão do Workflow, um resumo consolidado deve ser apresentado.

Conteúdo mínimo:

* obras organizadas;
* obras catalogadas;
* IDs resolvidos;
* metadados atualizados;
* sincronizações realizadas;
* erros;
* alertas;
* duração total.

Exemplo:

```text
Workflow concluído

684 obras processadas

31 IDs resolvidos

612 metadados atualizados

598 sincronizações

3 alertas

Tempo

08m 42s
```

---

# Layout Responsivo

A página deve adaptar-se automaticamente ao tamanho disponível.

## Desktop

* cartões distribuídos verticalmente;
* painel de execução expandido;
* resumo completo.

---

## Tablet

* redução dos espaçamentos;
* reorganização das ações;
* largura ajustada.

---

## Mobile

* cartões empilhados;
* ações em largura total;
* informações secundárias recolhidas quando necessário.

Nenhuma funcionalidade deve ser perdida.

---

# Comportamentos Visuais

A interface deve fornecer feedback imediato para:

* início de execução;
* mudança de etapa;
* conclusão;
* erro;
* cancelamento.

Mudanças de estado devem ocorrer sem necessidade de recarregar a página.

---

# Consistência Visual

Todos os cartões devem compartilhar:

* mesmo espaçamento;
* mesma tipografia;
* mesma hierarquia visual;
* mesmos componentes;
* mesma disposição de informações.

O usuário deve reconhecer imediatamente qualquer etapa como parte do mesmo Workflow.

---

# Relação com outros documentos

| Documento                        | Conteúdo relacionado               |
| -------------------------------- | ---------------------------------- |
| 03-etapas-do-workflow.md         | Comportamento funcional das etapas |
| 04-processamento-e-validacoes.md | Regras de execução                 |
| 06-estados-e-mensagens.md        | Estados visuais e feedback         |
| 07-regras-de-navegacao.md        | Navegação entre módulos            |

---

# Conclusão

O layout da página **Fluxos** deve funcionar como um painel operacional, permitindo ao usuário acompanhar todo o ciclo de processamento da biblioteca de forma clara e previsível. A organização em regiões distintas — cabeçalho, progresso global, etapas do Workflow, painel de execução e resumo final — facilita a compreensão do estado atual da operação e reduz a necessidade de intervenção durante o processamento.
