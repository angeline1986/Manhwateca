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


## 4. Arquétipos de layout

As páginas não devem ser comparadas ou padronizadas apenas pelo módulo ao qual pertencem.
A referência correta é o **arquétipo de layout**.

Isso evita forçar uma página de tabela a se comportar como uma página master/detail apenas
porque ambas pertencem à mesma área do sistema.

### 4.1. Tabela × tabela

Use como referência outras telas cujo conteúdo principal também seja uma tabela.

Exemplos atuais:

- **Fluxos > Buscar candidatos**;
- **Acompanhamento > Lançamentos recentes**.

Regras:

- mantenha o envelope da página, cabeçalho, ritmo vertical e paginação coerentes;
- tabelas paginadas não devem reposicionar suas colunas quando a página muda;
- quando o conteúdo variável puder alterar a geometria, use `table-layout: fixed` e
  larguras definidas por `<colgroup>` ou seletores escopados àquela tabela;
- não aplique larguras específicas em uma classe de tabela compartilhada quando outras
  telas possuem outra quantidade ou semântica de colunas;
- compare densidade, altura de linhas e espaço negativo somente com tabelas equivalentes;
- o conteúdo das colunas pode variar conforme a função da tela.

### 4.2. Fila + detalhe + capa

Este é o padrão master/detail para telas em que o usuário seleciona uma obra na coluna
esquerda e trabalha ou consulta seus dados na coluna direita.

Referências atuais:

- **Organização v2**;
- **Acompanhamento > Busca e favoritas**;
- **Fluxos > Sincronizar Notion**.

Estrutura recomendada:

```text
+------------------+------------------------------------------+
| FILA             | OBRA SELECIONADA                         |
| KPIs             | título + ação contextual                 |
| busca + filtro   | metadados                                |
| itens            | capa + contexto/explicação               |
|                  | conteúdo específico                      |
| flow-pager       | próxima ação                             |
+------------------+------------------------------------------+
```

#### Coluna da fila

- use **340px** como largura de referência no desktop;
- o detalhe deve ocupar `minmax(0, 1fr)`;
- KPIs, busca, filtros, estado selecionado e paginação devem reutilizar os mesmos
  componentes e a mesma escala visual sempre que cumprirem a mesma função;
- listas paginadas devem reutilizar `flow-pager`;
- nomes de obras devem continuar legíveis sem depender de negrito excessivo;
- a fila pode variar em conteúdo, mas não deve inventar um novo micro-layout sem necessidade.

Exemplo estrutural:

```css
.master-detail-workspace {
  display: grid;
  grid-template-columns: 340px minmax(0, 1fr);
}
```

#### Painel de detalhe

A **capa faz parte do padrão** quando a entidade selecionada é uma obra e existe uma imagem
disponível. Ela funciona como âncora de reconhecimento, reduz a sensação de painel
excessivamente textual e ajuda o usuário a confirmar rapidamente qual obra está aberta.

A composição recomendada é:

1. `eyebrow` + título da obra + ação contextual;
2. metadados principais;
3. **capa à esquerda + bloco contextual à direita**;
4. conteúdo específico da tela;
5. aviso/notice quando necessário;
6. próxima ação na base do painel.

Para a capa:

- preserve proporção vertical de capa;
- use `object-fit: cover` quando houver imagem;
- não distorça a imagem para preencher o espaço;
- mantenha fallback explícito como **Sem capa** quando não houver imagem;
- não use a capa como decoração: ela representa a obra selecionada;
- a capa deve permanecer no detalhe e não precisa ser repetida em cada item da fila.

O bloco ao lado da capa pode variar por função:

- **Organização v2:** explicar o que precisa ser revisado;
- **Acompanhamento:** resumir contexto de monitoramento da obra;
- **Sincronizar Notion:** explicar o que acontecerá na sincronização.

A estrutura é compartilhada; o conteúdo é especializado.

### 4.3. O que pode variar entre telas do mesmo arquétipo

Padronização não significa tornar todas as telas idênticas.

Pode variar:

- quantidade e significado dos KPIs;
- conteúdo dos cards de metadados;
- texto do bloco ao lado da capa;
- corpo do detalhe;
- ação final;
- densidade interna necessária à tarefa.

Deve permanecer coerente:

- largura da fila;
- posição relativa de fila e detalhe;
- escala de espaçamento;
- estado selecionado;
- família de inputs e botões;
- `flow-pager`;
- tratamento da capa;
- hierarquia `eyebrow → título → apoio → conteúdo → ação`.

## 5. Tipografia e títulos

A regra para títulos é **padrão base + especializações**.

- família tipográfica, cor e hierarquia devem partir do padrão base;
- use `.eyebrow` para contexto curto em caixa alta;
- textos de apoio devem usar `var(--muted)`, salvo estado funcional que exija outra cor;
- uma página pode especializar tamanho, `line-height`, `letter-spacing` ou espaçamento
  quando sua composição exigir;
- especialização não significa criar uma nova linguagem visual;
- evite duplicar regras tipográficas apenas para reproduzir algo que o padrão base já entrega.

## 6. Tabelas e listas

- Reutilize os componentes de tabela existentes antes de criar uma variante.
- Cabeçalho e corpo devem sempre ter a mesma quantidade de colunas.
- Estados vazios devem usar `colspan` compatível com a quantidade atual de colunas.
- Se uma lista puder crescer além do espaço confortável de leitura, adote paginação ou limite visual explícito.
- Em tabelas paginadas, a geometria das colunas deve permanecer estável ao trocar de página.
- Quando o algoritmo automático do navegador fizer as colunas se moverem por causa do
  conteúdo, use `table-layout: fixed` e larguras escopadas à tabela.
- Prefira conteúdo operacional a colunas meramente decorativas.

## 7. Paginação

O componente canônico de paginação das páginas internas é o mesmo usado em
**Fluxos > Jornada operacional > Buscar candidatos**: `flow-pager`.

### Contrato visual

- use `.flow-pager` como contêiner;
- use `.flow-page-link` nos controles;
- use `‹` e `›` para anterior e próxima;
- mostre até três números de página por vez;
- marque a página atual com `.active`, preservando o sublinhado Rose;
- desabilite controles dos extremos com `disabled`;
- não crie uma segunda aparência com botões textuais “Anterior / Próxima”,
  contador “Página X de Y” ou outra paleta quando `flow-pager` atender à tela.

Para paginação client-side:

- mantenha `currentPage` e `pageSize` no módulo da página;
- ao alterar busca ou filtros, retorne para a página 1;
- limite `currentPage` ao total de páginas após qualquer mudança nos dados;
- esconda o pager quando houver somente uma página, se isso não prejudicar a compreensão;
- preserve a mesma janela visual de páginas adotada pelo componente canônico.

Para tabelas paginadas, a paginação não pode causar reflow horizontal:
as posições das colunas devem permanecer estáveis entre páginas.

Quando a quantidade de dados for grande ou o endpoint já oferecer paginação real,
prefira paginação no backend sem alterar a apresentação visual do `flow-pager`.

## 8. JavaScript por página

- Mantenha a lógica específica em `web/js/pages/<pagina>Page.js`.
- Registre elementos DOM em `web/js/app.js` e passe-os para o módulo da página.
- Evite seletores globais quando um ID ou elemento injetado puder manter o escopo explícito.
- Filtros e paginação devem ser estado da própria página, sem alterar contratos de API sem necessidade.

## 9. CSS por página

- Regras específicas ficam em `web/css/pages/`.
- Não use uma correção global para resolver diferença visual de uma única tela.
- Antes de adicionar cor, sombra, raio ou espaçamento novo, procure o token/componente equivalente já existente.
- A paleta Rose Edition atual deve ser preservada.

## 10. Checklist antes de concluir uma página

- [ ] Primeiro painel está alinhado com a topbar como as páginas de referência.
- [ ] Largura e centralização seguem o padrão operacional.
- [ ] Espaçamento entre grandes seções é consistente.
- [ ] A tela foi comparada com outras do **mesmo arquétipo de layout**.
- [ ] Foram reutilizados componentes existentes.
- [ ] Títulos seguem **padrão base + especializações**.
- [ ] Tabelas têm cabeçalho, corpo e `colspan` coerentes.
- [ ] Colunas de tabelas paginadas não se movem ao trocar de página.
- [ ] Listas longas possuem paginação/limite apropriado.
- [ ] Paginação reutiliza `flow-pager`.
- [ ] Filtros resetam a paginação quando necessário.
- [ ] Em master/detail, a fila usa a referência de 340px quando aplicável.
- [ ] Em telas de obra com master/detail, a capa está no detalhe quando disponível.
- [ ] A capa preserva proporção e possui fallback quando ausente.
- [ ] Não foram adicionadas cores ou componentes redundantes.
- [ ] CSS e JS estão escopados à página.
- [ ] A página foi conferida em viewport desktop e reduzido.

## 11. Página Acompanhamento como exemplo

A página Acompanhamento aplica dois arquétipos diferentes sem misturá-los:

- **Lançamentos recentes** segue o padrão de tabela paginada, com cinco itens por página,
  colunas estáveis e `flow-pager`;
- **Busca e favoritas** segue o padrão **Fila + detalhe + capa**, com fila à esquerda,
  obra selecionada à direita, capa como âncora visual, metadados, histórico e próxima ação.

O envelope permanece em 16px, a largura operacional de referência é 1180px e os títulos
seguem **padrão base + especializações**.

## Padrão visual dos itens de fila — Cápsulas leves

<!-- QUEUE_CAPSULES_STANDARD_20260827 -->

Para telas do arquétipo **Fila + detalhe + capa**, o padrão visual oficial dos itens
da coluna esquerda é **Cápsulas leves**.

A fila tem uma responsabilidade simples: **localizar e selecionar a obra**.
Ela não deve explicar o estado da obra.

### Conteúdo permitido na fila

Cada item pode conter apenas:

- controle de seleção quando a etapa trabalhar com seleção em lote;
- interação própria da entidade quando indispensável, como a estrela de Favorito em
  Acompanhamento;
- **nome da obra**;
- affordance discreto de navegação, como `›`, sem texto adicional.

Não exiba ao redor ou abaixo do nome:

- ID;
- status;
- data;
- quantidade de divergências;
- estado de sincronização;
- caminho;
- grupo;
- capítulo;
- mensagens operacionais;
- qualquer outro metadado.

Essas informações pertencem ao **painel de detalhe à direita**.

### Aparência da Cápsula leve

O item deve manter o estilo Rose Edition já existente, sem introduzir nova paleta:

- altura mínima de referência: **48px**;
- raio de referência: **10–11px**;
- fundo em repouso muito sutil, próximo ao fundo da fila;
- borda transparente ou extremamente discreta em repouso;
- `gap` vertical de aproximadamente **6–7px** entre itens;
- nome com peso moderado, sem negrito excessivo;
- `overflow: hidden`, `text-overflow: ellipsis` e `white-space: nowrap` para nomes longos.

#### Hover

No hover:

- a cápsula pode deslocar-se horizontalmente em aproximadamente **2px**;
- fundo passa para o painel branco;
- borda Rose suave aparece;
- o `›` pode surgir com transição curta.

O movimento deve ser pequeno e não pode causar reflow da fila.

#### Item aberto no detalhe

A obra atualmente aberta no painel direito deve receber:

- borda Rose;
- fundo claro;
- sombra muito sutil;
- `›` visível;
- nenhuma informação textual adicional.

O estado de **item aberto** é diferente do estado de **checkbox marcado**.
Marcar um checkbox para ação em lote não deve alterar qual obra está aberta no detalhe.

### Aplicação no projeto

Este padrão deve ser compartilhado por filas equivalentes, incluindo:

- **Organização v2**;
- **Acompanhamento > Busca e favoritas**;
- **Fluxos > Sincronizar Notion**.

As telas continuam livres para especializar o conteúdo do painel direito, mas a fila
de obras deve manter a mesma linguagem de seleção e navegação.

### Checklist específico da fila

- [ ] A fila mostra somente interação indispensável + nome da obra.
- [ ] Nenhum status, ID ou metadado aparece abaixo do nome.
- [ ] Informações operacionais estão no painel direito.
- [ ] Hover usa acabamento leve e deslocamento de no máximo 2px.
- [ ] Item aberto possui destaque Rose sem acrescentar texto.
- [ ] Checkbox marcado e item aberto continuam estados independentes.
- [ ] Nomes longos são truncados de forma previsível.
- [ ] `flow-pager` continua sendo usado quando a fila é paginada.
