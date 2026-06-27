# Dashboard — Especificação Funcional

## 13 - Catálogo de Mensagens

---

# Objetivo do Documento

Este documento centraliza todas as mensagens utilizadas pelo Dashboard da Manhwateca.

Seu objetivo é garantir consistência na comunicação com o usuário, padronizando textos, severidades e contextos de utilização em toda a interface.

Todos os componentes do Dashboard devem utilizar exclusivamente as mensagens definidas neste documento.

---

# Escopo

Este documento define:

* mensagens informativas;
* mensagens de sucesso;
* mensagens de atenção;
* mensagens de erro;
* mensagens de estado vazio;
* mensagens de bloqueio.

Não define:

* mensagens técnicas de exceções;
* mensagens de API;
* logs internos;
* mensagens específicas de outros módulos.

---

# Padrões de Escrita

Todas as mensagens devem seguir os princípios abaixo.

## Clareza

A mensagem deve informar exatamente o que aconteceu.

---

## Objetividade

Evitar textos longos.

Preferir frases curtas.

---

## Linguagem

Utilizar linguagem simples.

Evitar termos técnicos sempre que possível.

---

## Orientação

Sempre que aplicável, indicar ao usuário a próxima ação recomendada.

---

# Severidades

| Severidade | Utilização                     |
| ---------- | ------------------------------ |
| Info       | Informação geral               |
| Success    | Operação concluída com sucesso |
| Warning    | Situação que exige atenção     |
| Error      | Falha que impede uma operação  |
| Blocked    | Bloqueio crítico do ambiente   |

---

# Mensagens Informativas

| ID           | Mensagem                                | Contexto                       |
| ------------ | --------------------------------------- | ------------------------------ |
| MSG-DASH-001 | Dashboard carregado.                    | Carregamento inicial concluído |
| MSG-DASH-002 | Informações atualizadas.                | Atualização concluída          |
| MSG-DASH-003 | Nenhuma alteração encontrada.           | Atualização sem mudanças       |
| MSG-DASH-004 | Última atualização realizada às {hora}. | Cabeçalho                      |

---

# Mensagens de Sucesso

| ID           | Mensagem                                 | Contexto              |
| ------------ | ---------------------------------------- | --------------------- |
| MSG-DASH-101 | Dashboard atualizado com sucesso.        | Atualização manual    |
| MSG-DASH-102 | Todas as integrações estão operacionais. | Painel de Integrações |
| MSG-DASH-103 | Nenhuma pendência encontrada.            | Painel de Pendências  |
| MSG-DASH-104 | Workflow concluído.                      | Resumo do Workflow    |

---

# Mensagens de Atenção

| ID           | Mensagem                                        | Contexto      |
| ------------ | ----------------------------------------------- | ------------- |
| MSG-DASH-201 | Existem pendências que exigem atenção.          | Pendências    |
| MSG-DASH-202 | Algumas integrações apresentam restrições.      | Integrações   |
| MSG-DASH-203 | Existem obras aguardando identificação.         | Próximo Passo |
| MSG-DASH-204 | Alterações aguardam sincronização com o Notion. | Pendências    |

---

# Mensagens de Erro

| ID           | Mensagem                                                 | Contexto             |
| ------------ | -------------------------------------------------------- | -------------------- |
| MSG-DASH-301 | Não foi possível carregar o Dashboard.                   | Carregamento inicial |
| MSG-DASH-302 | Não foi possível atualizar as informações.               | Atualização          |
| MSG-DASH-303 | Não foi possível consultar o Workflow.                   | Workflow             |
| MSG-DASH-304 | Não foi possível consultar as pendências.                | Pendências           |
| MSG-DASH-305 | Não foi possível consultar as integrações.               | Integrações          |
| MSG-DASH-306 | Não foi possível determinar o próximo passo recomendado. | Próximo Passo        |

---

# Mensagens de Estado Vazio

| ID           | Mensagem                      | Contexto      |
| ------------ | ----------------------------- | ------------- |
| MSG-DASH-401 | Nenhuma pendência encontrada. | Pendências    |
| MSG-DASH-402 | Workflow ainda não iniciado.  | Workflow      |
| MSG-DASH-403 | Nenhuma obra cadastrada.      | Métricas      |
| MSG-DASH-404 | Nenhuma ação pendente.        | Próximo Passo |

---

# Mensagens de Bloqueio

| ID           | Mensagem                                                       | Contexto    |
| ------------ | -------------------------------------------------------------- | ----------- |
| MSG-DASH-501 | PostgreSQL indisponível. Verifique a configuração do ambiente. | Integrações |
| MSG-DASH-502 | Biblioteca não configurada.                                    | Integrações |
| MSG-DASH-503 | Não foi possível acessar a biblioteca configurada.             | Integrações |
| MSG-DASH-504 | O Workflow está bloqueado até que o ambiente seja corrigido.   | Workflow    |
| MSG-DASH-505 | Corrija os problemas de configuração antes de continuar.       | Dashboard   |

---

# Uso de Variáveis

Quando necessário, as mensagens podem utilizar variáveis.

| Variável     | Exemplo      |
| ------------ | ------------ |
| {hora}       | 20:35        |
| {quantidade} | 8            |
| {etapa}      | Resolver IDs |
| {integracao} | PostgreSQL   |

Exemplo:

```text id="p6chra"
Existem {quantidade} obras aguardando identificação.
```

Resultado:

```text id="yc8twn"
Existem 8 obras aguardando identificação.
```

---

# Regras Funcionais

## RF-001

Todas as mensagens devem possuir um identificador único.

---

## RF-002

Mensagens não devem conter detalhes técnicos da implementação.

---

## RF-003

Erros internos, stack traces ou exceções nunca devem ser exibidos ao usuário.

---

## RF-004

Sempre que possível, mensagens devem orientar a próxima ação.

---

## RF-005

Mensagens iguais devem reutilizar o mesmo identificador.

---

## RF-006

As mensagens devem ser reutilizadas por todos os componentes do Dashboard.

---

## RF-007

A severidade da mensagem deve ser compatível com a gravidade da situação.

---

## RF-008

Mensagens não devem depender exclusivamente de cores para transmitir significado.

---

# Localização

Todas as mensagens devem estar centralizadas em um único catálogo de recursos da aplicação.

Os componentes devem consumir as mensagens por meio de seus respectivos identificadores.

Isso facilita:

* internacionalização futura;
* manutenção;
* padronização;
* reutilização.

---

# Dependências

Este documento é utilizado por:

* 03-cabecalho.md
* 04-proximo-passo.md
* 05-metricas.md
* 06-pendencias.md
* 07-workflow.md
* 08-integracoes.md
* 09-acoes-rapidas.md
* 10-atualizacao.md
* 12-estados-da-interface.md

Todos os componentes do Dashboard devem utilizar exclusivamente as mensagens catalogadas neste documento.

---

# Critérios de Aceite

O catálogo será considerado conforme esta especificação quando:

* todas as mensagens do Dashboard estiverem documentadas;
* cada mensagem possuir identificador único;
* existir uma classificação por severidade;
* as mensagens forem reutilizáveis entre componentes;
* não existirem mensagens duplicadas com o mesmo significado;
* o texto utilizar linguagem clara, objetiva e consistente;
* os componentes consumirem este catálogo como única fonte de mensagens da interface.
