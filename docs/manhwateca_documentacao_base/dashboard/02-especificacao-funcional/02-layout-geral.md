## 02 - Layout Geral

---

# Objetivo do Documento

Este documento especifica a organização estrutural da interface do Dashboard.

Seu objetivo é definir como os componentes são distribuídos visualmente na página, estabelecendo uma arquitetura consistente para implementação e futuras evoluções da interface.

Este documento **não descreve o comportamento interno dos componentes**. Cada componente possui sua própria especificação funcional.

---

# Escopo

Este documento cobre exclusivamente:

* estrutura da página;
* organização dos blocos;
* hierarquia visual;
* sistema de grid;
* espaçamentos;
* comportamento responsivo;
* ordem de renderização;
* comportamento de rolagem.

Não faz parte deste documento:

* regras de negócio;
* navegação;
* mensagens;
* estados específicos dos componentes;
* comportamento funcional dos cards.

---

# Objetivos do Layout

O layout do Dashboard deve atender aos seguintes objetivos:

* facilitar a identificação das informações mais importantes;
* reduzir a carga cognitiva do usuário;
* manter uma organização previsível;
* permitir expansão futura sem alterações estruturais;
* garantir consistência visual entre todos os módulos da Manhwateca.

---

# Estrutura Geral da Página

A estrutura da página é composta por duas áreas principais:

```text
Aplicação
├── Sidebar
└── Workspace
```

A Sidebar permanece fixa durante toda a navegação.

Todo o conteúdo do Dashboard é exibido dentro do Workspace.

---

# Hierarquia Visual

A página deve seguir a seguinte ordem de prioridade visual.

| Prioridade | Área                      |
| ---------- | ------------------------- |
| Muito Alta | Próximo Passo Recomendado |
| Alta       | Cards de Métricas         |
| Alta       | Pendências                |
| Média      | Integrações               |
| Média      | Workflow                  |
| Baixa      | Atualização               |

Essa hierarquia deve ser preservada independentemente do tamanho da tela.

---

# Organização da Interface

A distribuição dos componentes deve seguir obrigatoriamente a ordem abaixo.

```text
Workspace

├── Cabeçalho
│
├── Próximo Passo Recomendado
│
├── Cards de Métricas
│
├── Grid Principal
│   ├── Pendências
│   └── Integrações
│
└── Workflow
```

Essa ordem representa a sequência lógica de leitura da página.

---

# Sidebar

A Sidebar possui as seguintes responsabilidades:

* navegação principal;
* identificação do módulo atual;
* acesso aos módulos da aplicação.

Ela deve permanecer fixa durante toda a navegação.

Itens exibidos:

* Dashboard
* Biblioteca
* Fluxos
* Configurações

O comportamento funcional da navegação é documentado em **11-navegacao.md**.

---

# Workspace

O Workspace representa toda a área útil da aplicação.

Responsabilidades:

* conter todos os componentes do Dashboard;
* controlar o espaçamento entre blocos;
* controlar a rolagem vertical.

O Workspace nunca deve possuir rolagem horizontal.

---

# Cabeçalho

O Cabeçalho é sempre o primeiro componente do Workspace.

Seu comportamento funcional está documentado em **03-cabecalho.md**.

---

# Organização dos Blocos

A página deve seguir exatamente a sequência abaixo.

1. Cabeçalho
2. Próximo Passo Recomendado
3. Cards de Métricas
4. Pendências
5. Integrações
6. Workflow

Essa organização não deve variar de acordo com os dados carregados.

Mesmo quando um componente estiver vazio, sua posição deve ser preservada.

---

# Sistema de Grid

O Dashboard utiliza um layout baseado em blocos independentes.

Estrutura recomendada:

```text
┌──────────────────────────────────────────────┐
│ Cabeçalho                                    │
├──────────────────────────────────────────────┤
│ Próximo Passo                                │
├──────────────────────────────────────────────┤
│ Métrica │ Métrica │ Métrica │ Métrica        │
├──────────────────────┬───────────────────────┤
│ Pendências           │ Integrações           │
├──────────────────────┴───────────────────────┤
│ Workflow                                    │
└──────────────────────────────────────────────┘
```

Cada bloco deve possuir independência visual e funcional.

---

# Espaçamentos

O layout deve manter espaçamentos consistentes entre todos os componentes.

Os seguintes princípios devem ser respeitados:

* distância uniforme entre blocos;
* alinhamento vertical consistente;
* margens externas simétricas;
* ausência de sobreposição entre componentes.

Os valores específicos (pixels, rem, etc.) pertencem ao Design System e não fazem parte desta especificação.

---

# Responsividade

O Dashboard deve adaptar sua organização sem alterar a ordem lógica dos componentes.

## Desktop

Sidebar fixa.

Grid com duas colunas para Pendências e Integrações.

Cards de métricas exibidos na mesma linha.

---

## Tablet

Sidebar recolhida.

Cards de métricas podem quebrar em duas linhas.

Pendências e Integrações permanecem lado a lado quando houver espaço suficiente.

---

## Mobile

Todos os componentes devem ser empilhados verticalmente.

A ordem de leitura permanece:

1. Cabeçalho
2. Próximo Passo
3. Métricas
4. Pendências
5. Integrações
6. Workflow

---

# Rolagem

A página possui apenas rolagem vertical.

A Sidebar permanece fixa.

O Cabeçalho pode permanecer fixo ou acompanhar a rolagem, conforme definido pelo Design System.

Nenhum componente interno deve possuir barras de rolagem próprias, exceto quando houver necessidade funcional específica.

---

# Princípios de UX

A organização visual do Dashboard deve seguir os seguintes princípios:

* informações mais importantes aparecem primeiro;
* leitura natural de cima para baixo;
* componentes relacionados permanecem próximos;
* ausência de poluição visual;
* estabilidade do layout durante atualizações.

O carregamento de novos dados não deve provocar mudanças bruscas na posição dos componentes.

---

# Dependências

Este documento possui relação direta com:

* 03-cabecalho.md
* 04-proximo-passo.md
* 05-metricas.md
* 06-pendencias.md
* 07-workflow.md
* 08-integracoes.md
* 09-acoes-rapidas.md
* 11-navegacao.md

Cada um desses documentos detalha o comportamento do respectivo componente.

---

# Critérios de Aceite

O layout será considerado conforme esta especificação quando:

* existir apenas uma Sidebar;
* existir apenas um Workspace;
* os componentes forem apresentados na ordem definida;
* a estrutura permanecer consistente em diferentes resoluções;
* não houver rolagem horizontal;
* o layout preservar sua estabilidade durante atualizações;
* a implementação respeitar a separação entre estrutura visual e comportamento funcional.

