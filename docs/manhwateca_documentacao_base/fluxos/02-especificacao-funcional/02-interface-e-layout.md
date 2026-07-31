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

# Padrão de Blocos Independentes

Telas novas ou novas seções dentro da página **Fluxos** devem seguir o padrão de blocos independentes.

## Regra principal

Quando uma etapa possuir uma área operacional principal e uma área auxiliar, elas devem ser renderizadas como blocos irmãos, cada um com sua própria borda externa.

Exemplo:

```html
<section class="etapa-main-card">
  Conteúdo principal da etapa.
</section>

<section class="etapa-info-card">
  Conteúdo auxiliar, informativo ou de manutenção.
</section>
```

Não deve existir um card pai com borda envolvendo os dois blocos.

## Cabeçalho da etapa

O título, a descrição e os indicadores principais da etapa devem ficar dentro do bloco principal.

O conteúdo específico selecionado pela usuária não deve dominar o topo da página nem substituir visualmente o título da etapa.

Quando um bloco for expansível, o cabeçalho deve continuar usando a mesma hierarquia visual do bloco principal:

* marcador contextual curto;
* título da seção;
* descrição objetiva;
* ícone de expansão no canto direito.

O estado recolhido deve ocupar pouco espaço, sem perder a identificação da seção.

Exemplo correto:

```text
[Card principal]
  Jornada operacional
  Revisar pendências
  Descrição curta da etapa

  Conteúdo operacional

[Card auxiliar]
  Corrigir ID confirmado
```

## Áreas auxiliares

Áreas de informação, exceção, manutenção ou diagnóstico devem aparecer abaixo do bloco principal como card independente.

Exemplos:

* `Informações da sincronização`;
* `Corrigir ID confirmado`;
* detalhes recolhíveis;
* painéis de exceção.

Essas áreas não devem ficar visualmente dentro do card operacional principal, salvo quando forem parte direta da ação principal da etapa.

Quando uma área auxiliar for expansível, ela deve manter o mesmo estilo de card e cabeçalho do bloco principal. A diferença deve estar no conteúdo, não na moldura visual.

## Bordas e espaçamentos

Deve existir:

* uma borda externa no bloco principal;
* uma borda externa no bloco auxiliar;
* espaçamento claro entre blocos.

Não deve existir:

* borda externa envolvendo múltiplos blocos independentes;
* card com borda dentro de outro card com borda sem necessidade funcional;
* título da etapa fora do card principal quando a etapa já usa esse padrão.

## Referências atuais

As etapas abaixo devem ser usadas como referência de composição:

* `Atualizar metadados`: bloco principal + bloco informativo;
* `Revisar pendências`: bloco principal + bloco de manutenção `Corrigir ID confirmado`.

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
