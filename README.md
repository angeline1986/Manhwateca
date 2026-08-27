# Manhwateca — Padronização de filas: Cápsulas leves

Este patch aplica a opção aprovada **B — Cápsulas leves** nas filas equivalentes
do projeto e registra a decisão em `docs/frontend_page_standard.md`.

## Regra consolidada

Na fila esquerda aparecem somente:

- checkbox quando houver seleção em lote;
- interação indispensável, como Favorito em Acompanhamento;
- nome da obra;
- seta `›` discreta.

Não aparecem na fila status, ID, datas, divergências, grupo, caminho, mensagem de
sincronização ou outro metadado. Essas informações ficam no painel direito.

## Telas ajustadas

- Organização v2
- Acompanhamento > Busca e favoritas
- Fluxos > Sincronizar Notion

Em Sincronizar Notion é removida visualmente a segunda linha
`Nunca sincronizada · ID ...`; os dados continuam preservados nos `data-*` usados
pelo detalhe e pela lógica da tela.

## Documentação

Adiciona ao `docs/frontend_page_standard.md` a seção
**Padrão visual dos itens de fila — Cápsulas leves**, incluindo hover, item aberto,
truncamento e independência entre checkbox e item em detalhe.

## Arquivos alterados

- `docs/frontend_page_standard.md`
- `web/js/pages/organizationPage.js`
- `web/css/pages/organization.css`
- `web/js/pages/trackingPage.js`
- `web/css/pages/releases.css`
- `web/js/flows/syncNotionPanel.js`
- `web/css/pages/flows-journey.css`

## Aplicação

Copie `apply_updates.py` para a raiz do repositório e execute:

```bash
python apply_updates.py
```

Backup automático:

```text
reports/patch_backups/queue_capsules_<timestamp>/
```

## Validação recomendada

```bash
node --check web/js/pages/organizationPage.js
node --check web/js/pages/trackingPage.js
node --check web/js/flows/syncNotionPanel.js
python -m unittest discover -s tests -p 'test_release_monitor*.py' -v
```
