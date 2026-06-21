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
- `manhwateca.decision_queue`

Views implementadas:

- `manhwateca.vw_mangas`
- `manhwateca.vw_next_reads`
- `manhwateca.vw_stats`

Infraestrutura implementada:

- conexão PostgreSQL via `DATABASE_URL`;
- camada de repositório;
- `updated_at` automático;
- `sync_events`;
- `decision_queue`;
- índices de `decision_queue` por status, tipo, obra e fonte;
- regras de conflito Notion x PostgreSQL;
- valores oficiais de `notion_sync_status`.

Dados atuais:

| Item | Quantidade |
| ---- | ---------: |
| Obras em `mangas` | 133 |
| Temáticas em `themes` | 30 |
| Relações em `manga_themes` | 576 |

### Diagnóstico Atual

O projeto saiu da fase principal de modelagem e entrou na fase de migração
operacional.

| Área | Estado |
| ---- | ------ |
| Modelagem de banco | praticamente concluída |
| Infraestrutura PostgreSQL | majoritariamente implementada |
| Integração dos fluxos | parcial |
| Desacoplamento de JSON/CSV | inicial |

O gargalo atual não é criar mais estrutura de banco. O gargalo é fazer os
fluxos existentes adotarem as estruturas já criadas.

Regra operacional: não criar novas tabelas até que `decision_queue` esteja
sendo usada por pelo menos um fluxo real, como MangaUpdates ou revisão manual.

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

Status: base implementada. `DATABASE_URL`, `psycopg[binary]`, conexão,
modelos, repositório, temas, leituras de views e testes unitários já existem.
Ainda assim, esta milestone deve continuar sendo tratada como fundação, não
como autorização para remover JSON/CSV.

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

Status: parcial. A web já possui fonte ativa para alternar entre PostgreSQL e
JSON legado, e os principais painéis começam a preferir PostgreSQL. Ainda falta
garantir consistência visual e funcional em todas as telas, especialmente onde
existem ações antigas, mensagens de próximo passo e dados ainda derivados de
artefatos JSON/CSV.

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

Status: integrada de forma incremental. `scripts/scan.py` continua gerando
`data/mangas.json`, mas também tenta salvar no PostgreSQL quando o banco está
configurado. O próximo cuidado é validar em uso real que campos editoriais
manuais nunca sejam sobrescritos pela catalogação.

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

Status: parcial. O fluxo editorial ainda preserva CSV, metadata JSON e
`data/mangas.json`, mas também tenta aplicar alterações no PostgreSQL via
repositório. Ainda não é um fluxo banco-primeiro.

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

Status: parcial. Dados do MangaUpdates já podem atualizar campos e temas no
PostgreSQL, e o painel web de status já prefere o banco quando disponível.
`decision_queue` já existe para substituir o staging de decisões, mas o fluxo
de revisão de candidatos e parte do cache ainda continuam em JSON legado.

### Objetivo

Fazer os dados enriquecidos do MangaUpdates atualizarem o banco diretamente.

### Escopo

- Gravar `work_code`, `mangaupdates_url`, capítulo externo, formato e
  metadados úteis em `mangas`.
- Associar temáticas em `themes` e `manga_themes`.
- Manter `data/mangaupdates.json` como cache temporário.
- Migrar gradualmente candidatos ambíguos, conflitos e decisões humanas para
  `decision_queue`.
- Manter `reports/integrations/buscaIds.json` como compatibilidade enquanto
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

Status: base técnica implementada. Existem constantes de status, regra de
conflito, migration para `updated_at`/`sync_events` e testes. Ainda depende de
aplicação efetiva da migration no banco local/produção e de uso disciplinado
pelos fluxos de sync.

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

Status: núcleo implementado, mas ainda híbrido. O sync já pode carregar
catálogo do PostgreSQL sob opção explícita, mantendo JSON como padrão legado.
Quando `notion_page_id` estiver disponível no catálogo, ele é usado antes da
busca por título. Rodadas aplicadas com origem PostgreSQL persistem
`notion_page_id`, `notion_last_synced_at`, `notion_sync_status` e eventos em
`sync_events`. Falta tornar PostgreSQL o padrão operacional em todos os pontos
de entrada.

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

### Implementado

- `scripts/sync.py --catalog-source postgresql` lê `vw_mangas` por meio do
  repositório.
- Páginas existentes podem ser localizadas por `notion_page_id` antes da busca
  por título normalizado.
- Criação, atualização, pendência, duplicidade e erro podem atualizar os campos
  `notion_*` no PostgreSQL quando a execução é aplicada.
- Eventos de sync são registrados em `sync_events` via `MangaRepository`.
- Simulações não gravam eventos no PostgreSQL.

### Pendência transferida para a Milestone 8

- Remover a operação operacional CSV -> Notion. A base já permite publicar
  metadados a partir do PostgreSQL, mas o fluxo legado de CSV deve continuar
  disponível até a web/menu estarem totalmente orientados ao banco.

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

Status: iniciada. A web já possui uma camada central para identificar a fonte
ativa do catálogo e passa a preferir PostgreSQL em painéis de status, catálogo
e reconciliação do Notion, mantendo JSON como fallback explícito. A redução do
legado agora depende menos de modelagem e mais da adoção operacional de
`decision_queue`, `vw_mangas`, `vw_next_reads` e `sync_events`.

### Objetivo

Transformar JSON e CSV em exportações opcionais, não em fonte operacional.

Esta milestone também cobre a aplicação web acessada em:

```text
http://127.0.0.1:8000/
```

A web deve ficar orientada ao PostgreSQL de ponta a ponta: dashboards,
Biblioteca, Organização, MangaUpdates, Notion, Automação e Configurações devem
exibir a fonte ativa, consumir dados do banco quando disponíveis e sinalizar
claramente quando algum painel ainda estiver usando JSON/CSV legado.

### Escopo

- Marcar comandos legados no README.
- Ajustar menu e web para mostrar a fonte ativa.
- Atualizar a página web local para priorizar PostgreSQL em:
  - visão geral;
  - biblioteca;
  - cards de ações;
  - painéis de Notion;
  - histórico/status de tarefas;
  - mensagens de próximo passo.
- Remover dependência operacional de:
  - `data/mangas.json`;
  - `reports/integrations/manhwateca_import.csv`.
- Manter exports manuais quando úteis.

### Critérios de aceite

- Web funciona com PostgreSQL sem depender do JSON.
- A página `http://127.0.0.1:8000/` deixa claro quando a fonte é PostgreSQL e
  quando algum dado ainda é legado.
- Notion sync funciona sem depender do CSV.
- README explica claramente o novo fluxo.
- Arquivos legados continuam geráveis sob demanda.

### Implementado

- Criada uma camada de fonte ativa para a web decidir entre PostgreSQL e JSON
  legado.
- `/api/status` informa a fonte ativa do catálogo.
- `/api/catalog` reutiliza a fonte ativa e remove detalhes internos antes de
  responder à interface.
- Painel Notion passa a comparar Drive x catálogo usando PostgreSQL quando
  disponível.
- Pendências de CSV deixam de ser tratadas como bloqueio operacional quando
  PostgreSQL está ativo.
- Atualização de metadados do Notion passa a ter fonte `auto`: tenta
  PostgreSQL primeiro e usa CSV apenas como fallback legado.
- Status de metadados registra e expõe a fonte usada na última simulação ou
  aplicação.
- Painel de status MangaUpdates passa a preferir PostgreSQL para contagem de
  IDs confirmados, detalhes já persistidos e próximos detalhes a consultar.
- Revisão de candidatos MangaUpdates permanece marcada como staging JSON
  legado até o fluxo passar a consumir `decision_queue`.

### Próximos cortes

- Fazer MangaUpdates gravar candidatos ambíguos e decisões pendentes em
  `decision_queue`.
- Fazer a revisão manual ler e aplicar decisões a partir de `decision_queue`.
- Tornar catalogação, editorial e sync Notion banco-primeiro nos pontos de
  entrada principais.
- Atualizar textos do README e menu para marcar JSON/CSV como compatibilidade.

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

## Views Implementadas e Propostas

Já implementadas:

### `vw_stats`

Métricas rápidas da biblioteca:

- total de obras;
- lendo;
- finalizadas;
- backlog;
- aguardando atualização.

Também já existem:

- `vw_mangas`: representação principal para consumo da aplicação;
- `vw_next_reads`: fila priorizada de próximas leituras.

Ainda propostas para depois:

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

## Mapeamento do Legado Removível Futuramente

Esta seção é um inventário. Nada deve ser deletado automaticamente. A remoção
só deve acontecer quando houver sinalização explícita de que o fluxo
PostgreSQL substituiu completamente o uso correspondente.

### Arquivos de dados legados

| Item | Uso atual | Pode ser removido quando |
| ---- | --------- | ------------------------ |
| `data/mangas.json` | Catálogo local usado por fluxos antigos, relatórios e fallback web. | Scanner, web, Notion sync e automação lerem do PostgreSQL sem fallback obrigatório. |
| `reports/integrations/manhwateca_import.csv` | Base enriquecida para atualização de metadados no Notion. | O sync de metadados ler diretamente de `vw_mangas`/repositório. |
| `reports/integrations/buscaIds.json` | Revisão e confirmação de IDs MangaUpdates. | IDs confirmados, pendentes e decisões forem persistidos em tabelas do PostgreSQL. |
| `data/mangaupdates.json` | Cache local de detalhes MangaUpdates. | Cache externo for migrado para tabela própria ou campos normalizados no banco. |
| `data/mangaupdates_progress.json` | Progresso de execução dos lotes MangaUpdates. | Controle de lotes estiver em tabela de eventos/status. |
| `reports/integrations/mangaupdates_state.json` | TTL e controle de consultas MangaUpdates. | Estado de consulta estiver no PostgreSQL. |
| `reports/integrations/notion_import_status.json` | Status de importação Notion usado pela web. | `sync_events` e campos `notion_*` alimentarem a web. |

### Scripts e fluxos legados

| Item | Uso atual | Pode ser removido quando |
| ---- | --------- | ------------------------ |
| Fluxos que dependem de `scripts/sync.py` com JSON | Sincronização catálogo -> Notion em modo legado. | O sync via PostgreSQL virar padrão e cobrir criação, atualização e status. |
| Fluxos CSV -> Notion | Atualização de metadados via `manhwateca_import.csv`. | Metadados forem publicados diretamente do banco. |
| Export CSV obrigatório | Ponte entre MangaUpdates, revisão manual e Notion. | CSV virar apenas export manual opcional. |
| Fallback JSON da web | Segurança quando `DATABASE_URL` ou banco falham. | O banco for requisito operacional aceito para a web. |

### Campos legados

| Campo | Motivo para manter agora | Pode ser removido quando |
| ----- | ------------------------ | ------------------------ |
| `interest_level` | Compatibilidade com importação inicial do Notion. | `reading_status_v2` e `personal_rank` estiverem totalmente validados. |
| `reading_status` | Histórico/compatibilidade. | A coluna final de status estiver definida e todos os fluxos usarem o modelo novo. |
| Nome físico `reading_status_v2` | Nome transitório criado para migração segura. | Uma migration futura renomear para `reading_status` sem conflito com legado. |

### Relatórios legados

Relatórios HTML continuam úteis para auditoria e revisão visual. Eles não são
candidatos imediatos à remoção. A mudança esperada é trocar a fonte dos dados
para PostgreSQL quando fizer sentido, mantendo a geração sob demanda.

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
