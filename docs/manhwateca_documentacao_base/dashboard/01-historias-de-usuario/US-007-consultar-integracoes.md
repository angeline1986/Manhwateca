# US-007 — Consultar o estado das integrações

## Identificação

| Campo            | Valor                                        |
| ---------------- | -------------------------------------------- |
| **ID**           | US-007                                       |
| **Título**       | Consultar o estado das integrações           |
| **Módulo**       | Dashboard                                    |
| **Prioridade**   | Alta                                         |
| **Tipo**         | Funcionalidade                               |
| **Epic**         | Dashboard                                    |
| **Dependências** | PostgreSQL, Biblioteca, MangaUpdates, Notion |

---

# Objetivo

Como **usuária da Manhwateca**,

quero **visualizar rapidamente se todas as integrações necessárias para o funcionamento do sistema estão disponíveis**,

para que **eu consiga identificar problemas de ambiente antes de iniciar qualquer operação do workflow**.

---

# Descrição

O Dashboard deve apresentar um painel resumido com a situação das principais integrações utilizadas pela Manhwateca.

Esse painel tem caráter exclusivamente informativo e serve para indicar se o ambiente está preparado para execução das funcionalidades da aplicação.

O Dashboard não deve executar testes profundos nem permitir configuração das integrações.

Toda configuração e diagnóstico detalhado pertencem ao módulo **Configurações**.

---

# Valor de Negócio

Grande parte das falhas operacionais ocorre devido a problemas de infraestrutura, como:

* PostgreSQL indisponível;
* biblioteca inacessível;
* credenciais inválidas;
* APIs indisponíveis.

Ao apresentar essas informações logo na abertura da aplicação, o sistema reduz tentativas de execução que inevitavelmente falhariam e orienta o usuário para resolver primeiro os problemas de ambiente.

---

# Fluxo Principal

1. O usuário acessa o Dashboard.
2. O sistema consulta o estado das integrações.
3. O Dashboard apresenta um resumo do ambiente.
4. O usuário verifica se existe alguma integração indisponível.
5. Caso exista algum problema, o usuário acessa **Configurações** para solucioná-lo.

---

# Fluxos Alternativos

### FA-01 — Todas as integrações disponíveis

O Dashboard deve apresentar todas as integrações como saudáveis.

Exemplo:

```text
✓ PostgreSQL

✓ Biblioteca

✓ MangaUpdates

✓ Notion
```

---

### FA-02 — Integração indisponível

Caso uma integração esteja indisponível, ela deve permanecer visível, porém destacada como indisponível.

Exemplo:

```text
✖ PostgreSQL

Não foi possível estabelecer conexão.
```

---

### FA-03 — Integração parcialmente funcional

Quando um serviço estiver acessível, porém apresentar restrições, o Dashboard deve indicar estado de atenção.

Exemplo:

```text
⚠ MangaUpdates

A API respondeu lentamente.
```

---

# Critérios de Aceite

| ID     | Critério                                                                             |
| ------ | ------------------------------------------------------------------------------------ |
| AC-001 | O Dashboard deve apresentar o estado resumido das integrações.                       |
| AC-002 | Cada integração deve possuir um indicador visual de status.                          |
| AC-003 | Problemas em uma integração não devem impedir a exibição das demais.                 |
| AC-004 | O Dashboard não deve permitir configuração das integrações.                          |
| AC-005 | O usuário deve conseguir acessar Configurações para investigar problemas.            |
| AC-006 | O estado das integrações deve ser atualizado sempre que o Dashboard for recarregado. |

---

# Componentes Relacionados

## Painel — Estado das Integrações

Lista resumida das integrações monitoradas.

Cada item apresenta:

* nome;
* situação;
* descrição resumida.

---

## Integração — PostgreSQL

Responsável por indicar a disponibilidade do banco de dados utilizado pelo catálogo local.

Possíveis estados:

* Disponível
* Indisponível

---

## Integração — Biblioteca

Verifica se o diretório principal da biblioteca está acessível.

Não realiza auditoria estrutural.

---

## Integração — MangaUpdates

Indica se o serviço pode ser utilizado para consultas.

Não executa sincronizações automáticas.

---

## Integração — Notion

Indica se a integração está corretamente configurada para futuras sincronizações.

Não executa sincronização durante a consulta.

---

# Regras de Negócio Relacionadas

### RN-046

O Dashboard deve apresentar apenas um resumo do estado das integrações.

---

### RN-047

O Dashboard não deve executar operações que alterem dados durante a verificação.

---

### RN-048

A indisponibilidade de uma integração não deve impedir o carregamento do Dashboard.

---

### RN-049

As integrações devem ser avaliadas individualmente.

---

### RN-050

O Dashboard deve utilizar uma linguagem compreensível para usuários não técnicos.

Exemplo:

```text
Banco de dados indisponível.
```

em vez de:

```text
psycopg.OperationalError
```

---

### RN-051

Sempre que possível, deve ser apresentada uma orientação simples para resolução do problema.

Exemplo:

```text
Biblioteca não encontrada.

Verifique o diretório configurado nas Configurações.
```

---

### RN-052

Problemas de infraestrutura possuem prioridade superior às pendências do Workflow.

Caso exista uma falha crítica de ambiente, ela deve ser destacada antes das demais informações do Dashboard.

---

# Estados Possíveis

| Estado          | Descrição                                     |
| --------------- | --------------------------------------------- |
| Disponível      | Integração operacional.                       |
| Atenção         | Funcional, porém com alguma limitação.        |
| Indisponível    | Não pode ser utilizada.                       |
| Não configurada | Configuração obrigatória ainda não realizada. |

---

# Matriz de Integrações

| Integração   | Finalidade                  | Destino para configuração |
| ------------ | --------------------------- | ------------------------- |
| PostgreSQL   | Catálogo local              | Configurações             |
| Biblioteca   | Leitura dos arquivos        | Configurações             |
| MangaUpdates | Consulta de metadados       | Configurações             |
| Notion       | Sincronização da biblioteca | Configurações             |

---

# Pós-condições

Após utilizar esta funcionalidade, o usuário deve ser capaz de:

* confirmar que o ambiente está pronto para uso;
* identificar rapidamente problemas de infraestrutura;
* distinguir falhas de ambiente de pendências operacionais;
* acessar o módulo **Configurações** quando necessário.

---

# Observações de UX

O painel de integrações deve transmitir **confiança**, e não gerar ansiedade.

Para isso:

* deve apresentar poucas informações;
* utilizar linguagem não técnica;
* evitar mensagens de erro detalhadas;
* destacar apenas problemas relevantes para o usuário;
* servir como um indicador rápido de saúde do ambiente, deixando diagnósticos completos para o módulo **Configurações**.

> **Observação de arquitetura:** a responsabilidade do Dashboard termina na **visualização do estado** das integrações. Toda configuração, teste aprofundado, autenticação, validação de credenciais e diagnóstico detalhado pertence exclusivamente ao módulo **Configurações**. Isso mantém uma separação clara entre monitoramento (Dashboard) e administração (Configurações).
