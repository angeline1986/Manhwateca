# Manhwateca — Acompanhamento / paginação padrão v2

Pacote de ajuste conservador para a página **Acompanhamento**.

## O que muda

1. **Lançamentos recentes**
   - mantém 5 itens por página;
   - substitui a paginação anterior pelo mesmo componente visual de
     **Fluxos > Jornada operacional > Buscar candidatos**;
   - usa `‹ 1 2 3 ›`, `.flow-pager` e `.flow-page-link`;
   - mostra no máximo três números de página e sublinha a página ativa.

2. **Busca e favoritas**
   - reduz o peso tipográfico dos nomes da Fila de obras;
   - deixa a estrela de favorito com peso regular;
   - preserva o destaque da obra selecionada pela borda já existente.

3. **Último lançamento**
   - corrige a origem do dado no backend;
   - o overview passa a procurar o lançamento mais recente em
     `external_releases` e `mangaupdates_releases`;
   - mantém um fallback no frontend para o histórico já carregado;
   - não inventa lançamento quando não existe registro persistido.

4. **Documentação**
   - atualiza `docs/frontend_page_standard.md`;
   - define formalmente a paginação de Buscar candidatos como componente
     canônico para novas páginas internas.

## Arquivos alterados pelo patch

- `web/index.html`
- `web/js/pages/trackingPage.js`
- `web/css/pages/releases.css`
- `manhwateca/release_monitor/repository.py`
- `docs/frontend_page_standard.md`

## Como aplicar

Copie `apply_updates.py` para a raiz do repositório Manhwateca e execute:

```bash
python apply_updates.py
```

O script valida a estrutura esperada antes de gravar e cria backup automático em:

```text
reports/patch_backups/acompanhamento_paginacao_v2_<timestamp>/
```

## Depois de aplicar

```bash
node --check web/js/pages/trackingPage.js
python -m py_compile manhwateca/release_monitor/repository.py
python -m unittest discover -s tests
```

Depois, inicie normalmente:

```bash
./start_manhwateca.command
```

## Escopo preservado

O pacote não altera migrations/schema, slider, favoritos, topbar, menu,
roteamento, monitor de execução, APIs externas nem outras páginas.
