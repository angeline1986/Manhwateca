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

# Dependências

```bash
pip install -r requirements.txt
```

---

# Configuração

Preencher `.env`:

```env
NOTION_TOKEN=
NOTION_DATABASE_ID=
MANGA_ROOT=
```

---

# Scan da biblioteca

```bash
python scripts/scan.py
```

Gera:

```text
data/mangas.json
```

---

# Sync com Notion

```bash
python scripts/sync.py
```

---

# Estrutura esperada da biblioteca

```text
Mangas/
  ABC/
    Antidote/

  DEF/
```

---

# Campos do Notion

| Campo | Tipo |
|---|---|
| Nome | Title |
| Alias | Text |
| Status | Select |
| Nota | Select |
| Último lido | Number |
| Total caps | Number |

---

# Status

- Lendo
- Em espera
- Finalizado
- Hiato
- Dropado
- Quero ler

---

# Nota

- Topzera
- Legalzin
- Ok
- Meh
- Ruim
