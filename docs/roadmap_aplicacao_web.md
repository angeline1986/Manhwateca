# Roadmap da Aplicação Web

> Pré-requisito recomendado: concluir a modularização descrita em
> [`roadmap_refatoracao.md`](roadmap_refatoracao.md). O menu e
> a aplicação web devem consumir os mesmos serviços internos.

## Objetivo

Evoluir a interface atual de terminal para uma aplicação web local, mantendo
as regras, scripts, configurações, dados, relatórios e testes existentes.

A aplicação web não será uma reescrita do projeto. Ela será uma nova interface
para o mesmo núcleo já utilizado por:

```bash
python scripts/menu.py
```

Durante toda a evolução, as duas interfaces deverão continuar disponíveis:

```bash
python scripts/menu.py  # Interface de terminal
python server.py        # Interface web local
```

## Princípios

1. Reaproveitar os scripts e funções atuais.
2. Manter compatibilidade com o menu do terminal.
3. Migrar uma funcionalidade por vez.
4. Simular antes de executar ações destrutivas.
5. Preservar campos editoriais do Notion.
6. Exibir progresso, logs e erros de forma clara.
7. Manter a aplicação restrita ao computador local.
8. Não duplicar regras entre terminal, API e navegador.

## Arquitetura de transição

```text
┌────────────────────┐       ┌────────────────────┐
│ Menu do terminal   │       │ Navegador          │
│ scripts/menu.py    │       │ HTML, CSS e JS     │
└─────────┬──────────┘       └─────────┬──────────┘
          │                            │
          │                   ┌────────▼────────┐
          │                   │ API local       │
          │                   │ server.py       │
          │                   └────────┬────────┘
          │                            │
          └──────────────┬─────────────┘
                         ▼
              ┌─────────────────────┐
              │ Funções e scripts   │
              │ existentes          │
              └──────────┬──────────┘
                         ▼
        Drive, JSON, CSV, MangaUpdates e Notion
```

No início, a API poderá executar alguns scripts como subprocessos. As ações
mais importantes serão gradualmente convertidas em chamadas diretas às
funções Python já existentes.

## Estrutura inicial

```text
Manhwateca/
├── scripts/             # Núcleo e menu atuais
├── web/
│   ├── index.html
│   ├── css/
│   │   └── app.css
│   └── js/
│       └── app.js
├── server.py            # API e servidor web local
├── config/
├── data/
├── reports/
├── docs/
└── tests/
```

Uma reorganização maior somente deverá ocorrer quando houver benefício claro.

## Milestone 1: Fundação web local

**Status:** concluído em 12 de junho de 2026.

Foi criado um servidor HTTP local usando apenas a biblioteca padrão do
Python, com a fachada `server.py`, o endpoint `GET /api/status` e os arquivos
estáticos em `web/`.

A página inicial mostra disponibilidade do catálogo, biblioteca, cache do
MangaUpdates, CSV e configuração do Notion. Nenhum token é retornado pela API
e nenhuma ação de escrita foi adicionada nesta etapa.

### Escopo

- Adicionar um servidor Python local.
- Servir HTML, CSS e JavaScript.
- Criar endpoint de status da aplicação.
- Validar `.env`, diretórios e arquivos essenciais.
- Exibir versão, catálogo atual e disponibilidade das integrações.
- Criar layout inicial inspirado em `docs/guia_menu.html`.

### Entregáveis

```text
GET /api/status
GET /
```

### Critérios de aceite

- A aplicação abre em `http://127.0.0.1:8000`.
- O menu do terminal continua funcionando.
- Nenhuma ação altera Drive ou Notion.
- A tela informa se catálogo, MangaUpdates e Notion estão disponíveis.

## Milestone 2: Execução e acompanhamento de tarefas

**Status:** concluído em 12 de junho de 2026.

Foi criada uma camada de tarefas em segundo plano com histórico persistido em
`reports/logs/web_tasks.json`, captura de saída, código de retorno, horários e
relatórios relacionados.

Nesta etapa a web expõe somente ações seguras: previews, auditoria,
catalogação e testes. Tarefas do mesmo grupo não podem rodar ao mesmo tempo.
As operações destrutivas continuam reservadas para os próximos milestones.

### Escopo

- Criar uma camada única para executar tarefas.
- Capturar saída, erros, duração e código de retorno.
- Impedir duas operações incompatíveis simultaneamente.
- Exibir progresso no navegador.
- Registrar histórico local das execuções.
- Permitir abrir os relatórios gerados.

### Modelo de tarefa

```json
{
  "id": "task-id",
  "action": "catalog_scan",
  "status": "running",
  "started_at": "2026-06-12T10:00:00",
  "finished_at": null,
  "messages": []
}
```

### Critérios de aceite

- A interface não congela durante tarefas demoradas.
- Erros aparecem com mensagem compreensível.
- O usuário consegue consultar o histórico recente.
- A mesma ação não pode ser iniciada duas vezes simultaneamente.

## Milestone 3: Organização local

**Status:** concluído em 12 de junho de 2026.

A interface web agora oferece previews, auditoria, testes, registro de
observações e aplicação da organização ou padronização. As ações mutáveis
exigem a confirmação textual exata `APLICAR` antes de entrarem na fila.

Os comandos continuam usando os mesmos serviços e bloqueios do terminal:
conflitos, duplicidades e erros mantêm o código de saída e aparecem no
histórico da tarefa.

### Funcionalidades

- Gerar previews de organização e renomeação.
- Abrir relatórios HTML no navegador.
- Registrar observações de revisão.
- Aplicar padronização dos arquivos.
- Aplicar organização alfabética.
- Executar testes relacionados.

### Reaproveitamento

```text
scripts/organize.py
scripts/rename_files.py
reports/audits/
reports/reviews/
```

### Segurança

- Ações de aplicação exigem confirmação.
- Conflitos e duplicidades bloqueiam a execução.
- A interface mostra o comando e o impacto esperado.

### Critérios de aceite

- Todas as opções atuais de organização estão disponíveis na web.
- Preview e aplicação permanecem separados.
- O resultado da tarefa pode ser revisado sem abrir o terminal.

## Milestone 4: Catalogação da biblioteca

**Status:** concluído em 12 de junho de 2026.

A aplicação agora expõe `GET /api/catalog` e apresenta uma tabela pesquisável
com progresso, capítulos, tamanho, side stories e alertas de cada obra. A
varredura compara o catálogo anterior com o novo e persiste somente o resumo
de obras novas, alteradas ou removidas no histórico da tarefa.

O snapshot usado na comparação permanece apenas em memória durante a
execução; caminhos locais e dados internos não são enviados pela API.

### Funcionalidades

- Executar a varredura completa do Drive.
- Atualizar `data/mangas.json`.
- Mostrar resumo das 128 obras ou do total atual.
- Exibir:
  - último lido;
  - próximo a ler;
  - último capítulo disponível;
  - tamanho;
  - capítulos encontrados;
  - side stories;
  - problemas de contagem.
- Destacar obras novas ou alteradas desde a última varredura.

### Reaproveitamento

```text
scripts/scan.py
scripts/utils.py
data/mangas.json
scripts/chapter_audit.py
```

### Critérios de aceite

- O resultado web corresponde ao resultado do terminal.
- A classificação usa o último capítulo, não a quantidade de PDFs.
- O progresso segue a regra do primeiro capítulo disponível.

## Milestone 5: MangaUpdates e revisão de IDs

**Status:** concluído em 12 de junho de 2026.

A interface web agora executa busca por letras, atualização de candidatos,
consulta de detalhes e geração do CSV como tarefas em segundo plano. A área
de revisão mostra somente candidatos com score acima de 0,70 e exclui
candidatos explicitamente identificados como não BL.

As decisões podem ser aplicadas diretamente pelo candidato ou por um ID
manual. O serviço valida a correspondência, cria backup e atualiza
`reports/integrations/buscaIds.json`, preservando o fluxo do terminal.

### Funcionalidades

- Buscar IDs por letras iniciais.
- Atualizar candidatos incompletos.
- Exibir candidatos com score acima do limite.
- Filtrar candidatos BL.
- Selecionar um candidato.
- Informar um ID manual.
- Aplicar decisões diretamente, sem exportar e importar JSON.
- Consultar detalhes dos IDs confirmados.
- Atualizar o CSV.

### Reaproveitamento

```text
scripts/mangaupdates.py
scripts/id_review.py
reports/integrations/buscaIds.json
data/mangaupdates.json
reports/integrations/manhwateca_import.csv
```

### Evolução principal

O fluxo web deverá substituir:

```text
Selecionar → Exportar JSON → Informar caminho → Importar JSON
```

por:

```text
Selecionar → Revisar resumo → Aplicar decisões
```

O arquivo JSON continuará sendo atualizado internamente para preservar
compatibilidade com o terminal.

### Critérios de aceite

- Obras já confirmadas não reaparecem como pendentes.
- Nomes oficiais, locais e aliases são tratados como a mesma obra.
- IDs manuais são validados.
- A consulta respeita delay, lotes e cache.

## Milestone 6: Sincronização do catálogo com o Notion

**Status:** concluído em 12 de junho de 2026.

A aplicação web agora oferece simulação do próximo lote, importação de até 25
obras e atualização das páginas existentes. As duas ações de escrita exigem
a confirmação textual `APLICAR`; a simulação permanece somente leitura.

O painel usa `reports/integrations/notion_import_status.json` para mostrar o
total do catálogo, obras importadas, último lote, pendências e duplicidades.
As propriedades continuam sendo construídas pelo serviço compartilhado, que
não envia campos editoriais vazios e não cria páginas durante uma atualização
das obras existentes.

### Funcionalidades

- Simular o próximo lote.
- Mostrar páginas existentes, novas, ausentes e duplicadas.
- Criar páginas em lotes.
- Atualizar páginas já importadas.
- Atualizar capítulos novos.
- Preservar campos editoriais.
- Mostrar comparação antes e depois.

### Reaproveitamento

```text
scripts/sync.py
reports/integrations/notion_import_status.json
```

### Campos protegidos

- Alias
- Status
- Nota
- Interesse
- Picância
- Último lido quando não houver valor inferido

### Critérios de aceite

- A simulação não altera o Notion.
- A aplicação exige confirmação explícita.
- Páginas existentes não são duplicadas.
- Campos vazios no catálogo não apagam valores editoriais.

## Milestone 7: Atualização de metadados no Notion

**Status:** concluído em 12 de junho de 2026.

A interface web agora executa a simulação e a aplicação de
`manhwateca_import.csv`. A simulação grava um resumo estruturado em
`reports/integrations/notion_csv_status.json`, com páginas atualizáveis,
nomes das propriedades enviadas, ausentes e duplicadas.

Nenhuma página é criada por esse fluxo. A aplicação exige `APLICAR` e usa as
mesmas regras de correspondência por nome oficial, nome local e alias. Campos
opcionais vazios continuam fora da requisição, preservando dados editoriais
já preenchidos no Notion.

### Funcionalidades

- Ler `manhwateca_import.csv`.
- Simular atualizações.
- Atualizar páginas por nome oficial, nome local ou alias.
- Exibir propriedades que serão alteradas.
- Atualizar:
  - ID da obra;
  - MangaUpdates;
  - temática;
  - formato;
  - universo;
  - tamanho;
  - capítulos;
  - último lido;
  - interesse;
  - picância.

### Reaproveitamento

```text
scripts/notion_csv.py
config/catalog_metadata.json
```

### Critérios de aceite

- Nenhuma página é criada nessa etapa.
- Ausentes e duplicados são exibidos antes da aplicação.
- O esquema do Notion é validado antes da atualização.

## Milestone 8: Dashboard editorial

**Status:** concluído em 12 de junho de 2026.

O dashboard editorial reúne busca e filtros para obras em leitura, sem ID,
com metadados incompletos, capítulos disponíveis e pendências de auditoria.
Cada obra pode ser editada diretamente na página.

As alterações são gravadas de forma atômica no CSV e reaplicadas ao catálogo
atual. Alias e Interesse também atualizam `config/catalog_metadata.json`.
Durante uma nova catalogação, os campos editoriais salvos no CSV são
reincorporados ao resultado, evitando o retorno aos valores padrão.

Salvar no dashboard não altera o Notion. A sincronização permanece uma etapa
separada, com simulação e confirmação explícita.

### Visões

- Obras em leitura.
- Próximas obras.
- Obras sem ID.
- Obras com metadados incompletos.
- Obras com novos capítulos.
- Obras por tamanho.
- Obras por status, nota, interesse e picância.
- Pendências de auditoria.

### Edição

Permitir editar na aplicação:

- Status
- Nota
- Interesse
- Picância
- Último lido
- Temática
- Universo
- Alias

As alterações poderão ser salvas no CSV/configuração e depois sincronizadas
com o Notion.

### Critérios de aceite

- O usuário identifica rapidamente o próximo passo.
- Alterações editoriais não são perdidas após recatalogação.
- Filtros e busca funcionam sem recarregar a página.

## Milestone 9: Fluxo completo e automação

**Status:** concluído em 12 de junho de 2026.

A aplicação agora oferece um fluxo guiado com seleção de etapas, execução
sequencial, histórico persistido em `reports/logs/web_workflow.json` e
retomada. Etapas concluídas são preservadas; uma etapa que falhou é executada
novamente por inteiro para evitar resultados parciais.

As operações seguras rodam automaticamente. Organização, revisão de IDs e
aplicações no Notion são representadas como etapas manuais. O fluxo pausa,
explica a ação necessária e só continua quando o usuário confirma que
concluiu a revisão ou aplicação pela área específica.

### Funcionalidades

- Executar o fluxo completo pela interface.
- Permitir selecionar etapas.
- Parar quando uma etapa falhar.
- Exibir resumo consolidado.
- Retomar a partir da última etapa concluída.
- Criar notificações para ações manuais necessárias.

### Fluxo principal

```text
Previews
  → Organização
  → Catalogação
  → Busca e revisão de IDs
  → Detalhes MangaUpdates
  → Atualização do CSV
  → Sincronização do catálogo
  → Atualização de metadados
```

### Critérios de aceite

- Nenhuma etapa destrutiva é aplicada sem confirmação.
- O fluxo informa claramente onde parou.
- Operações concluídas não são repetidas sem necessidade.

## Milestone 10: Robustez e empacotamento

**Status:** concluído em 12 de junho de 2026.

A aplicação possui diagnóstico de configuração, arquivos essenciais e
permissões de escrita. Tarefas e fluxos encontrados em execução após uma
reinicialização são persistidos como interrompidos e podem ser retomados.

Edições editoriais criam backups datados do CSV, catálogo e configuração,
além do log estruturado `reports/logs/editorial_changes.jsonl`. O cliente do
MangaUpdates já aplica espera exponencial e respeita `Retry-After` para
respostas 429.

O servidor pode abrir o navegador com `python server.py --open`. No macOS, o
arquivo executável `start_manhwateca.command` oferece o mesmo atalho sem
adicionar dependências.

### Robustez

- Backups antes de alterações sensíveis.
- Logs estruturados.
- Recuperação após interrupção.
- Testes de API.
- Testes end-to-end da interface.
- Validação de permissões e conexões.
- Tratamento de rate limit do MangaUpdates e Notion.

### Empacotamento

Primeira opção:

```bash
python server.py
```

Evolução opcional:

- atalho para iniciar a aplicação;
- abertura automática do navegador;
- aplicativo macOS com Tauri;
- pacote instalável local.

Docker não é prioridade, pois pode dificultar o acesso ao Google Drive local.

## Tecnologias recomendadas

### Backend

- Python
- servidor HTTP da biblioteca padrão
- funções e scripts existentes

### Frontend inicial

- HTML
- CSS
- JavaScript
- Fetch API
- Server-Sent Events para progresso

Um framework frontend não é necessário no início. Ele só deverá ser avaliado
se a interface crescer a ponto de justificar a complexidade adicional.

## Ordem de implementação

1. Fundação web local.
2. Execução e acompanhamento de tarefas.
3. Organização local.
4. Catalogação.
5. MangaUpdates e revisão de IDs.
6. Sincronização do catálogo.
7. Atualização de metadados.
8. Dashboard editorial.
9. Fluxo completo.
10. Robustez e empacotamento.

## Definição de pronto

A migração será considerada concluída quando:

- todas as ações do menu estiverem disponíveis na aplicação web;
- o terminal continuar funcional;
- as duas interfaces utilizarem as mesmas regras;
- previews e confirmações continuarem obrigatórios;
- tarefas demoradas exibirem progresso;
- os dados do Drive, CSV e Notion permanecerem consistentes;
- a suíte automatizada cobrir os fluxos principais.

## Próximo passo recomendado

Realizar uma validação manual da primeira versão:

```text
iniciar com python server.py --open
percorrer os painéis sem aplicar alterações
executar previews e uma catalogação
revisar o diagnóstico e os históricos
```

A primeira versão produtiva prevista neste roadmap está implementada.
