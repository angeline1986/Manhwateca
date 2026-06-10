# Manhwateca

Sistema pessoal para organização e tracking de manhwas.

## Navegação

- [Início rápido](#início-rápido)
- [Fluxo recomendado](#fluxo-recomendado)
- [Campos do Notion](#campos-do-notion)
- [MangaUpdates e CSV](#mangaupdates-e-csv)
- [Organização dos relatórios](#organização-dos-relatórios)

## Objetivo

Centralizar:

- progresso de leitura;
- status;
- notas;
- capítulos;
- sincronização com Notion.

Os arquivos físicos permanecem fora do projeto.

## Estrutura do projeto

```text
Manhwateca/
├── config/
├── data/
├── scripts/
├── .env
├── README.md
└── requirements.txt
```

## Dependências

```bash
pip install -r requirements.txt
```

## Configuração

Preencher `.env`:

```env
NOTION_TOKEN=
NOTION_DATABASE_ID=
MANGA_ROOT=
```

## Início rápido

```bash
pip install -r requirements.txt
python scripts/menu.py
```

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

| Opção | Função                                                    |
| :---: | --------------------------------------------------------- |
|   1   | Verifica e aplica a padronização dos arquivos.             |
|   2   | Organiza as pastas alfabeticamente ou executa os testes.   |
|   3   | Cataloga e sincroniza a biblioteca com o Notion.           |
|   4   | Busca IDs no MangaUpdates e atualiza `buscaIds.json`.      |
|   5   | Consulta os IDs confirmados e atualiza o CSV.              |
|   6   | Atualiza páginas existentes do Notion usando o CSV.        |
|   7   | Executa o fluxo completo.                                  |
|   0   | Encerra o programa.                                        |

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

| Campo                       | Tipo         |
| --------------------------- | ------------ |
| Nome                        | Title        |
| ID da obra                  | Number       |
| Alias                       | Text         |
| Status                      | Select       |
| Nota                        | Select       |
| Último lido                 | Number       |
| Último capítulo disponível  | Number       |
| Capítulos encontrados       | Number       |
| Side stories                | Number       |
| Lacunas                     | Text         |
| Status da contagem          | Select       |
| Capítulo MangaUpdates       | Number       |
| MangaUpdates                | URL          |
| Temática                    | Multi-select |
| Formato                     | Select       |
| Universo                    | Multi-select |
| Picância                    | Select       |
| Interesse                   | Select       |

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

## MangaUpdates e CSV

O processo funciona assim:

1. **Opção 4:** busca os IDs e atualiza
   `reports/integrations/buscaIds.json`.
2. Revise no JSON os itens com `Status: Revisar`.
3. **Opção 5:** consulta os IDs confirmados e atualiza
   `reports/integrations/manhwateca_import.csv`.

As consultas são feitas em lotes de 10, com intervalo de 3 segundos. O
processo pode ser retomado sem repetir as obras já concluídas.

A opção 5 preserva os campos preenchidos manualmente no CSV, como `Interesse`,
`Status` e `Nota`.

A opção 6 simula a atualização do Notion antes de pedir confirmação. Ela
atualiza somente páginas existentes.

## Organização dos relatórios

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

## Nota

- Topzera
- Legalzin
- Ok
- Meia boca
- Ruim
