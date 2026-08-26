# Padrão de criação de páginas — Manhwateca

Este documento registra o contrato visual mínimo para novas páginas internas da interface web. O objetivo é impedir que cada tela crie um micro-layout próprio e acabe divergindo em posição, largura, espaçamento e componentes.

## 1. Referência principal

Para páginas operacionais internas, **Fluxos / Buscar candidatos** é a referência de composição e espaçamento. Antes de criar CSS novo, reutilize tokens, componentes e estruturas já existentes em `web/css/` e `web/js/`.

## 2. Envelope da página

- Use a estrutura existente `workspace > topbar + .page-container > .page`.
- Não altere `.page-container` global para corrigir apenas uma página. Prefira regra escopada pelo ID da página ativa.
- Para páginas que devem seguir o padrão compacto de Fluxos, use `padding: 16px` no `.page-container` somente quando aquela página estiver ativa.
- Quando o conteúdo principal for operacional, use largura máxima de referência de **1180px** e centralização horizontal.
- Evite valores próprios de margem superior que afastem o primeiro painel da topbar.

Exemplo:

```css
.page-container:has(#page-exemplo.active) {
  padding: 16px;
}

#page-exemplo {
  width: min(1180px, 100%);
  margin-right: auto;
  margin-left: auto;
}
```

## 3. Painéis e seções

- Reutilize `.panel`, `.section-heading`, `.eyebrow`, `.primary-action`, `.secondary-action`, badges, estados e inputs existentes.
- Não recrie visualmente um componente que já existe.
- Defina o espaço entre painéis no escopo da página, sem alterar `.page > .panel + .panel` global.
- Use `16px` como referência de espaçamento compacto entre grandes seções operacionais, salvo necessidade real do fluxo.

## 4. Tabelas e listas

- Reutilize os componentes de tabela existentes antes de criar uma variante.
- Cabeçalho e corpo devem sempre ter a mesma quantidade de colunas.
- Estados vazios devem usar `colspan` compatível com a quantidade atual de colunas.
- Se uma lista puder crescer além do espaço confortável de leitura, adote paginação ou limite visual explícito.

## 5. Paginação

Para paginação client-side:

- mantenha `currentPage` e `pageSize` no módulo da página;
- ao alterar busca ou filtros, retorne para a página 1;
- limite `currentPage` ao total de páginas após qualquer mudança nos dados;
- desabilite Anterior/Próxima nos extremos;
- mostre página atual, total de páginas e intervalo de registros;
- use os botões/componentes existentes, sem criar nova paleta.

Quando a quantidade de dados for grande ou o endpoint já oferecer paginação real, prefira paginação no backend.

## 6. JavaScript por página

- Mantenha a lógica específica em `web/js/pages/<pagina>Page.js`.
- Registre elementos DOM em `web/js/app.js` e passe-os para o módulo da página.
- Evite seletores globais quando um ID ou elemento injetado puder manter o escopo explícito.
- Filtros e paginação devem ser estado da própria página, sem alterar contratos de API sem necessidade.

## 7. CSS por página

- Regras específicas ficam em `web/css/pages/`.
- Não use uma correção global para resolver diferença visual de uma única tela.
- Antes de adicionar cor, sombra, raio ou espaçamento novo, procure o token/componente equivalente já existente.
- A paleta Rose Edition atual deve ser preservada.

## 8. Checklist antes de concluir uma página

- [ ] Primeiro painel está alinhado com a topbar como as páginas de referência.
- [ ] Largura e centralização seguem o padrão operacional.
- [ ] Espaçamento entre grandes seções é consistente.
- [ ] Foram reutilizados componentes existentes.
- [ ] Tabelas têm cabeçalho, corpo e `colspan` coerentes.
- [ ] Listas longas possuem paginação/limite apropriado.
- [ ] Filtros resetam a paginação quando necessário.
- [ ] Não foram adicionadas cores ou componentes redundantes.
- [ ] CSS e JS estão escopados à página.
- [ ] A página foi conferida em viewport desktop e reduzido.

## 9. Página Acompanhamento como exemplo

A correção de Acompanhamento de 26/08/2026 segue este padrão: envelope de 16px, largura operacional de 1180px, seções com espaçamento controlado, tabela de quatro colunas coerentes e paginação client-side de cinco lançamentos por página.
