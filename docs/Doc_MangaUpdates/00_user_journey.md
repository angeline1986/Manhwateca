# Jornada de resolução de IDs MangaUpdates

## Objetivo

Manter a busca, a revisão e a confirmação dos IDs em uma jornada contínua. A gravação de decisões manuais exige uma ação explícita, mesmo quando a conferência do lote acontece na mesma tela.

## Fluxo

```text
Buscar candidatos
       ↓
Central de decisões
  ├─ Pendências: escolher candidato, informar ID ou marcar sem correspondência
  ├─ IDs confirmados: validar e corrigir um vínculo existente
  └─ Conferir lote: selecionar, verificar e aplicar decisões preparadas
       ↓
Atualizar metadados
       ↓
Sincronizar Notion
```

## Central de decisões

A fila de pendências e a busca de obras com ID confirmado compartilham a mesma área. A seleção de uma obra mostra seus dados e controles no painel ao lado da fila.

Na revisão de uma pendência, a usuária escolhe um candidato, informa um ID manual ou marca **Sem correspondência**. **Preparar decisão** guarda a escolha apenas na sessão de revisão e seleciona a próxima pendência. A obra preparada permanece visível no fim da fila para consulta, edição ou remoção do lote.

**Corrigir vínculo** é um caminho separado dentro da Central. A usuária busca uma obra já vinculada, informa outro ID, consulta o preview do MangaUpdates e confirma a troca. Essa correção não entra no lote de pendências. Após a troca, os metadados derivados do ID antigo precisam ser reconstruídos em **Atualizar metadados**.

## Conferência e aplicação

**Conferir lote** abre uma confirmação sobre a Central, sem navegar para outra página. A usuária pode desmarcar decisões e aplicar somente parte do lote. Pendências ainda abertas não impedem a aplicação das decisões já preparadas.

Antes de habilitar **Aplicar**, o sistema verifica o formato dos IDs, a repetição entre decisões do lote, a existência da obra local e se algum ID já pertence a outra obra no PostgreSQL. O resultado dessa conferência aparece no próprio diálogo. A existência do ID informado na API do MangaUpdates não é verificada por essa conferência; a tela deve dizer isso claramente.

A ação **Aplicar** repete a validação no servidor. Se alguma decisão for rejeitada ou o catálogo mudar entre a conferência e a gravação, a interface informa quais decisões foram efetivamente aplicadas e mantém as demais disponíveis para revisão.

## Regras de navegação

- Preparar uma decisão não grava o ID nem troca de página.
- A confirmação do lote depende de clique explícito e de uma conferência válida.
- A usuária pode voltar da confirmação à obra em análise sem perder as decisões preparadas.
- A correção de um ID confirmado possui preview e confirmação próprios.
- Atualizar metadados e Sincronizar Notion continuam como etapas posteriores.
