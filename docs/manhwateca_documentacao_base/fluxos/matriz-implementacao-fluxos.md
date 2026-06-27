# Matriz de Implementação — Fluxos

> Fonte de verdade: documentação em `docs/manhwateca_documentacao_base/fluxos`.

Este documento consolida as regras que a implementação da página **Fluxos** deve seguir. Ele não introduz comportamento novo; apenas organiza o que já está especificado na documentação funcional, técnica e de usuário.

---

## Princípios obrigatórios

- A sequência lógica do Workflow é fixa.
- A interface não pode permitir reordenar etapas.
- O Workflow deve executar automaticamente a transição entre etapas concluídas.
- Não deve existir intervenção manual entre etapas durante a execução automática.
- A interface deve usar somente estados documentados.
- Mensagens técnicas, stack traces e códigos internos não devem aparecer para o usuário final.
- O front-end deve conversar com o backend por contratos públicos do módulo Fluxos.

---

## Etapas oficiais

| Ordem | Etapa | Dependência | Finalidade | Próxima etapa |
| ----: | ----- | ----------- | ---------- | ------------- |
| 1 | Organizar Biblioteca | Nenhuma | Preparar a biblioteca para processamento | Catalogar Obras |
| 2 | Catalogar Obras | Organização concluída | Transformar diretórios válidos em registros persistidos | Resolver IDs |
| 3 | Resolver IDs | Obras catalogadas | Associar obras ao identificador oficial do MangaUpdates | Atualizar Metadados |
| 4 | Atualizar Metadados | IDs resolvidos | Atualizar informações oficiais das obras | Sincronizar Notion |
| 5 | Sincronizar Notion | Metadados atualizados | Refletir alterações no Notion | Finalizar Workflow |

---

## Ações por etapa

### 1. Organizar Biblioteca

- localizar diretórios;
- validar estrutura;
- identificar novas obras;
- atualizar índice interno;
- registrar inconsistências.

Critérios para início:

- biblioteca configurada;
- diretório acessível.

Critérios para conclusão:

- varredura finalizada;
- índice atualizado;
- inconsistências registradas.

---

### 2. Catalogar Obras

- criar novos registros;
- atualizar registros existentes;
- validar dados mínimos;
- identificar duplicidades.

Critérios para início:

- organização concluída.

Critérios para conclusão:

- todas as obras catalogadas;
- registros atualizados;
- pendências identificadas.

---

### 3. Resolver IDs

- pesquisar candidatos;
- validar correspondências;
- confirmar associações;
- registrar obras não localizadas.

Critérios para início:

- obra catalogada.

Critérios para conclusão:

- todos os IDs possíveis resolvidos;
- pendências registradas.

---

### 4. Atualizar Metadados

- consultar MangaUpdates;
- atualizar títulos;
- atualizar autores;
- atualizar gêneros;
- atualizar status;
- atualizar capítulos;
- registrar data da sincronização.

Critérios para início:

- obra com `mangaupdates_id`.

Critérios para conclusão:

- metadados atualizados;
- histórico registrado.

---

### 5. Sincronizar Notion

- criar páginas;
- atualizar páginas existentes;
- sincronizar propriedades;
- registrar falhas;
- consolidar resultados.

Critérios para início:

- metadados atualizados.

Critérios para conclusão:

- sincronização encerrada;
- resumo disponível.

---

## Estados oficiais do Workflow

| Estado técnico | Rótulo na interface |
| -------------- | ------------------- |
| `idle` | Não iniciado |
| `validating` | Preparando |
| `running` | Em execução |
| `cancelling` | Cancelando |
| `cancelled` | Cancelado |
| `completed` | Concluído |
| `completed_with_warnings` | Concluído com alertas |
| `failed` | Falhou |

---

## Estados oficiais das etapas

| Estado técnico | Rótulo na interface |
| -------------- | ------------------- |
| `waiting` | Aguardando |
| `validating` | Validando |
| `running` | Processando |
| `completed` | Concluída |
| `completed_with_warnings` | Concluída com alertas |
| `skipped` | Ignorada |
| `failed` | Falhou |
| `cancelled` | Cancelada |

Estados não documentados, como `manual`, `future`, `blocked` ou `interrupted`, não devem aparecer na interface final de Fluxos.

---

## Endpoints oficiais

| Método | Endpoint | Finalidade |
| ------ | -------- | ---------- |
| GET | `/api/flows/status` | Consulta o estado atual do Workflow |
| POST | `/api/flows/start` | Inicia o Workflow completo |
| POST | `/api/flows/stages/{stage}/run` | Executa uma etapa específica |
| POST | `/api/flows/cancel` | Solicita cancelamento |
| GET | `/api/flows/history` | Consulta histórico |
| GET | `/api/flows/integrations` | Consulta estado das integrações |

Modelo de resposta:

```json
{
  "success": true,
  "timestamp": "2026-06-27T01:35:00Z",
  "data": {},
  "errors": [],
  "warnings": []
}
```

---

## Regiões obrigatórias da página

- Cabeçalho;
- Barra de Progresso Global;
- Workflow;
- Painel de Execução;
- Resumo da Execução.

O layout visual pode ser simplificado, mas essas responsabilidades precisam estar representadas.

---

## Desalinhamentos atuais conhecidos

- O backend legado expõe `/api/workflow`, não os endpoints oficiais `/api/flows/...`.
- O backend legado usa passos internos em quantidade diferente das 5 etapas oficiais.
- O backend legado pode retornar estados não documentados, como `manual`, `waiting_manual` e `interrupted`.
- A página atual ainda usa um adaptador temporário para exibir dados legados na estrutura visual de Fluxos.

Esses desalinhamentos devem ser tratados explicitamente em implementação posterior, não mascarados com novos estados inventados na interface.
