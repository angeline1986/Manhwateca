# Roadmap de Migração para PostgreSQL

## Objetivo

Transformar o PostgreSQL na fonte técnica principal da Manhwateca, mantendo a
interface web, o menu do terminal e as integrações atuais funcionando durante a
transição.

O fluxo desejado é:

```text
PostgreSQL = fonte da verdade técnica
Notion = interface manual de leitura e progresso
CSV/JSON = legado ou export temporário
```

A migração deve reduzir inconsistências entre `data/mangas.json`,
`reports/integrations/manhwateca_import.csv`, caches locais e Notion.

## Estado Atual

Foi criado um banco PostgreSQL local:

```text
database: manhwateca
schema: manhwateca
```

Tabelas principais:

- `manhwateca.mangas`
- `manhwateca.themes`
- `manhwateca.manga_themes`
- `manhwateca.notion_import`

Views implementadas:

- `manhwateca.vw_mangas`
- `manhwateca.vw_next_reads`

Dados atuais:

| Item | Quantidade |
| ---- | ---------: |
| Obras em `mangas` | 133 |
| Temáticas em `themes` | 30 |
| Relações em `manga_themes` | 576 |

## Decisões Arquiteturais

### PostgreSQL Como Fonte Principal

O banco passa a ser o cadastro principal da biblioteca.

Novas funcionalidades devem consultar ou atualizar o PostgreSQL primeiro. JSON
e CSV continuam existindo por compatibilidade até que os fluxos sejam migrados.

### Notion Como Interface Complementar

O Notion continua útil para consulta visual e atualização manual de:

- leitura;
- status;
- nota;
- prioridade pessoal;
- picância;
- progresso.

Ele não deve mais ser tratado como banco principal.

### Separação de Interesse

O campo antigo `Interesse` misturava status de leitura e prioridade pessoal.

Foram criadas duas colunas:

- `reading_status_v2`
- `personal_rank`

`reading_status_v2` é aceitável como nome de transição no banco, mas não deve
vazar como nome final nas APIs internas. No código novo, o campo deve ser
exposto como `reading_status`. A renomeação física da coluna poderá acontecer
em uma migração futura, depois que os fluxos legados forem estabilizados.

Mapeamento aplicado para status:

| Valor antigo | `reading_status_v2` |
| ------------ | ------------------- |
| `Lendo` | `Lendo` |
| `Finalizado` | `Finalizado` |
| `Aguardando` | `Aguardando Atualização` |
| `Fila de Espera` | `Quero Ler` |
| nulo | `Quero Ler` |

Mapeamento aplicado para prioridade:

| Valor antigo | `personal_rank` |
| ------------ | --------------- |
| `Topzera` | `Topzera` |
| `Legalzin` | `Legalzin` |
| `Despriorizado` | `Despriorizado` |
| nulo | `Normal` |

### Temáticas Normalizadas

Temáticas usam relacionamento N:N:

```text
mangas -> manga_themes -> themes
```

Valores que antes pareciam pertencer ao campo `Universo`, como `Omegaverse` e
`Fantasia`, devem ser tratados como temáticas.

### Formato Mantido Como Texto

`format` permanece `VARCHAR`, porque a lista de formatos é pequena:

- Manhwa
- Manga
- Novel
- Manhwa e Novel

Não há ganho suficiente para criar tabelas `formats` e `manga_formats` agora.

### Identificador Externo

`work_code` representa o antigo campo `ID da obra` vindo do Notion.

Ele possui restrição `UNIQUE` e deve ser usado para evitar duplicidades de uma
mesma obra importada por nomes diferentes.

Nem toda obra nova terá `work_code` no primeiro cadastro. O repositório deve
suportar:

- busca por `work_code`;
- fallback por título normalizado;
- criação temporária sem `work_code`;
- preenchimento posterior do `work_code` sem duplicar a obra.

### Campos de Sincronização com Notion

`notion_sync_status` deve usar valores oficiais:

| Valor | Uso |
| ----- | --- |
| `pending` | Precisa ser criada ou atualizada no Notion. |
| `synced` | Banco e Notion estão alinhados na última verificação. |
| `error` | Última tentativa falhou. |
| `ignored` | Obra intencionalmente fora do sync. |
| `conflict` | Banco e Notion mudaram depois do último sync. |

Antes de migrar o sync do Notion, o banco deve possuir uma forma confiável de
atualizar `updated_at` em todo `UPDATE`, preferencialmente via trigger.

### Regras de Conflito Notion x PostgreSQL

A sincronização deve obedecer regras explícitas:

| Tipo de campo | Fonte vencedora |
| ------------- | --------------- |
| Campos técnicos | PostgreSQL |
| Campos editoriais manuais | Notion pode vencer |
| Ambos alterados após último sync | Marcar `conflict` |

Campos técnicos incluem identificação, caminhos, contagens calculadas,
capítulos detectados e metadados importados de fontes externas.

Campos editoriais incluem status de leitura, nota, prioridade pessoal,
picância e progresso atualizado manualmente.

### `notion_import` Como Staging

`manhwateca.notion_import` é uma tabela de staging/importação.

Ela pode ser usada para carga inicial, auditoria e comparação temporária, mas
não deve virar dependência permanente da aplicação.

### Views Somente Leitura

`vw_mangas` e `vw_next_reads` são representações para consumo.

Qualquer escrita deve acontecer nas tabelas base por meio do repositório.

## Modelo de Dados Relevante

### `manhwateca.mangas`

| Campo | Finalidade |
| ----- | ---------- |
| `id` | ID interno do PostgreSQL. Não usar como referência externa. |
| `work_code` | Identificador externo da obra. Antigo `ID da obra`. |
| `title` | Nome principal da obra. |
| `alternative_title` | Nome em português, aliases e títulos consolidados. |
| `interest_level` | Campo legado. Não usar em novas funcionalidades. |
| `reading_status` | Campo legado. |
| `reading_status_v2` | Status real de leitura. |
| `personal_rank` | Prioridade pessoal. |
| `score` | Nota atribuída. |
| `last_read_chapter` | Último capítulo lido. |
| `latest_available_chapter` | Último capítulo disponível conhecido. |
| `size_label` | Curto, Médio, Grande ou Longo. |
| `count_status` | Classificação auxiliar de contagem. |
| `latest_mangaupdates_chapter` | Último capítulo vindo de fonte externa. |
| `mangaupdates_url` | URL da obra no MangaUpdates. |
| `spice_level` | Picância. |
| `format` | Formato da obra. |
| `notion_page_id` | Página correspondente no Notion. |
| `notion_last_synced_at` | Última sincronização com Notion. |
| `notion_sync_status` | Estado da sincronização. |
| `created_at` | Criação do registro. |
| `updated_at` | Última atualização do registro. |

### `manhwateca.vw_mangas`

View principal para consumo da aplicação.

Deve alimentar:

- tela de Biblioteca;
- buscas;
- listagens gerais;
- APIs internas da web.

### `manhwateca.vw_next_reads`

Fila priorizada de leitura.

Filtra:

```text
reading_status_v2 = 'Quero Ler'
```

Ordena por prioridade:

1. Topzera
2. Legalzin
3. Normal
4. Despriorizado

Depois ordena por título.

## Configuração Necessária

Adicionar em `.env.example`:

```env
DATABASE_URL=postgresql://usuario:senha@localhost:5432/manhwateca
```

Adicionar em `requirements.txt`:

```text
psycopg[binary]
```

`psycopg` deve ser preferido por ser a versão atual do driver PostgreSQL para
Python.

## Regras de Migração

1. Nenhuma tela deve acessar SQL diretamente.
2. Nenhum script deve montar queries espalhadas pelo projeto.
3. Toda leitura e escrita deve passar por uma camada de repositório.
4. JSON e CSV devem continuar funcionando até a troca completa.
5. A migração deve ser reversível por milestone.
6. O menu do terminal e a interface web não devem perder funcionalidades.
7. Notion nunca deve sobrescrever dados locais mais novos sem comparação.

## Arquitetura Proposta

```text
manhwateca/
├── database/
│   ├── __init__.py
│   ├── connection.py
│   ├── manga_repository.py
│   └── models.py
├── catalog/
├── mangaupdates_service/
├── notion_sync/
└── webapp/
```

### `database/connection.py`

Responsável por:

- ler `DATABASE_URL`;
- abrir conexões;
- centralizar configuração do schema `manhwateca`;
- oferecer contexto seguro de transação.

### `database/manga_repository.py`

Responsável por:

- ler `vw_mangas`;
- ler `vw_next_reads`;
- inserir ou atualizar obras;
- atualizar campos editoriais;
- atualizar campos de sincronização com Notion;
- buscar por `work_code`, título ou `notion_page_id`.

Também deve centralizar métodos para temáticas:

- `get_or_create_theme`;
- `add_theme_to_manga`;
- `replace_manga_themes`.

### `database/models.py`

Opcional.

Pode conter dataclasses simples para transportar dados sem acoplar a aplicação
ao formato bruto das linhas SQL.

## Milestone 1: Camada de Conexão e Repositório

### Objetivo

Criar a base mínima para o projeto acessar PostgreSQL sem espalhar SQL pelos
módulos.

Esta milestone deve começar a implementação. Ela não deve mexer em sync Notion,
scanner, remoção de JSON/CSV ou alteração de fluxo da web.

### Escopo

- Adicionar `DATABASE_URL` em `.env.example`.
- Adicionar `psycopg[binary]` em `requirements.txt`.
- Criar `manhwateca/database/connection.py`.
- Criar `manhwateca/database/manga_repository.py`.
- Implementar leituras de `vw_mangas` e `vw_next_reads`.
- Expor `reading_status_v2` no código como `reading_status`.
- Implementar busca por `work_code`, título normalizado e `notion_page_id`.
- Implementar métodos de temas sem duplicação.
- Criar testes unitários com conexão falsa ou funções isoladas.

### Fora do escopo

- Alterar a interface web para usar PostgreSQL.
- Remover JSON ou CSV.
- Alterar sincronização com Notion.
- Alterar o scanner para gravar no banco.
- Alterar o fluxo de MangaUpdates.

### Critérios de aceite

- O projeto importa os novos módulos sem exigir banco ativo.
- A conexão falha com mensagem clara quando `DATABASE_URL` não existe.
- Banco indisponível gera erro claro, sem quebrar importação dos módulos.
- O repositório possui métodos de leitura estáveis.
- Nenhum SQL novo fica espalhado fora de `manhwateca/database/`.
- Os testes cobrem ausência de `DATABASE_URL`, banco indisponível e leitura
  por repositório com cliente falso.
- Nenhum fluxo existente muda de comportamento.

## Milestone 2: Web Lendo do PostgreSQL

### Objetivo

Fazer a interface web consumir `vw_mangas` e `vw_next_reads`.

### Escopo

- Adaptar `manhwateca/webapp/catalog.py`.
- Criar fallback temporário para `data/mangas.json` quando o banco não estiver
  configurado.
- Exibir origem dos dados na interface:

```text
Fonte: PostgreSQL
```

ou:

```text
Fonte: JSON legado
```

- Ajustar tela de Biblioteca para usar os campos novos:
  - `reading_status`;
  - `personal_rank`;
  - `last_read_chapter`;
  - `latest_available_chapter`;
  - `size_label`;
  - `themes`.

### Fora do escopo

- Escrita editorial no banco.
- Sync bidirecional com Notion.

### Critérios de aceite

- A tela abre com dados vindos de `vw_mangas`.
- A fila de próximas leituras usa `vw_next_reads`.
- O fallback JSON continua disponível.
- Nenhum dado aparece como `undefined`.

## Milestone 3: Catalogação Salvando no PostgreSQL

### Objetivo

Permitir que a catalogação atualize o banco, mantendo o JSON como export de
compatibilidade.

### Escopo

- Adaptar `catalog/scanner.py` para gravar em `mangas`.
- Preservar geração de `data/mangas.json`.
- Atualizar:
  - título;
  - aliases;
  - último lido;
  - último capítulo disponível;
  - tamanho;
  - status de contagem;
  - caminho local quando necessário.
- Manter campos editoriais existentes no banco.

Regra obrigatória: a catalogação não pode sobrescrever campos manuais.

### Fora do escopo

- Remover o JSON.
- Mudar regras de padronização de arquivos.

### Critérios de aceite

- Rodar catalogação não apaga `reading_status_v2`, `personal_rank`, `score` ou
  `spice_level`.
- Rodar catalogação não altera `last_read_chapter` quando o campo tiver sido
  atualizado manualmente por uma fonte editorial mais recente.
- Obras novas entram no banco.
- Obras existentes são atualizadas por `work_code` ou título normalizado.
- JSON continua sendo gerado.

## Milestone 4: Editorial Migrado Para PostgreSQL

### Objetivo

Mover edições manuais e metadados editoriais do CSV/JSON para a tabela
`mangas`.

### Escopo

- Adaptar `catalog/editorial.py` e módulos relacionados.
- Atualizar no banco:
  - `reading_status_v2`;
  - `personal_rank`;
  - `score`;
  - `spice_level`;
  - `last_read_chapter`;
  - `format`;
  - `themes`.
- Manter export CSV temporário.

### Fora do escopo

- Remover CSV.
- Alterar layout inteiro da web.

### Critérios de aceite

- Alterações editoriais aparecem em `vw_mangas`.
- CSV exportado reflete o banco.
- Campos manuais não são sobrescritos por importações antigas.

## Milestone 5: MangaUpdates Gravando no PostgreSQL

Status: implementada incrementalmente.

### Objetivo

Fazer os dados enriquecidos do MangaUpdates atualizarem o banco diretamente.

### Escopo

- Gravar `work_code`, `mangaupdates_url`, capítulo externo, formato e
  metadados úteis em `mangas`.
- Associar temáticas em `themes` e `manga_themes`.
- Manter `data/mangaupdates.json` como cache temporário.
- Manter `reports/integrations/buscaIds.json` como arquivo de revisão enquanto
  necessário.

### Fora do escopo

- Remover página de revisão de IDs.
- Remover cache local.

### Critérios de aceite

- ID confirmado atualiza a obra correspondente no banco.
- Temáticas novas são criadas sem duplicar.
- Obras revisadas manualmente preservam a decisão.
- CSV e cache continuam funcionando como compatibilidade.

## Milestone 6: Preparação Para Sync Notion

Status: implementada como base técnica, sem alterar o sync atual.

### Objetivo

Criar os mecanismos de segurança necessários antes de migrar a sincronização
para PostgreSQL.

### Escopo

- Criar trigger de atualização automática de `updated_at`.
- Criar tabela `sync_log` ou `sync_events`.
- Documentar e implementar constantes para `notion_sync_status`.
- Implementar funções auxiliares de decisão de conflito.

### Fora do escopo

- Alterar criação de páginas no Notion.
- Alterar atualização de páginas no Notion.
- Remover CSV.

### Critérios de aceite

- Todo `UPDATE` em `mangas` atualiza `updated_at`.
- Tentativas futuras de sync terão onde registrar sucesso, erro e conflito.
- Regras de conflito podem ser testadas sem chamar a API do Notion.

## Milestone 7: Notion Sync Usando PostgreSQL

### Objetivo

Fazer a sincronização com Notion usar o banco como fonte principal.

Esta milestone só pode começar depois de existir:

- trigger ou mecanismo equivalente para `updated_at`;
- regra formal de conflito Notion x PostgreSQL;
- tabela ou log de eventos de sincronização.

### Escopo

- Usar `notion_page_id` para updates.
- Usar `notion_sync_status` para pendências.
- Atualizar `notion_last_synced_at` após sucesso.
- Criar páginas ausentes com base em `vw_mangas`.
- Atualizar metadados sem depender do CSV.
- Manter CSV como modo legado temporário.
- Registrar cada tentativa em `sync_log` ou `sync_events`.

### Fora do escopo

- Sincronização bidirecional completa.
- Remoção imediata do fluxo CSV.

### Critérios de aceite

- Páginas existentes são atualizadas por `notion_page_id`.
- Páginas sem `notion_page_id` entram como pendentes.
- Rodadas repetidas não geram alterações falsas.
- Notion não apaga campos preenchidos manualmente sem intenção explícita.
- Conflitos são marcados como `conflict` e não são resolvidos
  automaticamente.

## Milestone 8: Redução do Legado JSON/CSV

### Objetivo

Transformar JSON e CSV em exportações opcionais, não em fonte operacional.

### Escopo

- Marcar comandos legados no README.
- Ajustar menu e web para mostrar a fonte ativa.
- Remover dependência operacional de:
  - `data/mangas.json`;
  - `reports/integrations/manhwateca_import.csv`.
- Manter exports manuais quando úteis.

### Critérios de aceite

- Web funciona com PostgreSQL sem depender do JSON.
- Notion sync funciona sem depender do CSV.
- README explica claramente o novo fluxo.
- Arquivos legados continuam geráveis sob demanda.

## Milestone 9: Limpeza e Documentação Final

### Objetivo

Consolidar o novo modelo e remover ambiguidades.

### Escopo

- Atualizar `README.md`.
- Atualizar `docs/arquitetura.md`.
- Atualizar guia web/menu.
- Documentar tabelas e views.
- Documentar fluxo de backup e restore local.
- Listar comandos legados e comandos recomendados.

### Critérios de aceite

- Um novo uso do projeto entende qual é a fonte de verdade.
- O fluxo feliz está documentado de ponta a ponta.
- Caminhos legados estão identificados como compatibilidade.

## Riscos e Cuidados

### Duplicidade de Obras

Obras com nomes diferentes podem representar o mesmo `work_code`.

Mitigação:

- priorizar `work_code`;
- manter `alternative_title`;
- revisar duplicatas antes de inserir.

### Perda de Campos Manuais

Catalogação e importações externas não devem apagar campos editoriais.

Mitigação:

- updates parciais;
- comparação de campos;
- testes de preservação.

### Banco Indisponível

Durante a transição, o projeto deve continuar abrindo com JSON legado.

Mitigação:

- fallback explícito;
- mensagens claras na web;
- diagnóstico de ambiente.

### Migração Parcial

O maior risco é manter três fontes ativas sem indicação clara.

Mitigação:

- exibir fonte de dados na interface;
- registrar no roadmap qual fluxo ainda é legado;
- migrar um domínio por milestone.

## Views Propostas Para Depois

Ainda não implementadas:

### `vw_stats`

Métricas rápidas da biblioteca:

- total de obras;
- lendo;
- finalizadas;
- backlog;
- aguardando atualização.

### `vw_topzera`

Obras com:

```text
personal_rank = 'Topzera'
```

### `vw_backlog`

Equivalente a:

```sql
SELECT *
FROM manhwateca.vw_mangas
WHERE reading_status_v2 = 'Quero Ler';
```

Pode ser desnecessária se `vw_next_reads` já cobrir o uso principal.

## Ordem Recomendada

1. Criar camada de conexão e repositório.
2. Fazer a web ler de `vw_mangas`.
3. Fazer catalogação gravar no PostgreSQL.
4. Migrar edição editorial.
5. Migrar MangaUpdates.
6. Preparar segurança do sync Notion.
7. Migrar Notion sync.
8. Reduzir JSON/CSV para compatibilidade.
9. Atualizar documentação final.

Essa ordem evita mexer primeiro nas partes mais sensíveis, como Notion e
MangaUpdates, antes de existir uma camada de banco estável.
