# Dashboard — Documentação Técnica

## 06 - Estados

---

# Objetivo

Este documento define a máquina de estados (State Machine) do Dashboard e de todos os seus componentes.

O objetivo é padronizar o comportamento da interface durante carregamento, sucesso, ausência de dados, erros e atualizações, garantindo previsibilidade, consistência visual e desacoplamento entre Backend e Frontend.

---

# Princípios

Todo componente do Dashboard deve obedecer aos seguintes princípios:

* possuir estados explícitos;
* nunca depender de inferências implícitas;
* permitir renderização independente;
* ser resiliente a falhas parciais;
* apresentar feedback visual claro ao usuário.

Cada componente deve possuir apenas um estado ativo por vez.

---

# Estados Globais da Página

O `DashboardPage` controla o estado global da tela.

```text
                DashboardPage

                     │

     ┌───────────────┼────────────────┐

     ▼               ▼                ▼

  Loading         Success          Error
                     │
                     ▼
                 Refreshing
```

---

## Loading

Estado inicial da página.

### Quando ocorre

* primeira abertura do Dashboard;
* atualização completa da página;
* recarga manual.

### Comportamento

* exibir skeletons;
* ocultar dados antigos;
* bloquear ações que dependam dos dados.

### Transições

```text
Loading

↓

Success

↓

Error
```

---

## Success

Todos os dados foram carregados corretamente.

### Comportamento

* renderizar todos os componentes;
* habilitar navegação;
* permitir atualização.

---

## Refreshing

Representa uma atualização iniciada pelo usuário.

### Objetivo

Evitar que a interface desapareça durante o refresh.

### Comportamento

* manter dados atuais visíveis;
* exibir indicador discreto de atualização;
* substituir dados apenas após sucesso.

Fluxo:

```text
Success

↓

Refreshing

↓

Success
```

Nunca retornar para Loading durante um refresh manual.

---

## Error

Falha na construção do Dashboard.

### Causas

* erro inesperado;
* indisponibilidade do backend;
* falha crítica no Aggregation Service.

### Interface

Exibir:

* mensagem amigável;
* botão **Tentar novamente**;
* detalhes apenas em logs.

---

# Máquina de Estados Global

```text
             ┌────────────┐
             │  Loading   │
             └─────┬──────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
   Success                 Error
        │                     ▲
        │                     │
        ▼                     │
 Refreshing ──────────────────┘
        │
        ▼
    Success
```

---

# Estados dos Componentes

Cada componente possui sua própria máquina de estados.

Esses estados são independentes.

Uma falha em um componente não altera o estado dos demais.

---

# Header

## Estados

```text
Loading

↓

Success

↓

Refreshing
```

Não possui estado Empty.

---

# NextActionCard

## Máquina

```text
Loading

↓

Success

↓

Empty

↓

Error
```

---

## Loading

Exibir skeleton.

---

## Success

Exibir:

* título;
* descrição;
* prioridade;
* botão.

---

## Empty

Quando nenhuma ação for necessária.

Exemplo:

```text
Sua biblioteca está totalmente atualizada.
```

---

## Error

Erro ao obter recomendação.

O restante do Dashboard permanece funcional.

---

# MetricsGrid

Estados:

```text
Loading

↓

Success
```

Nunca possui Empty.

Mesmo valores iguais a zero continuam sendo métricas válidas.

Exemplo:

```text
Novos capítulos

0
```

---

# MetricCard

Cada card possui apenas dois estados.

```text
Loading

↓

Success
```

Nunca apresentar mensagens de erro individuais.

Caso uma métrica não possa ser obtida, o Backend deverá fornecer um valor consistente.

---

# PendingActionsPanel

Estados possíveis.

```text
Loading

↓

Success

↓

Empty

↓

Error
```

---

## Empty

Exibir:

```text
Nenhuma pendência encontrada.
```

Não ocultar o painel.

---

## Error

Exibir:

```text
Não foi possível carregar as pendências.
```

Com botão:

```text
Tentar novamente
```

---

# IntegrationsPanel

Estados.

```text
Loading

↓

Success

↓

Error
```

Mesmo em caso de erro parcial, deve renderizar todas as integrações conhecidas.

Exemplo:

```text
PostgreSQL

Operacional

──────────

Notion

Erro
```

---

# WorkflowPanel

Estados.

```text
Loading

↓

Success

↓

Error
```

Nunca possui Empty.

Sempre existe um Workflow.

---

# QuickActionsPanel

Estados.

```text
Loading

↓

Success
```

Os atalhos fazem parte da estrutura fixa da aplicação.

Nunca desaparecem.

---

# Estados das Integrações

Cada integração possui estado próprio.

```text
healthy

warning

error

unknown
```

---

## healthy

Renderização:

```text
🟢
```

---

## warning

Renderização:

```text
🟡
```

---

## error

Renderização:

```text
🔴
```

---

## unknown

Utilizado quando:

* integração desabilitada;
* estado indisponível;
* primeira inicialização.

Renderização:

```text
⚪
```

---

# Estados do Workflow

Cada etapa possui estado próprio.

```text
pending

running

completed

blocked

error
```

---

## pending

Ainda não iniciada.

---

## running

Executando.

---

## completed

Finalizada.

---

## blocked

Aguardando outra etapa.

---

## error

Execução interrompida.

---

# Estados das Pendências

Cada pendência possui prioridade.

```text
high

medium

low
```

Esses valores são definidos exclusivamente pelo Backend.

O Frontend apenas altera a apresentação visual.

---

# Transições Permitidas

Workflow.

```text
pending

↓

running

↓

completed
```

ou

```text
running

↓

error
```

ou

```text
blocked

↓

running
```

Nunca permitir:

```text
completed

↓

pending
```

Sem reinicialização explícita do Workflow.

---

# Atualização de Estado

Durante um refresh.

```text
Success

↓

Refreshing

↓

Success
```

Jamais:

```text
Success

↓

Loading
```

Essa abordagem elimina flickering da interface.

---

# Estados Derivados

Alguns estados são calculados.

Exemplo.

```text
missingIds == 0

↓

NextAction

↓

Atualizar Metadados
```

O Frontend nunca realiza esse cálculo.

---

# Responsabilidade do Backend

O Backend determina:

* estado do Workflow;
* prioridade;
* próxima ação;
* estado das integrações;
* existência de pendências.

---

# Responsabilidade do Frontend

O Frontend determina apenas:

* qual componente renderizar;
* qual cor utilizar;
* qual ícone utilizar;
* qual animação apresentar.

Nunca calcula estados.

---

# Recuperação após Erros

Fluxo.

```text
Error

↓

Retry

↓

Loading

↓

Success
```

Toda tentativa deve reconstruir completamente o `DashboardViewModel`.

---

# Regras de UX

* Nunca deixar um componente "travado" em Loading.
* Nunca ocultar erros silenciosamente.
* Sempre informar ao usuário quando um componente não puder ser carregado.
* Atualizações devem preservar a estabilidade visual.
* Componentes independentes nunca devem compartilhar estados internos.

---

# Checklist

Cada componente deve implementar:

| Estado     | Obrigatório          |
| ---------- | -------------------- |
| Loading    | ✅                    |
| Success    | ✅                    |
| Empty      | Quando aplicável     |
| Error      | Quando aplicável     |
| Refreshing | Apenas DashboardPage |

---

# Relação com outros documentos

| Documento                 | Conteúdo relacionado                   |
| ------------------------- | -------------------------------------- |
| 03-api-dashboard.md       | Origem dos estados no contrato JSON    |
| 05-componentes.md         | Componentes afetados por cada estado   |
| 08-atualizacao.md         | Fluxo de atualização e revalidação     |
| 09-tratamento-de-erros.md | Estratégias de recuperação após falhas |

---

# Conclusão

A máquina de estados do Dashboard garante previsibilidade, isolamento entre componentes e uma experiência consistente durante carregamentos, atualizações e falhas. A separação entre estados calculados pelo Backend e estados visuais controlados pelo Frontend reduz o acoplamento da interface, simplifica testes automatizados e facilita futuras evoluções da aplicação.
