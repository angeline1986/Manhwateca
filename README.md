# Manhwateca

Sistema pessoal para organização e tracking de manhwas.

## Objetivo

Centralizar:

- progresso de leitura;
- status;
- notas;
- capítulos;
- sincronização com Notion.

Os arquivos físicos permanecem fora do projeto.

---

# Estrutura

```text
Manhwateca/
├── config/
├── data/
├── scripts/
├── .env
├── README.md
└── requirements.txt
```

---

## Dependências

```bash
pip install -r requirements.txt
```

---

## Configuração

Preencher `.env`:

```env
NOTION_TOKEN=
NOTION_DATABASE_ID=
MANGA_ROOT=
```

---

## Fluxo recomendado

Todos os comandos devem ser executados na raiz do projeto.

### Menu interativo

O ponto de entrada recomendado é:

```bash
python scripts/menu.py
```

O menu permite revisar a biblioteca, registrar ajustes, aplicar a organização
alfabética e a padronização dos arquivos, catalogar as obras e sincronizar com
o Notion. Toda ação que altera a biblioteca ou o Notion apresenta as opções
numéricas `1. Aplicar` e `2. Cancelar`.

| Opção | Ação |
|---|---|
| 1 | Abre o submenu para verificar ou aplicar a padronização dos arquivos. |
| 2 | Registra críticas e correções pendentes em `reports/review_notes.md`. |
| 3 | Move as pastas para os grupos alfabéticos após confirmação numérica. |
| 4 | Abre o submenu para catalogar, simular ou aplicar a sincronização com o Notion. |
| 5 | Gera os relatórios, atualiza o catálogo e simula o sync com o Notion. |
| 6 | Executa os testes automatizados do projeto. |

### Ordem recomendada

1. Abra a opção 1, gere os relatórios e revise `reports/organize_preview.html` e
   `reports/rename_preview.html`.
2. Registre problemas encontrados pela opção 2.
3. Resolva as observações pendentes.
4. Use a opção 3 para organizar as pastas e o submenu 1 para renomear arquivos.
5. Abra a opção 4 e gere o catálogo já padronizado.
6. No mesmo submenu, simule e aplique o sync.

### 1. Escanear a biblioteca

```bash
python scripts/scan.py
```

Gera:

```text
data/mangas.json
```

---

### 2. Gerar os previews

```bash
python scripts/organize.py
python scripts/rename_files.py
```

Esses comandos operam em modo de simulação por padrão e geram relatórios em
`reports/`.

Para aplicar depois da revisão:

```bash
python scripts/organize.py --apply
python scripts/rename_files.py --apply
```

Os comandos recusam a aplicação quando encontram conflitos. A organização
também é bloqueada quando há possíveis obras duplicadas.

A padronização também renomeia a imagem da obra para `cover`, preservando a
extensão original (`cover.jpg`, `cover.jpeg` ou `cover.png`). Pastas com mais
de uma imagem são bloqueadas para revisão manual.

Títulos muito longos podem ser abreviados em `config/titles.json`. O nome
configurado é usado na pasta, nos capítulos e no catálogo enviado ao Notion.

Cada movimentação aplicada é registrada em
`reports/organize_history.jsonl`, com data, origem, destino e resultado.

### 3. Simular o sync com Notion

```bash
python scripts/sync.py
```

O sync consulta as páginas existentes pelo campo `Nome`: obras novas são
marcadas para criação e obras existentes para atualização. Páginas duplicadas
no Notion são bloqueadas.

### 4. Aplicar o sync

Depois de revisar a simulação:

```bash
python scripts/sync.py --apply
```

## Estrutura esperada da biblioteca

```text
Mangas/
  A/
    Antidote/

  BC/
```

## Campos do Notion

| Campo | Tipo |
|---|---|
| Nome | Title |
| Alias | Text |
| Status | Select |
| Nota | Select |
| Último lido | Number |
| Total caps | Number |
| Path | URL |

## Status

- Lendo
- Em espera
- Finalizado
- Hiato
- Dropado
- Quero ler

---

## Nota

- Topzera
- Legalzin
- Ok
- Meia boca
- Ruim
