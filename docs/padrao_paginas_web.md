# Padrão de páginas web

Este documento é a referência oficial para novas páginas da interface web
da Manhwateca.

## Referência visual

A página **Fluxo operacional** é a referência visual e estrutural para
novas telas. Ela combina navegação lateral, cabeçalho contextual,
conteúdo em `page-container`, painéis, cards de ação e estados de
feedback de forma consistente com o restante da aplicação.

## CSS obrigatório

Toda nova página deve reutilizar a base existente:

- `web/css/tokens.css`
- `web/css/base.css`
- `web/css/layout.css`
- `web/css/responsive.css`
- `web/css/components/*.css`

CSS específico de página deve ficar em `web/css/pages/` e conter apenas
as diferenças reais da tela.

Não criar:

- cores hardcoded sem necessidade;
- novos padrões de botão equivalentes aos existentes;
- novos tipos de card que dupliquem `panel`, `status-card` ou
  `action-card`;
- espaçamentos próprios quando já houver token ou padrão no layout;
- outra estrutura de cabeçalho;
- CSS inline;
- estilos duplicados de páginas existentes.

## Anatomia da página

Novas páginas devem seguir esta estrutura:

```text
sidebar
    |
topbar
    eyebrow
    titulo
    subtitulo
    acao contextual, se houver
    |
page-container
    |
page
    |
panel / cards / conteudo
    |
feedback / loading / empty / error
```

Use `panel` para blocos principais, `action-card` para escolhas de ação
e os componentes existentes para badges, botões, formulários e modais.

## Conteúdo e estados

Toda página nova deve prever:

- estado inicial carregando;
- estado vazio quando não houver dados;
- estado de erro com mensagem acionável;
- feedback dinâmico quando uma ação é executada;
- texto curto e específico para o fluxo do usuário.

Evite textos dentro da interface que expliquem a implementação, os
atalhos ou a estrutura visual. A tela deve guiar a ação, não documentar
o código.

## JavaScript

O JavaScript da página deve:

- separar comportamento visual de chamadas API;
- usar os mecanismos atuais de navegação;
- preservar loading, error e empty states;
- reutilizar helpers existentes antes de criar novos;
- evitar grandes blocos de lógica inline no HTML.

Arquivos específicos de página devem ficar em `web/js/pages/` quando a
tela tiver comportamento próprio. Helpers compartilhados devem ficar nos
diretórios já existentes de `web/js/`.

## Acessibilidade e responsividade

Toda página nova deve manter:

- botões com `type="button"` quando não forem submit;
- `aria-live` em feedback dinâmico quando apropriado;
- labels para campos de formulário;
- navegação compatível com teclado;
- comportamento responsivo baseado em `web/css/responsive.css`.

## Revisão antes de concluir

Antes de considerar uma página pronta:

- compare visualmente com a página Fluxo operacional;
- confira se os tokens e componentes existentes foram reutilizados;
- verifique se não há CSS inline ou duplicação de componentes;
- teste os estados loading, empty e error;
- teste desktop e mobile;
- revise foco, labels e feedback acessível.
