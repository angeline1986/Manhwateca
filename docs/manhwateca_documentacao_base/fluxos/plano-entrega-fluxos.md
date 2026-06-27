# Plano de Entrega — Módulo Fluxos

> Objetivo: implementar o **módulo Fluxos** como motor operacional da Manhwateca. O Dashboard será consumidor dos estados, métricas, logs e histórico produzidos pelos Fluxos, não o contrário.

---

## Escopo desta fase

- Focar exclusivamente no módulo Fluxos.
- Priorizar o backend dos Fluxos antes de avançar a interface.
- Implementar os contratos documentados em `/api/flows/...`.
- Usar a documentação de Fluxos como fonte de verdade.
- Não refatorar o Dashboard.
- Não mascarar desalinhamentos do backend legado na interface.

---

## Decisões iniciais

- Fluxos é o motor operacional da aplicação.
- Dashboard depende dos Fluxos e apenas observa seus resultados.
- A primeira prioridade passa a ser o backend dos Fluxos.
- O modelo de domínio vem antes da API.
- Persistência é uma camada explícita, baseada no banco de dados existente, não em arquivos JSON.
- Integrações externas são uma camada própria.
- O legado deve ficar isolado por adapter, sem espalhar compatibilidade pelo módulo novo.
- A página Fluxos servirá para operar e validar esse motor.
- Organização, catalogação, resolução de IDs, metadados e Notion são etapas de um Workflow único.
- A API oficial `/api/flows/...` deve substituir o uso direto do backend legado `/api/workflow`.
- A implementação deve seguir a matriz oficial em `matriz-implementacao-fluxos.md`.
- Estados e ações não documentados não devem ser exibidos como comportamento oficial da página Fluxos.

---

## Ordem arquitetural

```text
Interface Fluxos
        │
        ▼
API /api/flows
        │
        ▼
Workflow Orchestrator
        │
        ├── Modelo de domínio
        ├── Serviços de etapa
        ├── Camada de integrações
        ├── Camada de persistência
        └── Adapter legado
        │
        ▼
Estados • Progresso • Logs • Métricas • Histórico
        │
        ▼
Dashboard como consumidor
```

O Dashboard não executa operações do Workflow. Ele deve consumir a API e os resultados gerados pelo módulo Fluxos.

---

## Milestones

### Milestone 0 — Inventário e trava de escopo

Status: **OK**

- [x] Confirmar que a entrega atual foca somente em Fluxos.
- [x] Confirmar que o Dashboard não será alterado nesta fase.
- [x] Ler documentação principal de Fluxos.
- [x] Mapear blocos atuais reaproveitáveis da aplicação web.
- [x] Registrar endpoints atuais usados pela página.

Critério de aceite:

- Existe clareza sobre o que será alterado e o que ficará fora da entrega.

---

### Milestone 1 — Modelo de domínio dos Fluxos

Status: **OK**

- [x] Definir entidades de domínio do Workflow.
- [x] Definir entidades de domínio das etapas.
- [x] Definir estados oficiais do Workflow.
- [x] Definir estados oficiais das etapas.
- [x] Definir modelo de progresso.
- [x] Definir modelo de resultado, alerta e erro.
- [x] Definir modelo de execução e histórico.
- [x] Garantir que o domínio não dependa de HTTP, UI ou backend legado.

Critério de aceite:

- O núcleo conceitual dos Fluxos existe em código e pode ser testado sem API, UI, integrações externas ou legado.

---

### Milestone 2 — Persistência dos Fluxos

Status: **OK**

- [x] Definir migrations para tabelas de execução do Workflow.
- [x] Definir migrations para estados das etapas.
- [x] Definir migrations para progresso.
- [x] Definir migrations para logs estruturados.
- [x] Definir migrations para histórico.
- [x] Definir migrations para métricas e resumo.
- [x] Definir repositórios usando o banco de dados existente.
- [x] Garantir escrita transacional quando houver atualização de estado e log.
- [x] Garantir que a persistência use modelos de domínio, não payloads da API.
- [x] Proibir persistência oficial dos Fluxos em JSON.

Critério de aceite:

- Estados, progresso, logs e histórico podem ser salvos e recuperados no banco de dados sem depender da interface ou do Dashboard.

---

### Milestone 3 — Camada de integrações

Status: **OK**

- [x] Definir porta de integração da biblioteca local.
- [x] Definir porta de integração do PostgreSQL.
- [x] Definir porta de integração do MangaUpdates.
- [x] Definir porta de integração do Notion.
- [x] Definir contrato de disponibilidade das integrações.
- [x] Isolar detalhes externos dos serviços de etapa.
- [x] Padronizar erros e alertas vindos de integrações.

Critério de aceite:

- O domínio e o Orchestrator consomem integrações por contratos internos, sem acoplamento direto a bibliotecas, scripts ou APIs externas.

---

### Milestone 4 — Adapter legado

Status: **OK**

- [x] Criar adapter para comandos e serviços legados existentes.
- [x] Mapear resultados legados para estados oficiais.
- [x] Mapear erros legados para erros documentados.
- [x] Mapear logs legados para logs do módulo Fluxos.
- [x] Impedir que estados legados como `manual`, `waiting_manual` e `interrupted` vazem para a API oficial.
- [x] Documentar o que ainda é legado e o que já é implementação nativa.

Critério de aceite:

- Compatibilidade com o código atual existe em uma camada isolada, sem contaminar domínio, API ou interface.

---

### Milestone 5 — Workflow Orchestrator

Status: **OK**

- [x] Implementar componente responsável por controlar a sequência oficial das cinco etapas.
- [x] Validar pré-requisitos globais antes de iniciar.
- [x] Usar a camada de persistência para registrar estado.
- [x] Usar a camada de integrações para validar dependências.
- [x] Controlar transições automáticas entre etapas.
- [x] Registrar falhas, alertas, cancelamentos e conclusão.
- [x] Garantir que a interface não dependa de passos técnicos internos.

Critério de aceite:

- O backend consegue iniciar, acompanhar e finalizar o Workflow usando apenas as cinco etapas oficiais.

---

### Milestone 6 — Serviços das etapas

Status: **OK**

- [x] Implementar serviço da etapa Organizar Biblioteca.
- [x] Implementar serviço da etapa Catalogar Obras.
- [x] Implementar serviço da etapa Resolver IDs.
- [x] Implementar serviço da etapa Atualizar Metadados.
- [x] Implementar serviço da etapa Sincronizar Notion.
- [x] Padronizar `validate`, `execute` e `finalize` para cada etapa.
- [x] Usar portas de integração em vez de chamadas diretas a scripts, arquivos ou APIs externas.

Critério de aceite:

- Cada etapa possui validações, execução e finalização próprias, respeitando critérios de início e conclusão documentados.

---

### Milestone 7 — Estado, progresso, logs e histórico

Status: **pendente**

- [ ] Persistir estados oficiais do Workflow.
- [ ] Persistir estados oficiais das etapas.
- [ ] Registrar progresso global.
- [ ] Registrar progresso por etapa.
- [ ] Registrar logs operacionais.
- [ ] Consolidar histórico de execuções.
- [ ] Produzir dados de resumo para Dashboard.

Critério de aceite:

- O módulo Fluxos produz dados suficientes para operar a página Fluxos e alimentar o Dashboard futuramente.

---

### Milestone 8 — Contratos oficiais da API de Fluxos

Status: **pendente**

- [ ] Criar `GET /api/flows/status`.
- [ ] Criar `POST /api/flows/start`.
- [ ] Criar `POST /api/flows/stages/{stage}/run`.
- [ ] Criar `POST /api/flows/cancel`.
- [ ] Criar `GET /api/flows/history`.
- [ ] Criar `GET /api/flows/integrations`.
- [ ] Padronizar respostas com `success`, `timestamp`, `data`, `errors` e `warnings`.
- [ ] Impedir que o contrato oficial exponha detalhes do adapter legado.

Critério de aceite:

- A API pública do módulo Fluxos existe conforme a documentação e pode ser testada sem a interface.

---

### Milestone 9 — Interface dos Fluxos

Status: **parcial**

- [x] Criar primeira estrutura visual baseada em `fluxos_only.html`.
- [x] Renderizar as cinco etapas documentadas.
- [x] Remover rótulos de estados não documentados da UI.
- [ ] Consumir `/api/flows/status`.
- [ ] Iniciar execução por `/api/flows/start`.
- [ ] Executar etapa individual por `/api/flows/stages/{stage}/run`.
- [ ] Cancelar execução por `/api/flows/cancel`.
- [ ] Exibir progresso, logs e resumo conforme contratos oficiais.

Critério de aceite:

- A página Fluxos opera o backend oficial sem depender diretamente do endpoint legado `/api/workflow`.

---

### Milestone 10 — Dashboard como consumidor

Status: **pendente**

- [ ] Definir payload consolidado para Dashboard.
- [ ] Consumir métricas produzidas pelos Fluxos.
- [ ] Consumir histórico produzido pelos Fluxos.
- [ ] Consumir pendências produzidas pelos Fluxos.
- [ ] Exibir próxima ação recomendada sem executar operações.

Critério de aceite:

- Dashboard observa estado, métricas e pendências; não executa o Workflow.

---

### Milestone 11 — Testes e aceite

Status: **pendente**

- [ ] Testar modelo de domínio.
- [ ] Testar persistência.
- [ ] Testar integrações por contratos internos.
- [ ] Testar adapter legado isoladamente.
- [ ] Testar contratos `/api/flows/...`.
- [ ] Testar Orchestrator.
- [ ] Testar serviços de etapa.
- [ ] Testar persistência de estados, logs e histórico.
- [ ] Testar interface Fluxos contra a API oficial.
- [ ] Atualizar este plano marcando milestones concluídas.

Critério de aceite:

- O módulo Fluxos está operável, validado e documentado.

---

## Histórico de UI já realizado

### Estrutura visual inicial da página Fluxos

Status: **OK**

- [x] Aplicar a estrutura visual baseada em `fluxos_only.html`.
- [x] Criar uma página Fluxos explícita na aplicação.
- [x] Tornar Fluxos a entrada principal da experiência operacional.
- [x] Manter Dashboard fora do escopo de alteração.
- [x] Garantir layout responsivo básico.

Critério de aceite:

- A aplicação abre em uma tela de Fluxos simples, com workflow visível e sem mistura de módulos técnicos na jornada principal.

---

### Workflow estático inicial

Status: **OK**

- [x] Renderizar as cinco etapas documentadas.
- [x] Exibir estados visuais para cada etapa.
- [x] Destacar a etapa atual.
- [x] Exibir ação principal do Workflow.
- [x] Exibir painel da etapa atual.

Etapas:

1. Organizar Biblioteca
2. Catalogar Obras
3. Resolver IDs
4. Atualizar Metadados
5. Sincronizar Notion

Critério de aceite:

- O usuário entende visualmente onde está no processo, o que já foi concluído e o que ainda está bloqueado.

---

### Integração temporária com endpoint legado

Status: **OK**

- [x] Consumir `/api/workflow`.
- [x] Exibir progresso e notificação operacional.
- [x] Atualizar estado automaticamente durante execução.
- [x] Conectar botão de iniciar ou continuar Workflow.
- [x] Exibir erros de carregamento de forma compreensível.

Critério de aceite:

- A tela reflete o estado real do Workflow atual, sem depender de dados fixos.

---

Essa integração é provisória e deve ser substituída pelos contratos `/api/flows/...`.

---

## Endpoints oficiais previstos

- `GET /api/flows/status`
- `POST /api/flows/start`
- `POST /api/flows/stages/{stage}/run`
- `POST /api/flows/cancel`
- `GET /api/flows/history`
- `GET /api/flows/integrations`

---

## Fora do escopo nesta fase

- Redesenhar o Dashboard.
- Remover definitivamente páginas ou rotas antigas.
- Criar UI de Biblioteca, Obra, Configurações ou Admin.
- Usar o Dashboard como ponto de execução do Workflow.

---

## Registro de progresso

| Data | Marco | Status | Observações |
| ---- | ----- | ------ | ----------- |
| 2026-06-26 | Plano criado | OK | Documento inicial criado antes das alterações de UI. |
| 2026-06-26 | Milestones 0 a 3 | OK | Página Fluxos criada, definida como entrada principal e conectada ao `/api/workflow`. |
| 2026-06-26 | Validação inicial | Parcial | HTML e API carregaram via servidor local. `pytest` não está instalado; `unittest` revelou falhas pré-existentes nos testes de retomada do workflow. |
| 2026-06-26 | Simplificação visual | OK | Página Fluxos reduzida aos blocos do `fluxos_only.html`: processo recomendado e detalhe da etapa atual. |
| 2026-06-26 | Notion fora do foco atual | Substituído | A documentação oficial mantém Notion como etapa 5. A UI deve exibir a etapa com estados documentados, mesmo que a implementação completa fique para fase posterior. |
| 2026-06-26 | Matriz oficial | OK | Criada `matriz-implementacao-fluxos.md` para orientar implementação sem desvios. |
| 2026-06-26 | Correção de estados | OK | Removidos rótulos não documentados da UI, como `Ação manual` e `Futuro`. |
| 2026-06-26 | Validação pós-matriz | OK | Página local carregou com HTTP 200; seção Fluxos servida não contém rótulos fora da documentação. |
| 2026-06-26 | Reordenação backend-first | OK | Plano ajustado: contratos, Orchestrator, serviços, logs/estados/progresso antes da evolução da interface e do Dashboard. |
| 2026-06-26 | Refinamento arquitetural | OK | Inseridas milestones de domínio, persistência, integrações e adapter legado antes da API/interface. |
| 2026-06-27 | Modelo de domínio | OK | Criado `manhwateca/flows/domain.py` com etapas oficiais, estados, progresso, resultados, alertas, erros e execução do Workflow. |
| 2026-06-27 | Persistência dos Fluxos | OK | Criada migration `004_flows_workflow.sql` e repositório PostgreSQL para execução, etapas, mensagens, logs e resumo. |
| 2026-06-27 | Migration aplicada | OK | Executado `.venv/bin/python -m manhwateca.database.migrate`; tabelas `flow_*` confirmadas no PostgreSQL local. |
| 2026-06-27 | Camada de integrações | OK | Criados contratos para banco, biblioteca, MangaUpdates e Notion, sem implementação concreta acoplada ao Orchestrator. |
| 2026-06-27 | Adapter legado | OK | Criado `LegacyWorkflowAdapter`; apenas ele importa `WorkflowManager` e converte estados legados para estados oficiais. |
| 2026-06-27 | Workflow Orchestrator | OK | Criado Orchestrator oficial com `start`, `run_stage`, `cancel`, `get_status` e `finish`, usando repositório, integrações e serviços de etapa injetados. |
| 2026-06-27 | Serviços das etapas | OK | Criados serviços oficiais das cinco etapas usando apenas portas de integração e modelos de domínio. |
