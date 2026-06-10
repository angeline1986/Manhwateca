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
| 1 | Abre o submenu para verificar, aplicar ou registrar ajustes da padronização. |
| 2 | Move as pastas para os grupos alfabéticos após confirmação numérica. |
| 3 | Abre o submenu para catalogar, simular ou aplicar a sincronização com o Notion. |
| 4 | Gera os relatórios, atualiza o catálogo e simula o sync com o Notion. |
| 5 | Executa os testes automatizados do projeto. |

### Ordem recomendada

1. Abra a opção 1, gere os relatórios e revise
   `reports/audits/organize_preview.html` e
   `reports/audits/rename_preview.html`.
2. No mesmo submenu, registre problemas encontrados para revisão manual.
3. Resolva as observações pendentes.
4. Use a opção 2 para organizar as pastas e o submenu 1 para renomear arquivos.
5. Abra a opção 3 e gere o catálogo já padronizado.
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
`reports/logs/organize_history.jsonl`, com data, origem, destino e resultado.

### 3. Simular o sync com Notion

```bash
python scripts/sync.py --simulate-batch
```

Essa opção mostra somente as próximas 25 obras que formam o lote seguinte e
quantas continuarão pendentes. O sync consulta as páginas existentes pelo
campo `Nome`; páginas duplicadas no Notion são bloqueadas. A comparação ignora diferenças de acentuação,
maiúsculas, pontuação e sublinhados, e também considera aliases e nomes
anteriores configurados.

### 4. Aplicar o sync

Depois de revisar a simulação, importe o próximo lote de 25 obras:

```bash
python scripts/sync.py --apply-batch
```

Em cada execução, o programa consulta o Notion e ordena alfabeticamente as
obras ainda ausentes. Ele cria somente as próximas 25 e informa quantas
restaram. As páginas que já existem são reconhecidas pelo título e não são
criadas nem alteradas novamente. Se uma execução for interrompida, basta repetir a opção:
as páginas concluídas serão detectadas e o lote continuará das próximas.

O estado reconciliado com o Notion é salvo em
`reports/integrations/notion_import_status.json`. O arquivo informa as obras importadas,
as importadas no lote atual, as que ainda estão pendentes e eventuais
duplicidades. Ele é atualizado também durante a simulação.

O tamanho pode ser alterado no terminal, por exemplo:

```bash
python scripts/sync.py --apply-batch --batch-size 10
```

A aplicação integral continua disponível com `--apply`, mas é bloqueada
quando mais de 25% do catálogo seria criado. A exceção
`--apply --allow-mass-create` deve ser usada somente para uma importação
integral intencional.

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
| ID da obra | Number |
| Alias | Text |
| Status | Select |
| Nota | Select |
| Último lido | Number |
| Último capítulo disponível | Number |
| Capítulos encontrados | Number |
| Side stories | Number |
| Lacunas | Text |
| Status da contagem | Select |
| Capítulo MangaUpdates | Number |
| MangaUpdates | URL |
| Temática | Multi-select |
| Formato | Select |
| Universo | Multi-select |
| Picância | Select |
| Interesse | Select |

### Formato

- Manhwa
- Novel
- Manhwa e Novel

### Picância

- 💕 Baixa
- 💫 Média
- 🔥 Alta
- 🔥🔥🔥 Intenso

`Temática` reúne assuntos da obra, como regressão, poder, sobrevivência,
mistério, sobrenatural e drama psicológico. `Universo` classifica ambientações
e subgêneros, como fantasia, omegaverse e xianxia.

## Auditoria de capítulos

O catálogo diferencia o maior capítulo disponível da quantidade efetivamente
encontrada nos arquivos. A opção de relatórios gera
`reports/audits/chapter_audit.html`, contendo lacunas, intervalos sobrepostos,
arquivos não interpretados, side stories e divergências com o MangaUpdates.

IDs confirmados do MangaUpdates ficam em `config/mangaupdates.json`. A busca
pode ser usada para localizar candidatos:

```bash
python scripts/mangaupdates.py --search "Nome da obra"
```

Depois de confirmar o ID e adicioná-lo à configuração, atualize o cache:

```bash
python scripts/mangaupdates.py
python scripts/scan.py
```

A identificação não aceita automaticamente o primeiro resultado da busca,
evitando confundir versões Manhwa, Novel e obras com nomes semelhantes.

## CSV do MangaUpdates

A opção 4 do menu busca IDs para as obras de
`reports/integrations/buscaIds.json` em lotes de 10.
A opção 5 executa a busca de dados e, quando a correspondência é segura, o
detalhe da obra. Há um intervalo padrão de 3 segundos entre chamadas,
tratamento de HTTP 429 com espera progressiva, cache e retomada automática.

O resultado fica em `reports/integrations/manhwateca_import.csv`, com as mesmas colunas da
base do Notion, a coluna `ID da obra` e a coluna auxiliar
`Correspondência API`. O progresso fica em
`data/mangaupdates_progress.json`.

Casos ambíguos ou não encontrados permanecem no CSV para revisão, sem escolher
um ID automaticamente. Para executar uma quantidade menor pelo terminal:

```bash
python scripts/mangaupdates.py --generate-csv --delay 3 --limit 10
```

Para preencher os IDs pelo terminal:

```bash
python scripts/mangaupdates.py \
  --fill-ids reports/integrations/buscaIds.json \
  --delay 3 \
  --limit 10
```

Cada obra recebe uma lista `IDs` com os candidatos, título, tipo, ano, URL,
descrição de até 734 caracteres e pontuação. O campo `ID` só é preenchido quando o melhor resultado supera o
limite de confiança e está suficientemente distante do segundo colocado.
Variações de título são comparadas por palavras e similaridade textual.
Resultados duvidosos recebem `Status: Revisar`. O arquivo é salvo depois de
cada busca e pode ser retomado executando o mesmo comando novamente.
Para atualizar candidatos já marcados para revisão, use também
`--retry-review`.

A opção 6 primeiro simula a atualização do Notion e pede uma segunda
confirmação antes de aplicar. Ela atualiza somente páginas já existentes e
nunca cria obras a partir do CSV.

## Organização de relatórios

```text
reports/
├── audits/
│   ├── chapter_audit.html
│   ├── organize_preview.html
│   └── rename_preview.html
├── integrations/
│   ├── buscaIds.json
│   ├── manhwateca_import.csv
│   └── notion_import_status.json
├── logs/
│   └── organize_history.jsonl
└── reviews/
    ├── review_notes.md
    └── status_report.md
```

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
