# Roadmap de Performance e Sincronização Incremental

## Objetivo

Reduzir trabalho repetido, chamadas externas e atualizações desnecessárias no
Notion e no MangaUpdates.

A meta é mudar o comportamento atual de:

```text
rodar tudo novamente
```

para:

```text
detectar o que mudou e processar somente pendências reais
```

O sistema deve continuar seguro: simular antes de aplicar, preservar campos
manuais e manter compatibilidade com o menu do terminal e com a interface web.

## Princípios

1. Nunca atualizar página do Notion sem diferença real.
2. Nunca consultar MangaUpdates se o cache ainda for válido.
3. Registrar estado por obra, não apenas por execução.
4. Separar criação, atualização local, metadados e auditoria.
5. Mostrar pendências acionáveis na interface.
6. Manter logs simples e rastreáveis.
7. Evitar mudanças grandes em múltiplos fluxos no mesmo milestone.

## Situação Atual

Hoje alguns fluxos ainda fazem mais trabalho do que precisam:

- `scripts/notion_csv.py --apply` percorre todas as linhas do CSV.
- A atualização de páginas existentes pode reenviar campos iguais.
- O status do Notion depende do último relatório gerado.
- Obras novas podem exigir mais de uma etapa até entrarem no CSV.
- O cache do MangaUpdates existe, mas ainda não possui validade explícita.
- A interface mostra ações, mas nem sempre mostra a fila real de pendências.

## Arquivos de Estado Propostos

```text
reports/integrations/sync_state.json
reports/integrations/mangaupdates_state.json
reports/integrations/pending_actions.json
```

### `sync_state.json`

Estado de sincronização com o Notion.

```json
{
  "works": {
    "The Trapped Beast": {
      "notion_page_id": "abc",
      "csv_hash": "sha256...",
      "catalog_hash": "sha256...",
      "last_synced_at": "2026-06-17T10:00:00-03:00",
      "status": "sincronizado"
    }
  }
}
```

### `mangaupdates_state.json`

Estado de consultas externas.

```json
{
  "series": {
    "15541779211": {
      "last_checked_at": "2026-06-17T10:00:00-03:00",
      "cache_hash": "sha256...",
      "status": "cache_valido"
    }
  }
}
```

### `pending_actions.json`

Fila consolidada para a interface web.

```json
{
  "catalog": ["Catalogar biblioteca"],
  "mangaupdates": ["Consultar detalhes de 3 IDs"],
  "notion": ["Atualizar 5 páginas", "Criar 1 página"]
}
```

## Milestone 1: Diff Antes de Atualizar o Notion

**Status:** concluído em 17 de junho de 2026.

Resultado validado em simulação real:

```text
Atualizações: 0
Sem alteração: 133
Ausentes no Notion: 0
Duplicados bloqueados: 0
```

### Objetivo

Evitar que `CSV -> Notion` atualize todas as páginas quando só poucas mudaram.

### Escopo

- Ler páginas atuais do Notion.
- Converter propriedades atuais para um formato comparável.
- Comparar propriedades atuais com as propriedades geradas pelo CSV.
- Atualizar somente páginas com diferenças reais.
- Registrar quais campos mudariam na simulação.

### Fora do escopo

- Alterar criação de páginas novas.
- Alterar busca de IDs no MangaUpdates.
- Criar nova tela web.

### Entregáveis

- Função de comparação em `manhwateca/notion_sync/`.
- Resumo com:
  - páginas verificadas;
  - páginas sem alteração;
  - páginas com alteração;
  - campos alterados.
- Testes com cliente Notion falso.

### Critérios de aceite

- Simulação lista somente alterações reais.
- Aplicação não chama `pages.update` quando nada mudou.
- Campos manuais vazios no CSV não apagam valores no Notion.
- O menu do terminal continua funcionando.

## Milestone 2: Estado de Sincronização por Obra

### Objetivo

Guardar um histórico simples para saber o que já foi sincronizado.

### Escopo

- Criar `reports/integrations/sync_state.json`.
- Salvar `page_id` do Notion por obra.
- Salvar hash da linha do CSV.
- Salvar hash do registro do catálogo.
- Atualizar o estado após simulação e aplicação.

### Fora do escopo

- Trocar a lógica de matching por completo.
- Remover `notion_import_status.json`.

### Entregáveis

- Repositório de leitura/escrita do estado.
- Hash estável para linha do CSV e item do catálogo.
- Estado exibido na API/web.

### Critérios de aceite

- Rodadas repetidas não geram pendências falsas.
- Obra alterada no CSV aparece como pendente.
- Obra nova no catálogo aparece como não sincronizada.

## Milestone 3: Fila de Pendências Reais na Web

### Objetivo

Mostrar na interface exatamente o que precisa ser feito.

### Escopo

- Criar endpoint de pendências.
- Consolidar pendências de:
  - catálogo local;
  - organização;
  - MangaUpdates;
  - CSV;
  - Notion.
- Exibir cards acionáveis na visão geral.

### Exemplos de mensagens

```text
3 obras novas precisam ser catalogadas.
5 obras têm ID confirmado e ainda não entraram no CSV.
2 páginas do Notion têm metadados pendentes.
0 chamadas MangaUpdates necessárias.
```

### Critérios de aceite

- A tela inicial deixa claro o próximo passo.
- Cards levam para a seção correta.
- Simulação e aplicação ficam visualmente distintas.
- Nenhum card genérico aparece sem ação possível.

## Milestone 4: Cache Inteligente do MangaUpdates

### Objetivo

Evitar chamadas repetidas à API e permitir atualização controlada.

### Escopo

- Criar `reports/integrations/mangaupdates_state.json`.
- Registrar `last_checked_at` por ID.
- Definir validade padrão do cache.
- Adicionar opção de forçar atualização.
- Atualizar somente IDs:
  - sem cache;
  - com cache expirado;
  - marcados manualmente para atualizar.

### Critérios de aceite

- IDs já consultados não chamam a API novamente.
- A interface informa quantas chamadas serão feitas antes de iniciar.
- Existe opção explícita para forçar atualização.
- Delay entre requisições continua respeitado.

## Milestone 5: CSV Incremental e Autorreparável

### Objetivo

Manter `manhwateca_import.csv` sempre alinhado ao catálogo local sem regenerar
tudo nem perder campos manuais.

### Escopo

- Detectar obras do catálogo ausentes no CSV.
- Criar linhas novas com dados locais e cache disponível.
- Preservar `Interesse`, `Status`, `Nota`, `Picância` e campos editoriais.
- Marcar linhas órfãs, quando a obra saiu do catálogo.

### Critérios de aceite

- Obra nova catalogada entra no CSV sem regeneração total.
- Linha existente não perde campos preenchidos manualmente.
- Obras removidas não são apagadas sem confirmação.
- A interface mostra quantidade de linhas criadas, atualizadas e órfãs.

## Milestone 6: Lotes Mais Granulares no Notion

### Objetivo

Separar melhor criação, contagem e metadados.

### Escopo

- Lote de criação: somente páginas ausentes.
- Lote de contagem: capítulos, último lido, tamanho e status da contagem.
- Lote de metadados: ID, link, formato, temática, universo e picância.
- Lote editorial: campos manuais, quando desejado.

### Critérios de aceite

- Cada lote informa impacto antes de aplicar.
- A aplicação de um lote não altera campos fora do seu escopo.
- É possível atualizar só contagens sem tocar metadados.
- É possível atualizar só metadados sem tocar progresso de leitura.

## Milestone 7: Histórico e Diagnóstico de Performance

### Objetivo

Medir tempo, chamadas externas e volume de alterações por execução.

### Escopo

- Registrar duração por tarefa.
- Registrar quantidade de chamadas Notion e MangaUpdates.
- Registrar páginas alteradas, ignoradas e com erro.
- Exibir resumo no histórico da web.

### Critérios de aceite

- Cada tarefa mostra tempo total.
- Cada tarefa mostra quantidade de chamadas externas.
- Erros ficam associados à obra afetada.
- O histórico ajuda a decidir se vale rodar novamente.

## Ordem Recomendada

1. Milestone 1: diff antes de atualizar Notion.
2. Milestone 5: CSV incremental e autorreparável.
3. Milestone 2: estado por obra.
4. Milestone 3: fila de pendências reais na web.
5. Milestone 4: cache inteligente do MangaUpdates.
6. Milestone 6: lotes granulares no Notion.
7. Milestone 7: diagnóstico de performance.

## Validação Econômica

Para evitar esforço excessivo:

- usar testes unitários com clientes falsos;
- não chamar Notion ou MangaUpdates em testes automatizados;
- testar cada milestone com uma simulação real antes de aplicar;
- rodar suíte completa somente ao final de milestones com impacto amplo;
- registrar no histórico quantas chamadas externas seriam feitas.

## Resultado Esperado

Ao final, o fluxo deve responder perguntas como:

```text
O que mudou desde a última execução?
O que precisa ser enviado ao Notion?
Quais obras precisam consultar MangaUpdates?
Quantas chamadas externas serão feitas?
Quais ações são seguras e quais alteram dados?
```

O ganho principal será um processo mais rápido, previsível e menos cansativo:
menos cliques, menos chamadas, menos atualizações desnecessárias e menos
dúvida sobre o próximo passo.
