# Arquitetura da Manhwateca

## Visão geral

O projeto usa uma arquitetura modular simples:

```text
scripts/       Fachadas executáveis e compatibilidade de CLI
manhwateca/    Regras de negócio e serviços importáveis
config/        Correções e metadados mantidos manualmente
data/          Catálogo e caches gerados
reports/       Relatórios, logs e arquivos de integração
tests/         Testes automatizados
```

Os comandos conhecidos continuam em `scripts/`, mas a aplicação web poderá
importar diretamente os serviços de `manhwateca/` sem executar subprocessos.

## Módulos

| Pacote | Responsabilidade |
| ------ | ---------------- |
| `application` | Menu, confirmações e composição dos fluxos |
| `catalog` | Descoberta, catalogação, progresso e auditoria |
| `file_normalizer` | Padronização segura de capítulos e capas |
| `library_organizer` | Organização das obras em grupos alfabéticos |
| `mangaupdates_service` | Busca, matching, cache e exportação da API |
| `notion_sync` | Matching, criação e atualização de páginas |
| `reporting` | Componentes e escrita compartilhada de HTML |
| `shared` | Caminhos, títulos, capítulos e utilitários comuns |

## Dependências

```text
scripts
  -> application / serviços de domínio

application
  -> comandos públicos em scripts

catalog, file_normalizer, library_organizer
  -> shared
  -> reporting

mangaupdates_service
  -> shared
  -> reporting

notion_sync
  -> shared
```

Os pacotes de domínio não importam `scripts`. Isso evita efeitos colaterais ao
usar os serviços posteriormente por uma API web.

## Como adicionar uma integração

1. Crie um pacote em `manhwateca/` com cliente, regras e persistência separados.
2. Mantenha chamadas externas fora das regras puras de matching ou parsing.
3. Crie uma fachada pequena em `scripts/` somente quando houver comando CLI.
4. Adicione testes com clientes falsos; não dependa da API real.
5. Registre arquivos gerados em `README.md` e no guia do menu.
6. Use `manhwateca.reporting` para escrita de relatórios HTML.

## Limite de tamanho

O objetivo é manter módulos abaixo de 170 linhas. As exceções atuais são:

- workflows com relatórios HTML autossuficientes de organização e renomeação;
- relatório interativo de revisão de IDs;
- módulo de compatibilidade do MangaUpdates, que preserva funções importadas
  pelos testes e por comandos existentes.

Nessas exceções, as regras de negócio já estão isoladas em módulos menores.
