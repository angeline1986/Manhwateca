# Plano Técnico --- Convivência MangaDex + MangaUpdates no Release Monitor

## 1. Objetivo

Preparar o **Manhwateca** para utilizar **MangaDex e MangaUpdates** no
Release Monitor, removendo o acoplamento técnico do monitor a uma única
fonte.

Este plano trata da **arquitetura e implementação técnica**. Não define
regras de negócio do dashboard.

### Baseline

-   **Branch:** `main`
-   **Commit:** `b90ffc49996f7fc97622ad881ead58ea9073a718`
-   **Mensagem:**
    `fix: paginate release monitor until period exhaustion`
-   **Estado esperado antes de iniciar:** working tree limpo e
    `origin/main` no mesmo commit.

## 2. Princípios da implementação

-   Não remover MangaUpdates.
-   Não substituir diretamente MangaUpdates por MangaDex.
-   Não alterar fluxos MangaUpdates fora do Release Monitor sem
    necessidade técnica.
-   Não reutilizar `work_code` para armazenar UUID MangaDex.
-   Não armazenar UUID MangaDex em `BIGINT`.
-   Não criar `mangadex_releases`.
-   Não hardcodar obras específicas.
-   Não depender da API real nos testes automatizados.
-   Preservar o comportamento atual do Release Monitor durante a
    refatoração.
-   Tornar o domínio de releases independente do provider.

## 3. Arquitetura alvo

``` text
                 ReleaseMonitorService
                         |
                +--------+--------+
                |                 |
                v                 v
           MangaUpdates        MangaDex
                |                 |
                +--------+--------+
                         |
                         v
                  ExternalRelease
                         |
                         v
                 external_releases
```

Os identificadores externos deixam de ser tratados como se fossem um
único identificador universal:

``` text
Obra local
   |
   +-- MangaUpdates -> 39054810010
   |
   +-- MangaDex -> eede42a0-78a1-413d-8cb6-3a03ec365e2b
```

------------------------------------------------------------------------

## 4. Regra de execução dos milestones

Antes de implementar **qualquer milestone**, executar obrigatoriamente
uma etapa de análise do estado atual do repositório.

Este documento descreve a direção arquitetural desejada, mas não deve
ser tratado como uma ordem para criar arquivos, classes, tabelas ou
abstrações sem antes verificar o código existente.

Para **cada milestone**, seguir esta sequência:

### Passo 0 --- Analisar

Antes de alterar qualquer arquivo:

1.  Identificar os arquivos atualmente envolvidos no milestone.
2.  Ler as implementações existentes relacionadas ao objetivo.
3.  Identificar classes, funções, repositories, models, migrations,
    testes, utilitários e padrões arquiteturais já existentes.
4.  Verificar se alguma parte do milestone já está implementada integral
    ou parcialmente.
5.  Identificar dependências e possíveis impactos da alteração.
6.  Verificar se a estrutura sugerida pelo plano é compatível com a
    arquitetura real do repositório.
7.  Evitar criar abstrações, arquivos, tabelas ou helpers que dupliquem
    funcionalidades existentes.

### Passo 1 --- Apresentar diagnóstico

Antes da implementação, apresentar um resumo objetivo contendo:

-   estado atual;
-   arquivos envolvidos;
-   componentes reutilizáveis;
-   lacunas encontradas;
-   alterações realmente necessárias;
-   arquivos que provavelmente serão alterados ou criados;
-   riscos técnicos identificados.

### Passo 2 --- Validar o plano do milestone

Comparar o diagnóstico com o milestone planejado e classificar os itens
relevantes como:

-   **necessário**;
-   **já existente**;
-   **precisa adaptação**;
-   **desnecessário**.

Se a análise mostrar uma solução mais simples ou mais coerente com o
projeto atual, preferir essa solução e explicar objetivamente o motivo.

Não alterar a arquitetura apenas para fazer o código coincidir
literalmente com este documento.

### Passo 3 --- Implementar

Somente após concluir a análise:

-   realizar as alterações necessárias;
-   reutilizar estruturas existentes quando possível;
-   manter o escopo limitado ao milestone;
-   evitar refatorações não relacionadas.

### Passo 4 --- Validar

Executar:

-   testes novos do milestone;
-   testes existentes relacionados;
-   `py_compile` nos arquivos Python alterados;
-   validações adicionais específicas do milestone;
-   inspeção do `git diff`.

### Passo 5 --- Relatar

Ao concluir o milestone, informar:

1.  arquivos alterados;
2.  arquivos criados;
3.  o que foi implementado;
4.  o que foi reutilizado;
5.  diferenças entre o plano original e a implementação real;
6.  testes executados;
7.  resultado dos testes;
8.  pendências ou riscos encontrados;
9.  se o milestone está concluído ou não.

### Regra de avanço

**Não iniciar automaticamente o milestone seguinte.**

Finalizar o milestone atual, apresentar o resultado e aguardar
autorização para continuar.

------------------------------------------------------------------------

## 5. Fronteira de responsabilidade: Service x Provider

A implementação deve preservar uma fronteira explícita entre coordenação
do monitor e detalhes de cada API.

``` text
ReleaseMonitorService
├── decide período/janela de monitoramento
├── coordena providers
├── controla a execução
├── consolida métricas
└── consolida motivo de parada/resultado

Provider
├── conhece endpoints e parâmetros da API externa
├── executa a paginação técnica própria da API
├── transforma o payload externo
└── devolve resultados normalizados
```

Para MangaUpdates, o provider pode conhecer `page` e como obter a
próxima página, mas a decisão relacionada à janela temporal do monitor,
`periods.earliest_start` e ao resultado consolidado da execução deve
permanecer no nível apropriado do serviço.

Para MangaDex, o provider conhece `limit`, `offset`, `total` e
`/manga/{id}/feed`; o serviço decide quais obras devem ser consultadas e
coordena a execução.

Durante a análise do M2, confrontar esta divisão com o código real e
ajustar o contrato se necessário. A responsabilidade por `stop_reason`
deve ficar explícita e testada, evitando dividi-la implicitamente entre
service e provider.

------------------------------------------------------------------------

## 6. Decisão funcional futura: idioma

`translatedLanguage` deve ser preservado desde o MangaDex até a
persistência.

Neste plano não será decidido se o Dashboard deve considerar `pt-br`,
`en`, todos os idiomas ou alguma preferência.

Essa decisão não deve vazar para:

-   MangaDex client;
-   MangaDex provider;
-   parser/mapper de payload.

Qualquer filtro funcional de idioma deverá ser definido posteriormente
em camada apropriada.

------------------------------------------------------------------------

## 7. Regra adicional para migrations

O runner atual reaplica arquivos SQL ordenados e não possui tabela de
controle de migrations.

Portanto, toda migration nova criada neste plano deve seguir o padrão de
idempotência do projeto.

Antes de criar uma migration:

1.  analisar o runner atual;
2.  analisar migrations existentes;
3.  identificar o padrão de idempotência já utilizado;
4.  garantir execução repetida segura;
5.  testar a migration mais de uma vez.

Não alterar migrations antigas já aplicadas.

------------------------------------------------------------------------

# Milestones

## Status de execução

| Milestone | Status | Commit | Observação |
| --------- | ------ | ------ | ---------- |
| M1 --- Generalizar `ExternalRelease` | Concluído | `53ff892` | Domínio usa `provider` e `external_series_id`; persistência MangaUpdates segue específica. |
| M2 --- Abstrair o Release Provider | Concluído | `ef6287b` | `MangaUpdatesReleaseProvider` extraído; service preserva decisões de janela e parada. |
| M3 --- Cliente MangaDex: infraestrutura HTTP | Concluído | `08cc49e` | Cliente HTTP MangaDex criado com `urllib`, exceções próprias e testes dedicados. |
| M4 --- MangaDex: busca de obras | Concluído | `8b5a811` | Busca de candidatos MangaDex implementada sem ligação com o Release Monitor. |
| M5 --- MangaDex: detalhes da obra | Concluído | `41dc3f7` | Consulta de detalhe por UUID preservando payload, links e capítulo mais recente. |
| M6 --- MangaDex: Cover Art | Concluído | `25e10cb` | Extração de cover_art e URLs original/256/512 usando UUID da obra. |
| M7 --- MangaDex: feed de capítulos | Concluído | `3d5ad4b` | Consulta de uma página do feed preservando capítulo, idioma, timestamps e total. |
| M8 --- MangaDex: paginação do feed | Concluído | `4738cab` | Iteração incremental por limit/offset/total com safety limit e avanço por itens recebidos. |
| M9 --- MangaDex: normalização para `ExternalRelease` | Concluído | `67d5e94` | Feed MangaDex normalizado para `ExternalRelease` e provider MangaDex criado sem execução automática. |
| M10 --- Armazenar referências externas por provider | Próximo | - | Iniciar com Passo 0 --- Analisar. |

## M1 --- Generalizar `ExternalRelease`

### Análise prévia obrigatória

Antes de alterar `ExternalRelease`, verificar:

-   todos os locais que instanciam ou consomem `ExternalRelease`;
-   dependências de `series_id` como `int`;
-   serialização, comparação, persistência e testes relacionados;
-   campos equivalentes já existentes;
-   mudanças mínimas necessárias para preservar compatibilidade com
    MangaUpdates.

### Objetivo

Permitir que um release seja proveniente de qualquer provider.

### Modelo sugerido

``` python
@dataclass(frozen=True)
class ExternalRelease:
    provider: str
    external_series_id: str
    external_release_id: str | None
    chapter: str | None
    release_date: date

    volume: str | None = None
    language: str | None = None
    title: str | None = None
    source_url: str | None = None
    raw_payload: dict | None = None
```

### Decisão importante

`external_series_id` deve ser `str`.

Exemplos:

``` text
MangaUpdates:
39054810010

MangaDex:
eede42a0-78a1-413d-8cb6-3a03ec365e2b
```

Não converter UUID MangaDex para número.

### MangaUpdates

O provider atual deve preencher:

``` text
provider = "mangaupdates"
external_series_id = str(series_id)
```

Se não existir ID individual confiável do release:

``` text
external_release_id = None
```

### Testes

-   ID MangaUpdates convertido para string.
-   UUID aceito como `external_series_id`.
-   Campos opcionais.
-   Compatibilidade com MangaUpdates.

### Critério de conclusão

O domínio do Release Monitor não depende mais de `series_id: int`.

------------------------------------------------------------------------

## M2 --- Abstrair o Release Provider

### Análise prévia obrigatória

Antes de criar a abstração de provider, verificar:

-   como `ReleaseMonitorService` chama MangaUpdates hoje;
-   quais responsabilidades estão em `service.py`, `parser.py` e
    `mangaupdates_service/client.py`;
-   onde a paginação do baseline está implementada e quais testes a
    protegem;
-   se existe abstração semelhante de provider/protocol no projeto;
-   se `base.py` é realmente necessário ou se uma interface mais simples
    é suficiente.

### Objetivo

Remover do `ReleaseMonitorService` a responsabilidade de conhecer
diretamente a API do MangaUpdates.

Neste milestone, o comportamento externo do monitor deve permanecer
igual ao baseline.

### Estrutura sugerida

``` text
manhwateca/release_monitor/providers/
    __init__.py
    base.py
    mangaupdates.py
```

Criar uma abstração equivalente a:

``` python
class ReleaseProvider:
    name: str

    def get_releases(self, ...):
        ...
```

Não é obrigatório utilizar `ABC` se isso adicionar complexidade sem
benefício.

### Alterações

Mover para `providers/mangaupdates.py`:

-   chamada ao cliente MangaUpdates;
-   paginação específica;
-   transformação da resposta externa;
-   retorno dos releases no formato interno.

O `ReleaseMonitorService` não deve mais importar diretamente:

``` python
manhwateca.mangaupdates_service.client.list_releases_by_day
```

### Preservar

Manter integralmente a paginação do baseline:

-   consulta até o mês corrente estar esgotado;
-   parada por data somente quando a ordenação observada permitir;
-   `max_pages` apenas como safety limit;
-   motivos atuais de parada preservados.

### Testes

-   `ReleaseMonitorService` usa provider.
-   Provider MangaUpdates retorna `ExternalRelease`.
-   Paginação existente continua funcionando.
-   Motivos de parada permanecem iguais.
-   Não existe chamada direta ao cliente MangaUpdates dentro de
    `service.py`.

### Critério de conclusão

O monitor produz o mesmo resultado funcional antes e depois da
refatoração.

------------------------------------------------------------------------

## M3 --- Cliente MangaDex: infraestrutura HTTP

### Análise prévia obrigatória

Antes de criar o cliente MangaDex, verificar:

-   como os clientes HTTP existentes são implementados;
-   biblioteca HTTP, timeout, retry, rate limit e padrão de exceptions
    existentes;
-   uso de `Session` ou cliente compartilhado;
-   como `mangaupdates_service/client.py` é testado;
-   componentes reutilizáveis sem acoplar MangaDex ao MangaUpdates.

### Objetivo

Criar a infraestrutura mínima de comunicação com MangaDex, sem lógica
específica de busca, capa ou capítulos.

### Arquivos

``` text
manhwateca/mangadex_service/
    __init__.py
    client.py
```

### Base URL

``` text
https://api.mangadex.org
```

### Implementar

-   timeout configurável;
-   `Accept: application/json`;
-   tratamento de HTTP não 2xx;
-   timeout;
-   JSON inválido;
-   resposta estruturalmente inválida;
-   HTTP `429`;
-   suporte a mocks;
-   sem cookies;
-   sem autenticação para os endpoints públicos utilizados.

O cliente deve apenas:

-   construir requests;
-   executar requests;
-   devolver payload;
-   representar falhas de forma coerente.

### Exceções possíveis

``` text
MangaDexError
MangaDexHTTPError
MangaDexRateLimitError
MangaDexPayloadError
```

Adaptar ao padrão já existente no projeto.

### Testes

-   HTTP 200;
-   timeout;
-   404;
-   429;
-   500;
-   JSON inválido;
-   payload vazio;
-   headers.

### Critério de conclusão

Existe uma camada HTTP MangaDex reutilizável e testada.

------------------------------------------------------------------------

## M4 --- MangaDex: busca de obras

### Análise prévia obrigatória

Antes de implementar busca MangaDex, verificar:

-   mecanismos existentes de busca/candidatos;
-   representação atual de resultados externos;
-   normalização existente de títulos e títulos alternativos;
-   paginação/requisição reutilizável;
-   campos do endpoint `/manga` realmente necessários.

### Objetivo

Implementar busca de candidatos no MangaDex.

### Endpoint

``` http
GET /manga
```

Exemplo:

``` text
GET /manga?title=Accidental%20Baby&limit=10
```

### Método sugerido

``` python
search_manga(
    title: str,
    limit: int = 10,
    offset: int = 0,
)
```

### Campos relevantes

``` text
data[].id
data[].attributes.title
data[].attributes.altTitles
data[].attributes.originalLanguage
data[].attributes.status
data[].attributes.year
data[].attributes.links
data[].relationships
```

O método não deve escolher automaticamente o resultado correto.

Não assumir que `attributes.title.en` sempre existe.

### Testes

-   resultado único;
-   nenhum resultado;
-   múltiplos resultados;
-   título sem `en`;
-   `altTitles`;
-   `originalLanguage`;
-   `status`;
-   `links`;
-   UUID.

### Critério de conclusão

É possível pesquisar uma obra e obter candidatos MangaDex sem ligação
com o Release Monitor.

------------------------------------------------------------------------

## M5 --- MangaDex: detalhes da obra

### Análise prévia obrigatória

Antes de implementar detalhes da obra, verificar:

-   modelos/DTOs de metadados externos reutilizáveis;
-   campos que serão consumidos posteriormente;
-   tratamento atual de respostas parciais/nulas;
-   se `links` deve ser preservado como payload ou exposto;
-   evitar modelar dados sem uso.

### Objetivo

Consultar uma obra conhecida pelo UUID MangaDex.

### Endpoint

``` http
GET /manga/{manga_id}
```

### Método sugerido

``` python
get_manga(manga_id: str)
```

### Campos relevantes

``` text
data.id
data.attributes.title
data.attributes.altTitles
data.attributes.description
data.attributes.originalLanguage
data.attributes.status
data.attributes.year
data.attributes.links
data.attributes.latestUploadedChapter
data.relationships
```

Não transformar todo o payload MangaDex em modelos complexos sem
necessidade.

### Links externos

Preservar referências como:

``` text
mu
mal
raw
engtl
```

Não criar associação automática neste milestone.

### Testes

-   UUID válido;
-   obra inexistente;
-   attributes parcial;
-   links ausentes;
-   `latestUploadedChapter` nulo;
-   relationships ausentes/vazios.

### Critério de conclusão

A aplicação consulta detalhes de uma obra MangaDex pelo UUID.

------------------------------------------------------------------------

## M6 --- MangaDex: Cover Art

### Análise prévia obrigatória

Antes de implementar Cover Art, verificar:

-   helpers existentes para capas e URLs externas;
-   onde capas são armazenadas/exibidas;
-   se a URL deve ser persistida ou calculada;
-   como `relationships` será processado;
-   camada mais adequada para o helper de URL.

### Objetivo

Obter os dados da capa e montar corretamente sua URL.

### Endpoint

``` http
GET /manga/{manga_id}?includes[]=cover_art
```

No retorno:

``` text
relationships[]
    type == "cover_art"
```

Com `includes[]=cover_art`, utilizar:

``` text
relationship.attributes.fileName
```

### URLs

Original:

``` text
https://uploads.mangadex.org/covers/{manga_id}/{fileName}
```

256 px:

``` text
https://uploads.mangadex.org/covers/{manga_id}/{fileName}.256.jpg
```

512 px:

``` text
https://uploads.mangadex.org/covers/{manga_id}/{fileName}.512.jpg
```

### Atenção

Não usar `cover_art.id` no lugar de `manga_id`.

### Helper sugerido

``` python
build_cover_url(
    manga_id: str,
    file_name: str,
    size: int | None = None,
)
```

Inicialmente aceitar:

``` text
None
256
512
```

Não fazer download da imagem.

### Testes

-   cover encontrado;
-   cover ausente;
-   `fileName` ausente;
-   URL original;
-   URL 256;
-   URL 512;
-   proteção contra uso incorreto de `cover_art.id`.

### Critério de conclusão

A aplicação consegue gerar corretamente a URL da capa MangaDex.

------------------------------------------------------------------------

## M7 --- MangaDex: feed de capítulos

### Análise prévia obrigatória

Antes de implementar o feed, verificar:

-   campos que o Release Monitor atual realmente precisa;
-   tratamento atual de capítulos não numéricos;
-   normalização de datas/timestamps, volume e idioma;
-   tratamento de payloads vazios/incompletos;
-   garantir que regras de seleção/idioma não sejam colocadas nesta
    camada.

### Objetivo

Consultar capítulos/releases de uma obra específica.

### Endpoint

``` http
GET /manga/{manga_id}/feed
```

Exemplo:

``` text
GET /manga/{id}/feed?limit=100&order[publishAt]=desc
```

### Método sugerido

``` python
get_manga_feed(
    manga_id: str,
    limit: int = 100,
    offset: int = 0,
    order: str = "desc",
)
```

### Campos relevantes

``` text
data[].id

data[].attributes.volume
data[].attributes.chapter
data[].attributes.title
data[].attributes.translatedLanguage
data[].attributes.publishAt
data[].attributes.readableAt
data[].attributes.createdAt
data[].attributes.updatedAt

data[].relationships

limit
offset
total
```

### Cuidados técnicos

Não assumir que `chapter` é inteiro.

Pode ser:

``` text
null
decimal
texto especial
extra
```

Não converter prematuramente para `int`.

Preservar `translatedLanguage`.

Não filtrar idioma neste milestone.

Tratar `publishAt` como o timestamp fornecido pelo MangaDex para aquele
release.

### Testes

-   feed com capítulos;
-   feed vazio;
-   chapter nulo;
-   chapter decimal;
-   volume nulo;
-   idioma;
-   `publishAt`;
-   `readableAt`;
-   múltiplos idiomas;
-   `total > limit`;
-   offset.

### Critério de conclusão

Dado um UUID MangaDex, a aplicação consegue listar os releases da obra
com capítulo, idioma e data.

------------------------------------------------------------------------

## M8 --- MangaDex: paginação do feed

### Análise prévia obrigatória

Antes de implementar paginação MangaDex, verificar:

-   utilitários existentes de `limit/offset`;
-   se o client deve retornar páginas ou iterar resultados;
-   consumo de memória;
-   proteções existentes contra loop infinito;
-   tratamento de `total` inconsistente;
-   separação em relação à paginação MangaUpdates.

### Objetivo

Percorrer feeds cujo total exceda o `limit`.

### Modelo MangaDex

MangaDex trabalha com:

``` text
limit
offset
total
```

Não reutilizar a paginação por `page` do MangaUpdates.

### Fluxo

``` text
offset = 0

GET feed?limit=100&offset=0

se:
offset + quantidade_recebida < total

então:
offset += quantidade_recebida

repetir
```

Encerrar quando:

-   atingir `total`;
-   resposta vazia;
-   safety limit;
-   erro.

### Método possível

``` python
iter_manga_feed(...)
```

ou:

``` python
get_all_manga_feed(...)
```

Preferir processamento incremental caso isso combine melhor com a
arquitetura existente.

### Testes

-   uma página;
-   duas páginas;
-   última página parcial;
-   resposta vazia antes de `total`;
-   `total` inconsistente;
-   safety limit;
-   offset correto.

### Critério de conclusão

Todo o feed MangaDex pode ser percorrido corretamente.

------------------------------------------------------------------------

## M9 --- MangaDex: normalização para `ExternalRelease`

### Análise prévia obrigatória

Antes de criar `MangaDexReleaseProvider`, verificar:

-   contrato real produzido por M1/M2;
-   onde ocorre a transformação MangaUpdates;
-   parsers/mappers reutilizáveis;
-   campos obrigatórios reais de `ExternalRelease`;
-   separação correta entre client, provider e transformação.

### Objetivo

Converter itens MangaDex para o domínio comum do Release Monitor.

### Arquivo

``` text
manhwateca/release_monitor/providers/mangadex.py
```

### Mapeamento

``` text
provider
    -> "mangadex"

external_series_id
    -> manga UUID

external_release_id
    -> data[].id

chapter
    -> attributes.chapter

volume
    -> attributes.volume

language
    -> attributes.translatedLanguage

release_date / published_at
    -> attributes.publishAt

title
    -> attributes.title

raw_payload
    -> item original
```

### Separação

``` text
client
    -> HTTP

provider
    -> integração com Release Monitor

parser/helper
    -> transformação de payload, se necessário
```

### Testes

-   transformação completa;
-   campos nulos;
-   UUID;
-   chapter textual;
-   `publishAt` inválido;
-   idioma;
-   raw payload.

### Critério de conclusão

MangaDex e MangaUpdates produzem o mesmo tipo `ExternalRelease`.

------------------------------------------------------------------------

## M10 --- Referências externas das obras

### Análise prévia obrigatória

Antes de criar `manga_external_refs`, verificar:

-   como `mangas` armazena IDs externos;
-   todos os usos de `work_code`;
-   outras colunas/tabelas de IDs externos;
-   convenção de migrations, FKs e tipo de `mangas.id`;
-   repositories reutilizáveis;
-   views/queries dependentes de `work_code`;
-   impacto e idempotência da migração.

### Objetivo

Permitir que uma obra tenha IDs externos de múltiplos providers.

### Nova migration

Não alterar migrations já aplicadas.

Criar tabela conceitualmente equivalente a:

``` text
manga_external_refs
```

### Estrutura sugerida

``` text
id
manga_id
provider
external_id
external_url
external_title
metadata
created_at
updated_at
```

`external_id` deve ser `TEXT`.

### Constraints

``` text
UNIQUE (manga_id, provider)
UNIQUE (provider, external_id)
```

Foreign key:

``` text
manga_id -> mangas.id
```

### Operações mínimas

``` text
get_external_ref(manga_id, provider)

list_external_refs(manga_id)

upsert_external_ref(...)

find_manga_by_external_id(provider, external_id)
```

### Migração dos IDs atuais

Copiar IDs MangaUpdates conhecidos para:

``` text
provider = "mangaupdates"
external_id = valor atual
```

Não apagar o valor antigo.

Não remover `work_code`.

A migração deve ser idempotente.

### Testes

-   MangaUpdates ID;
-   MangaDex UUID;
-   mesma obra com dois providers;
-   impedir mesmo external ID/provider em obras diferentes;
-   upsert;
-   idempotência.

### Critério de conclusão

Uma obra pode possuir simultaneamente referências MangaUpdates e
MangaDex.

------------------------------------------------------------------------

## M11 --- Armazenamento genérico de releases

### Análise prévia obrigatória

Antes de criar `external_releases`, verificar:

-   schema, índices e constraints de `mangaupdates_releases`;
-   repository e queries atuais;
-   estratégia atual de deduplicação/upsert;
-   uso de `first_seen_at`, `last_seen_at` e `viewed_at`;
-   views/APIs dependentes da tabela antiga;
-   como preservar compatibilidade sem duplicar persistência.

### Compatibilidade com o Dashboard

A criação de `external_releases` não deve alterar automaticamente as
queries atuais do Dashboard.

Enquanto a migração de leitura não ocorrer no milestone específico:

-   preservar os contratos atuais;
-   manter a fonte de leitura existente funcionando;
-   não trocar summary/lista silenciosamente para a tabela nova.

### Objetivo

Permitir persistência de releases de qualquer provider.

### Nova tabela

``` text
external_releases
```

Não apagar `mangaupdates_releases` ainda.

### Estrutura sugerida

``` text
id
manga_id
provider
external_series_id
external_release_id
chapter
normalized_chapter
volume
normalized_volume
release_date
published_at
language
title
source_url
raw_payload
first_seen_at
last_seen_at
viewed_at
```

Adaptar ao padrão real do banco.

Não duplicar normalizadores existentes.

### Unicidade

Para MangaDex, quando houver ID:

``` text
(provider, external_release_id)
```

Para provider sem ID individual, utilizar chave determinística coerente,
baseada por exemplo em:

``` text
provider
external_series_id
chapter
volume
release_date
```

### Testes

-   insert MangaUpdates;
-   insert MangaDex;
-   duplicata MangaDex;
-   `last_seen_at`;
-   raw payload;
-   mesmo capítulo em providers diferentes;
-   UUID;
-   chapter não numérico;
-   volume opcional.

### Critério de conclusão

O banco armazena releases de múltiplas fontes sem tabela específica por
provider.

------------------------------------------------------------------------

## M12 --- MangaDex: execução eficiente e incremental

### Análise prévia obrigatória

Antes de implementar qualquer otimização, verificar:

-   quantas obras monitoradas existem atualmente e quantas possuem
    MangaDex ID;
-   como o monitor registra hoje a última execução/check;
-   se existe `last_checked_at`, cache ou estado equivalente
    reutilizável;
-   limites/rate limits observados ou documentados da API MangaDex;
-   comportamento atual do cliente diante de HTTP 429;
-   possibilidade de processamento incremental por obra;
-   necessidade real de concorrência e como limitá-la;
-   custo de executar uma chamada `/manga/{id}/feed` para cada obra;
-   como evitar reconsultar histórico completo sem necessidade;
-   como métricas da execução são registradas atualmente.

### Objetivo

Preparar tecnicamente a execução MangaDex para um conjunto grande de
obras antes de conectá-la ao monitor multi-provider.

O MangaUpdates atual pode consultar releases de forma agregada. O
MangaDex via `/manga/{id}/feed` tende a exigir consulta por obra,
portanto o custo operacional é diferente.

### Implementar conforme diagnóstico

Prever mecanismos compatíveis com a arquitetura real para:

-   registrar/checkar última consulta por obra/provider;
-   permitir consulta incremental;
-   evitar reprocessamento desnecessário de histórico;
-   respeitar HTTP 429 e rate limits;
-   controlar concorrência caso ela seja utilizada;
-   definir safety limits;
-   produzir métricas de chamadas, itens processados e falhas.

Não adicionar paralelismo apenas por desempenho aparente. Primeiro
preservar previsibilidade e respeito à API.

Não colocar regras funcionais de idioma ou seleção de capítulos nesta
camada.

### Testes

Cobrir, conforme a implementação escolhida:

-   primeira execução;
-   execução subsequente;
-   estado de última consulta;
-   feed sem novidade;
-   paginação incremental;
-   HTTP 429;
-   retry/backoff, se implementado;
-   limite de concorrência, se implementado;
-   falha em uma obra sem corromper estado das demais;
-   safety limit.

### Critério de conclusão

O custo de consultar MangaDex para muitas obras está controlado e
observável antes de habilitar o fluxo multi-provider.

------------------------------------------------------------------------

## M13 --- Release Monitor multi-provider

### Análise prévia obrigatória

Antes de tornar o service multi-provider, verificar:

-   contrato final dos providers;
-   como obras monitoradas são carregadas;
-   como resolver provider + external ID sem condicionais específicas;
-   tratamento atual de erros e métricas;
-   melhor unidade de execução segundo o código real;
-   impacto em scripts/endpoints consumidores.

### Objetivo

Permitir que `ReleaseMonitorService` execute providers diferentes.

### Estrutura

``` text
ReleaseMonitorService
        |
        +--- MangaUpdatesReleaseProvider
        |
        +--- MangaDexReleaseProvider
```

O service não deve conhecer endpoints específicos.

Evitar lógica como:

``` python
if provider == "mangadex":
    # chama endpoint MangaDex

if provider == "mangaupdates":
    # chama endpoint MangaUpdates
```

Essa responsabilidade pertence ao provider.

### Entrada

Utilizar `manga_external_refs` para localizar IDs externos.

### Resultado técnico da execução

Registrar pelo menos:

``` text
provider
quantidade consultada
quantidade persistida
falhas
```

Falhas de um provider devem ser isoladas quando possível.

### Testes

-   somente MangaUpdates;
-   somente MangaDex;
-   ambos;
-   MangaDex falha;
-   MangaUpdates falha;
-   nenhum external ref;
-   provider desconhecido.

### Critério de conclusão

Uma execução do Release Monitor processa MangaDex e MangaUpdates usando
a mesma camada de domínio.

------------------------------------------------------------------------

## M14 --- Comparação e validação

### Análise prévia obrigatória

Antes da comparação real, verificar:

-   observabilidade já existente;
-   obras com referências válidas nas duas fontes;
-   forma de comparar sem alterar dados indevidamente;
-   necessidade de dry-run/relatório;
-   métricas técnicas disponíveis;
-   como registrar divergências sem interpretá-las como erro.

### Objetivo

Validar tecnicamente as duas integrações antes de remover qualquer
componente antigo.

### Registrar

``` text
provider
external_series_id
quantidade de releases
capítulos
datas
erros
```

Executar uma amostra real de obras com IDs nas duas fontes.

`Accidental Baby` pode ser usada como uma das obras de validação, mas
nunca deve existir tratamento especial para ela no código.

### Exemplo de relatório

``` text
Manga ID local: 123

MangaUpdates
  external_id: 39054810010
  releases: X

MangaDex
  external_id: eede42a0-...
  releases: Y
```

Não interpretar automaticamente divergências como erro.

### Critério de conclusão

É possível comparar claramente os dados técnicos retornados pelos dois
providers para a mesma obra.

------------------------------------------------------------------------

## M15 --- Migração controlada das leituras do Dashboard

### Análise prévia obrigatória

Antes de alterar qualquer leitura do Dashboard, verificar:

-   quais endpoints/queries alimentam summary, lista e demais
    componentes do Release Monitor;
-   quais deles leem diretamente `mangaupdates_releases`;
-   quais repositories/views participam dessas consultas;
-   quais contratos de resposta a interface espera;
-   se `external_releases` já contém dados suficientes e equivalentes;
-   como manter rollback simples;
-   quais testes protegem os endpoints e a interface atual.

### Objetivo

Migrar de forma controlada as leituras do Dashboard da persistência
antiga para a persistência genérica.

### Compatibilidade obrigatória até este milestone

Durante M11-M14:

``` text
external_releases
    -> nova persistência multi-provider

mangaupdates_releases
    -> permanece atendendo as leituras atuais do Dashboard,
       quando ainda for a fonte utilizada pelo código existente
```

Criar `external_releases` não autoriza alterar silenciosamente queries
de summary/lista.

A mudança de leitura deve acontecer somente neste milestone, após
validação da persistência e comparação entre providers.

### Implementação

Com base no diagnóstico:

-   migrar queries/repositories necessários;
-   preservar contratos de resposta quando possível;
-   adaptar somente o necessário;
-   manter estratégia de rollback;
-   remover dependência da tabela antiga apenas onde a migração estiver
    comprovadamente concluída.

Não remover a tabela antiga neste milestone.

### Testes

-   summary antes/depois;
-   lista antes/depois;
-   obra somente MangaUpdates;
-   obra somente MangaDex;
-   obra com ambos;
-   ausência de releases;
-   regressão dos contratos HTTP;
-   queries e views afetadas.

### Critério de conclusão

O Dashboard lê a persistência genérica de forma controlada, testada e
reversível.

------------------------------------------------------------------------

## M16 --- Limpeza técnica e documentação

### Análise prévia obrigatória

Antes da limpeza, verificar:

-   componentes antigos ainda consumidos;
-   imports/funções realmente sem uso;
-   dependências fora do Release Monitor;
-   compatibilidade com migrations antigas;
-   referências restantes a `work_code`, `series_id` inteiro e
    `mangaupdates_releases`;
-   documentação a atualizar.

### Objetivo

Remover acoplamentos que ficaram obsoletos após a implementação.

### Revisar

-   imports MangaUpdates dentro de `release_monitor`;
-   acessos diretos a `mangaupdates_releases`;
-   dependências de `series_id` como inteiro;
-   dependências de `work_code` dentro do Release Monitor;
-   código duplicado;
-   parsers sem uso.

### Não fazer

-   não remover MangaUpdates de outros fluxos;
-   não remover migrations antigas;
-   não remover `work_code` nesta implementação.

### Documentar

``` text
Release Monitor
    |
    +-- providers
    |     +-- MangaUpdates
    |     +-- MangaDex
    |
    +-- ExternalRelease
    |
    +-- external_releases
```

------------------------------------------------------------------------

# Ordem resumida revisada

``` text
M1   [concluído - 53ff892]
     Generalizar ExternalRelease de forma compatível

M2   [concluído - ef6287b]
     Extrair MangaUpdatesReleaseProvider
     preservando no service a coordenação da janela/período

M3   [concluído - 08cc49e]
     Criar infraestrutura HTTP MangaDex

M4   [próximo]
     Implementar busca de obras MangaDex

M5   Implementar detalhes da obra MangaDex

M6   Implementar Cover Art MangaDex

M7   Implementar feed de capítulos MangaDex

M8   Implementar paginação limit/offset MangaDex

M9   Criar MangaDexReleaseProvider

M10  Criar manga_external_refs

M11  Criar external_releases
     + deduplicação explícita
     + compatibilidade com persistência/leitura antiga

M12  Preparar execução MangaDex eficiente
     + estado de última consulta
     + incremental
     + rate limit
     + concorrência controlada, se necessária
     + observabilidade de custo

M13  Tornar ReleaseMonitorService multi-provider

M14  Comparar MangaDex x MangaUpdates

M15  Migrar controladamente as leituras do Dashboard

M16  Limpeza técnica e documentação
```

# Estrutura de arquivos esperada

``` text
manhwateca/

    mangadex_service/
        __init__.py
        client.py

    mangaupdates_service/
        ...

    release_monitor/
        __init__.py
        models.py
        repository.py
        service.py

        providers/
            __init__.py
            base.py
            mangaupdates.py
            mangadex.py

    database/
        migrations/
            ...
            <migration external refs>
            <migration external releases>

tests/

    test_release_monitor.py
    test_release_provider_mangaupdates.py
    test_release_provider_mangadex.py
    test_mangadex_client.py
    test_external_refs_repository.py
```

Os nomes devem ser adaptados ao padrão real do repositório. Não criar
arquivos apenas para reproduzir esta estrutura se não houver
necessidade.

# Validação por milestone

Ao terminar cada milestone:

1.  Executar testes específicos da alteração.
2.  Executar toda a suíte relacionada ao Release Monitor.
3.  Executar `py_compile` nos arquivos Python modificados.
4.  Validar migrations quando aplicável.
5.  Revisar `git diff`.
6.  Não avançar se o milestone quebrar comportamento existente.

Ao final:

-   executar a suíte completa disponível;
-   registrar arquivos alterados;
-   registrar migrations criadas;
-   registrar quantidade e resultado dos testes;
-   registrar limitações encontradas.

# Resultado arquitetural esperado

``` text
Obra local
   |
   +-- MangaUpdates external ref
   |
   +-- MangaDex external ref
           |
           v
     Release Providers
           |
           v
      ExternalRelease
           |
           v
    external_releases
```

A arquitetura deve permitir que uma terceira fonte seja adicionada
futuramente principalmente através de:

``` text
novo client
+
novo provider
```

sem exigir reescrita do `ReleaseMonitorService` ou criação de uma nova
tabela de releases específica para cada fonte.
