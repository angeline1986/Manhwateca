# Manual do Usuário — Módulo Fluxos

> Documento: **README.md**

---

# Bem-vindo ao módulo Fluxos

O módulo **Fluxos** é o centro operacional da Manhwateca.

É através dele que todas as tarefas responsáveis por organizar, catalogar, atualizar e sincronizar sua biblioteca são executadas.

Enquanto o **Dashboard** informa a situação atual da biblioteca, a página **Fluxos** permite que você execute as ações necessárias para manter seus dados sempre organizados e atualizados.

---

# Objetivo deste Manual

Este manual explica como utilizar cada funcionalidade da página **Fluxos**.

Ao final da leitura você será capaz de:

* entender como funciona o Workflow da Manhwateca;
* executar cada etapa individualmente;
* acompanhar o progresso do processamento;
* interpretar mensagens e alertas;
* solucionar os problemas mais comuns.

Este documento é destinado aos usuários finais da aplicação e não aborda detalhes técnicos de implementação.

---

# Como este Manual está Organizado

Os capítulos seguem a mesma ordem do Workflow executado pela aplicação.

| Documento                    | Conteúdo                                               |
| ---------------------------- | ------------------------------------------------------ |
| 01-introducao.md             | Conceitos básicos e funcionamento do módulo            |
| 02-conhecendo-os-fluxos.md   | Conhecendo a interface e seus componentes              |
| 03-organizar-biblioteca.md   | Como organizar a biblioteca                            |
| 04-catalogar-obras.md        | Como catalogar novas obras                             |
| 05-resolver-ids.md           | Como localizar e confirmar IDs                         |
| 06-atualizar-metadados.md    | Como atualizar informações das obras                   |
| 07-sincronizar-com-notion.md | Como sincronizar a biblioteca com o Notion             |
| 08-acompanhar-o-workflow.md  | Como acompanhar uma execução em andamento              |
| 09-cancelar-ou-reiniciar.md  | Cancelar, reiniciar e reprocessar etapas               |
| 10-ajuda.md                  | Perguntas frequentes, solução de problemas e glossário |

---

# O Workflow da Manhwateca

O módulo Fluxos executa sempre a mesma sequência de etapas.

```text
Organizar Biblioteca

↓

Catalogar Obras

↓

Resolver IDs

↓

Atualizar Metadados

↓

Sincronizar Notion
```

Cada etapa prepara os dados necessários para a seguinte.

Embora seja possível executar etapas individualmente, recomenda-se utilizar o Workflow completo sempre que houver alterações significativas na biblioteca.

---

# Quando utilizar a página Fluxos

Utilize este módulo quando:

* adicionar novas obras à biblioteca;
* reorganizar pastas ou arquivos;
* desejar atualizar informações das obras;
* precisar localizar IDs do MangaUpdates;
* sincronizar alterações com o Notion.

No uso diário, normalmente basta executar o Workflow completo após realizar mudanças na biblioteca.

---

# Antes de começar

Antes da primeira execução, verifique se:

* a biblioteca foi configurada corretamente;
* o PostgreSQL está em funcionamento;
* o acesso ao MangaUpdates está disponível;
* a integração com o Notion foi configurada (caso utilize esse recurso).

Caso alguma dessas dependências não esteja disponível, determinadas etapas poderão ser interrompidas.

---

# Fluxo de Leitura Recomendado

Se esta é sua primeira utilização da Manhwateca, recomenda-se a seguinte sequência de leitura:

```text
Introdução

↓

Conhecendo os Fluxos

↓

Organizar Biblioteca

↓

Catalogar Obras

↓

Resolver IDs

↓

Atualizar Metadados

↓

Sincronizar Notion

↓

Acompanhar o Workflow

↓

Cancelar ou Reiniciar

↓

Ajuda
```

Essa ordem acompanha o ciclo natural de utilização da aplicação.

---

# Convenções Utilizadas

Ao longo deste manual serão utilizados os seguintes elementos:

> **Dica**
>
> Informações que facilitam o uso da aplicação.

---

> **Importante**
>
> Informações que evitam erros ou perda de tempo durante o processamento.

---

**Botões**

Sempre aparecerão em **negrito**.

Exemplo:

* **Executar Workflow**
* **Cancelar**
* **Reexecutar Etapa**

---

# Relação com os demais documentos

A documentação da Manhwateca está organizada em quatro níveis.

```text
Histórias de Usuário

↓

Especificação Funcional

↓

Documentação Técnica

↓

Manual do Usuário
```

Este manual representa a camada voltada ao uso da aplicação.

---

# Conclusão

O módulo **Fluxos** concentra todas as operações responsáveis por manter sua biblioteca organizada, atualizada e sincronizada. Os próximos capítulos apresentam cada etapa do Workflow em detalhes, explicando quando utilizá-la, como executá-la e como interpretar os resultados obtidos.
