
# 00 — User Journey — Fluxo Operacional da Manhwateca

> Este documento define a jornada do usuário entre as etapas do fluxo MangaUpdates.
>
> **Produto, Design e Engenharia descrevem cada tela.**
>
> **Este documento descreve quando cada tela começa, termina e como ocorre a navegação entre elas.**

---

# 1. Objetivo

Garantir que todo o fluxo operacional seja percebido como uma única jornada guiada, evitando mudanças abruptas de contexto.

Princípios:

- Cada etapa possui um objetivo único.
- O usuário conclui uma etapa antes de iniciar outra.
- O sistema nunca muda de contexto sem motivo claro.
- A navegação deve preservar a continuidade da tarefa.

---

# 2. Fluxo Geral

```text
Buscar candidatos
      ↓
Revisar pendências
      ↓
Revisão concluída
      ↓
Aplicar decisões
      ↓
Atualizar metadados
      ↓
Sincronizar Notion
      ↓
Concluído
```

Cada etapa representa um lote de trabalho, nunca um único item.

---

# 3. Máquina de Estados da Jornada

```text
SEARCHING
   ↓
REVIEWING
   ↓
REVIEW_COMPLETED
   ↓
APPLYING
   ↓
UPDATING_METADATA
   ↓
SYNCING_NOTION
   ↓
FINISHED
```

O estado global só muda quando os critérios da etapa atual forem atendidos.

---

# 4. Regras de Navegação

## Buscar candidatos

Entrada:
- Usuário inicia o fluxo.

Saída:
- Busca concluída.

Próximo estado:
- Revisar pendências.

---

## Revisar pendências

Objetivo:

Resolver todas as pendências uma por uma.

Ao clicar em **Salvar decisão**:

- salvar decisão;
- atualizar indicadores;
- remover (ou marcar) o item da fila;
- selecionar automaticamente a próxima pendência;
- permanecer na mesma tela.

### É proibido

- navegar automaticamente para "Aplicar decisões";
- interromper a revisão para mudar de etapa.

Enquanto existir qualquer pendência:

```text
Estado = REVIEWING
```

---

## Quando a fila termina

Critério:

- não existem mais pendências revisáveis.

O sistema apresenta uma tela de conclusão.

Mensagem sugerida:

> Revisão concluída.
>
> Todas as pendências foram resolvidas.

Ações disponíveis:

- Revisar novamente;
- Aplicar decisões.

Somente após ação explícita do usuário ocorre a navegação.

---

## Aplicar decisões

Objetivo:

Confirmar a gravação das decisões.

O usuário não revisa candidatos nesta etapa.

A tela existe apenas para confirmar o lote.

---

## Atualizar metadados

Executado após aplicação concluída.

Não retorna para etapas anteriores automaticamente.

---

## Sincronizar Notion

Última etapa do fluxo.

Ao concluir:

Estado = FINISHED.

---

# 5. Transições Permitidas

| Origem | Destino | Automática | Usuário |
|--------|---------|------------|----------|
| Buscar candidatos | Revisar pendências | Sim | Não |
| Revisar pendências | Revisar pendências | Sim (próximo item) | Não |
| Revisão concluída | Aplicar decisões | Não | Sim |
| Aplicar decisões | Atualizar metadados | Sim (após sucesso) | Não |
| Atualizar metadados | Sincronizar Notion | Sim | Não |
| Sincronizar Notion | Concluído | Sim | Não |

---

# 6. Regras Globais

- Nunca navegar automaticamente entre etapas de revisão e confirmação.
- Toda mudança de contexto deve ser perceptível.
- Cada tela deve possuir apenas um objetivo cognitivo.
- A fila de revisão representa trabalho, não navegação.

---

# 7. Critérios de UX

O usuário deve sentir:

Buscar candidatos:
> "Vamos localizar correspondências."

Revisar pendências:
> "Estou resolvendo uma pendência por vez."

Aplicar decisões:
> "Está tudo pronto para gravar."

Atualizar metadados:
> "O catálogo está sendo enriquecido."

Sincronizar Notion:
> "Os dados estão sendo publicados."

---

# 8. Critérios de Aceite

- [ ] Nenhuma etapa mistura responsabilidades.
- [ ] Revisar pendências permanece ativa até a fila terminar.
- [ ] Salvar decisão nunca muda de etapa.
- [ ] Aplicar decisões só inicia mediante ação explícita do usuário.
- [ ] Todas as transições seguem a máquina de estados.
- [ ] O fluxo completo transmite continuidade e não quebra o contexto do usuário.
