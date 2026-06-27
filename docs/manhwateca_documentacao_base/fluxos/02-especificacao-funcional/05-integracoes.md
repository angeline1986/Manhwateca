# Integrações

> Documento: **05-integracoes.md**

---

# Objetivo

Este documento especifica o comportamento funcional das integrações utilizadas pela página **Fluxos**.

O módulo Fluxos depende de serviços internos e externos para executar suas cinco etapas operacionais. Cada integração possui responsabilidades específicas, estados próprios e comportamentos esperados em situações normais ou de falha.

O objetivo desta especificação é definir **como a interface deve reagir** às diferentes condições dessas integrações, sem detalhar aspectos de implementação técnica.

---

# Visão Geral

A página Fluxos utiliza quatro fontes principais de dados.

```text
                 Fluxos
                    │
    ┌───────────────┼────────────────┐
    ▼               ▼                ▼
 PostgreSQL   MangaUpdates API    Notion API
                    │
                    ▼
            Google Drive (Biblioteca)
```

Cada integração participa de uma ou mais etapas do Workflow.

---

# Matriz de Dependências

| Integração                | Organizar | Catalogar | Resolver IDs | Metadados | Notion |
| ------------------------- | :-------: | :-------: | :----------: | :-------: | :----: |
| Biblioteca (Google Drive) |     ✅     |     ✅     |       —      |     —     |    —   |
| PostgreSQL                |     ✅     |     ✅     |       ✅      |     ✅     |    ✅   |
| MangaUpdates              |     —     |     —     |       ✅      |     ✅     |    —   |
| Notion                    |     —     |     —     |       —      |     —     |    ✅   |

---

# PostgreSQL

## Finalidade

O PostgreSQL é a fonte oficial de dados da Manhwateca.

Toda informação utilizada pelo Workflow deve ser lida ou persistida no banco de dados.

---

## Comportamento esperado

Durante a execução, a interface deve considerar o banco:

* disponível;
* indisponível;
* reconectando.

---

## Quando indisponível

O Workflow não poderá ser iniciado.

A interface deverá:

* impedir novas execuções;
* exibir mensagem clara;
* manter o histórico da última execução visível.

Exemplo:

```text
PostgreSQL indisponível.

Verifique a conexão antes de iniciar o Workflow.
```

---

# Biblioteca (Google Drive)

## Finalidade

Representa a estrutura física das obras.

É utilizada nas etapas:

* Organizar Biblioteca;
* Catalogação.

---

## Comportamento esperado

O sistema deve validar:

* diretório configurado;
* acesso permitido;
* leitura dos diretórios.

---

## Biblioteca inacessível

Caso a biblioteca não possa ser acessada:

* impedir a etapa Organização;
* interromper o Workflow antes da execução;
* informar o motivo ao usuário.

---

# MangaUpdates

## Finalidade

Fornecer informações oficiais das obras.

É utilizado em:

* Resolução de IDs;
* Atualização de Metadados.

---

## Estados esperados

A interface deve reconhecer:

| Estado       | Significado              |
| ------------ | ------------------------ |
| Disponível   | API operacional          |
| Indisponível | Sem comunicação          |
| Limitada     | Rate limit ou degradação |
| Desconhecida | Estado não determinado   |

---

## API indisponível

Caso a API esteja indisponível:

* finalizar apenas a etapa afetada;
* registrar alerta;
* permitir nova tentativa posteriormente.

O restante do Workflow não deve ser invalidado.

---

## Limite de requisições

Quando identificado limite de requisições:

A interface deve informar:

* processamento pausado;
* possibilidade de retomar posteriormente.

Não deve apresentar erro fatal.

---

# Notion

## Finalidade

Representar externamente a biblioteca da Manhwateca.

Utilizado exclusivamente na quinta etapa.

---

## Comportamento esperado

O sistema deve:

* localizar páginas existentes;
* criar novas páginas;
* atualizar páginas alteradas.

---

## Banco inexistente

Caso o banco configurado não exista:

* interromper apenas a etapa de sincronização;
* manter as etapas anteriores concluídas.

---

## Página removida

Caso uma página tenha sido removida manualmente:

O sistema deve:

* marcar o registro para recriação;
* informar o ocorrido;
* permitir nova sincronização.

---

# Independência das Integrações

Cada integração deve funcionar de forma independente.

Exemplo:

```text
Biblioteca      OK

PostgreSQL      OK

MangaUpdates    Erro

Notion          OK
```

Nesse cenário:

* Organização executa normalmente.
* Catalogação executa normalmente.
* Resolução de IDs falha.
* Atualização de Metadados não é iniciada.
* Sincronização com Notion não ocorre por depender da etapa anterior.

---

# Atualização dos Estados

A interface deve atualizar automaticamente o estado das integrações:

* antes do início do Workflow;
* durante o processamento;
* após a conclusão.

Mudanças de estado devem ocorrer sem necessidade de recarregar a página.

---

# Feedback Visual

Cada integração deve possuir indicação clara do seu estado.

Exemplo:

| Estado      | Exemplo        |
| ----------- | -------------- |
| Operacional | ✓ PostgreSQL   |
| Atenção     | ⚠ MangaUpdates |
| Erro        | ✕ Notion       |
| Verificando | ⟳ Biblioteca   |

A informação textual é obrigatória e não deve depender apenas de ícones ou cores.

---

# Resiliência

O comportamento esperado diante de falhas é:

| Situação                  | Resultado                           |
| ------------------------- | ----------------------------------- |
| Falha em uma obra         | Continuar processando as demais     |
| Falha em uma integração   | Afetar apenas as etapas dependentes |
| Recuperação da integração | Permitir reprocessamento            |
| Erro temporário           | Registrar e permitir nova tentativa |

---

# Resumo da Execução

Ao final do Workflow, o sistema deve informar:

* integrações utilizadas;
* integrações indisponíveis;
* operações concluídas;
* operações não executadas devido a dependências.

Essas informações auxiliam o usuário na identificação de problemas sem necessidade de consultar logs técnicos.

---

# Relação com outros documentos

| Documento                                 | Conteúdo relacionado                  |
| ----------------------------------------- | ------------------------------------- |
| 03-etapas-do-workflow.md                  | Dependência entre etapas              |
| 04-processamento-e-validacoes.md          | Validações antes da execução          |
| 06-estados-e-mensagens.md                 | Estados e mensagens exibidas          |
| 03-documentacao-tecnica/05-integracoes.md | Implementação técnica das integrações |

---

# Conclusão

As integrações da página **Fluxos** sustentam todo o processo operacional da Manhwateca. A interface deve tratar cada serviço como um componente independente, informando claramente seu estado e limitando o impacto de falhas apenas às etapas que realmente dependem daquela integração. Essa abordagem aumenta a previsibilidade do Workflow, facilita a identificação de problemas e melhora significativamente a experiência do usuário durante o processamento.
