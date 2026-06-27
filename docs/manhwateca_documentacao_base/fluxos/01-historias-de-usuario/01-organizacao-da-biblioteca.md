# Organização da Biblioteca

> Documento: **01-organizacao-da-biblioteca.md**

---

# Objetivo

Esta etapa do Workflow é responsável por preparar a biblioteca para todo o processamento posterior.

Seu objetivo é garantir que todos os arquivos estejam organizados, padronizados e prontos para serem catalogados pelo sistema, reduzindo inconsistências antes das etapas de identificação, obtenção de metadados e sincronização.

Esta é a única etapa obrigatória para iniciar um Workflow completo.

---

# Escopo

Esta etapa contempla:

* varredura da biblioteca;
* identificação de novos diretórios;
* validação da estrutura de pastas;
* detecção de arquivos inválidos;
* normalização da organização física;
* atualização do índice interno da biblioteca.

Não contempla:

* identificação da obra;
* busca de IDs externos;
* atualização de metadados;
* sincronização com o Notion.

---

# US-001 — Organizar automaticamente a biblioteca

## História

**Como** usuário da Manhwateca

**Quero** que o sistema organize automaticamente minha biblioteca

**Para que** todas as próximas etapas do Workflow utilizem uma estrutura consistente e livre de inconsistências.

---

## Critérios de Aceite

* O sistema deve localizar todas as obras presentes na biblioteca configurada.
* Apenas diretórios válidos devem ser considerados.
* Arquivos que não pertençam a nenhuma obra devem ser ignorados ou sinalizados.
* O índice interno da biblioteca deve ser atualizado ao final da execução.
* O usuário deve visualizar o progresso da organização.

---

## Regras de Negócio

RN-001

A biblioteca somente poderá ser organizada quando existir um diretório configurado.

RN-002

A organização nunca deverá alterar o conteúdo dos arquivos das obras.

RN-003

A etapa deve ser idempotente.

Executá-la múltiplas vezes deve produzir exatamente o mesmo resultado quando não houver alterações na biblioteca.

RN-004

Todas as inconsistências encontradas deverão ser registradas para análise posterior.

---

# US-002 — Detectar novas obras

## História

**Como** usuário

**Quero** que novas obras adicionadas à biblioteca sejam detectadas automaticamente

**Para que** elas possam participar do Workflow sem necessidade de cadastro manual.

---

## Critérios de Aceite

* Detectar diretórios inexistentes no banco.
* Registrar novas obras.
* Não criar registros duplicados.
* Informar quantidade de novas obras encontradas.

---

## Regras de Negócio

RN-005

Uma obra é considerada nova quando não existir registro correspondente no banco de dados.

RN-006

A comparação deve utilizar o caminho físico da obra.

---

# US-003 — Identificar alterações na biblioteca

## História

**Como** usuário

**Quero** que o sistema identifique alterações realizadas na biblioteca

**Para que** o índice interno permaneça sincronizado com os arquivos existentes.

---

## Critérios de Aceite

* Detectar novas pastas.
* Detectar pastas removidas.
* Detectar renomeações quando possível.
* Atualizar o estado da biblioteca.

---

## Regras de Negócio

RN-007

A exclusão física de uma pasta nunca deverá remover automaticamente o registro da obra.

A obra deverá permanecer marcada como "não localizada" até confirmação do usuário.

---

# US-004 — Validar a estrutura da biblioteca

## História

**Como** usuário

**Quero** que o sistema valide a estrutura física da biblioteca

**Para que** problemas sejam identificados antes da catalogação.

---

## Critérios de Aceite

O sistema deverá identificar:

* diretórios vazios;
* nomes inválidos;
* arquivos órfãos;
* estruturas inesperadas;
* duplicidades aparentes.

---

## Regras de Negócio

RN-008

A validação nunca interrompe o Workflow.

As inconsistências devem gerar alertas.

---

# US-005 — Atualizar o índice interno

## História

**Como** sistema

**Quero** manter um índice atualizado da biblioteca

**Para que** as etapas seguintes consultem apenas informações previamente consolidadas.

---

## Critérios de Aceite

* Atualizar registros existentes.
* Inserir novos registros.
* Marcar obras ausentes.
* Registrar data da última organização.

---

## Regras de Negócio

RN-009

O índice interno representa o estado conhecido da biblioteca no momento da última organização.

---

# Fluxo Principal

```text
Usuário inicia "Organizar Biblioteca"

↓

Sistema valida configuração da biblioteca

↓

Varredura completa dos diretórios

↓

Detecta novas obras

↓

Atualiza índice interno

↓

Valida inconsistências

↓

Registra alertas

↓

Etapa concluída
```

---

# Fluxos Alternativos

## Biblioteca vazia

Resultado esperado:

* nenhuma obra encontrada;
* índice atualizado;
* Workflow permanece disponível.

---

## Biblioteca inacessível

Resultado esperado:

* etapa interrompida;
* erro registrado;
* usuário informado.

---

## Diretórios inválidos

Resultado esperado:

* registrar alerta;
* continuar processamento das demais obras.

---

# Exceções

| Código   | Situação                               |
| -------- | -------------------------------------- |
| FLUX-001 | Biblioteca não configurada             |
| FLUX-002 | Diretório inexistente                  |
| FLUX-003 | Permissão insuficiente                 |
| FLUX-004 | Erro de leitura do sistema de arquivos |

---

# Dependências

Esta etapa depende de:

* configuração da biblioteca;
* acesso ao sistema de arquivos;
* PostgreSQL disponível.

Não depende de:

* MangaUpdates;
* Notion.

---

# Impactos nos demais módulos

Após a conclusão desta etapa:

* a Catalogação poderá ser executada;
* o Dashboard atualizará métricas da biblioteca;
* novas obras poderão aparecer na Biblioteca;
* o Workflow avançará para a etapa de Catalogação.

---

# Prioridade

**Alta**

A organização da biblioteca é pré-requisito para todas as demais etapas do Workflow operacional.

---

# Rastreabilidade

| Próximo documento       | Relação                    |
| ----------------------- | -------------------------- |
| Especificação Funcional | 03-etapas-do-workflow.md   |
| Documentação Técnica    | 04-processamento.md        |
| Manual do Usuário       | 03-organizar-biblioteca.md |

---

# Conclusão

A etapa **Organização da Biblioteca** estabelece a base operacional para todo o Workflow da Manhwateca. Ao consolidar o estado físico da biblioteca, detectar novas obras e validar inconsistências estruturais, ela garante que as etapas seguintes operem sobre uma visão consistente e confiável dos arquivos disponíveis.
