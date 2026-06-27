# Dashboard — Especificação Funcional

## 12 - Estados da Interface

---

# Objetivo do Documento

Este documento define todos os estados globais da interface do Dashboard da Manhwateca.

Seu objetivo é garantir que todos os componentes da página apresentem comportamento consistente diante das diferentes condições de carregamento, disponibilidade de dados e falhas operacionais.

Este documento centraliza os estados da interface, evitando que cada componente implemente comportamentos diferentes para uma mesma situação.

---

# Escopo

Este documento define apenas os estados visuais e funcionais da interface.

Ele **não** documenta:

* regras de negócio;
* mensagens específicas dos componentes;
* navegação;
* funcionamento interno das APIs.

Esses assuntos possuem documentação própria.

---

# Componentes Abrangidos

Os estados definidos neste documento aplicam-se aos seguintes componentes:

* Cabeçalho
* Próximo Passo Recomendado
* Métricas
* Pendências
* Integrações
* Workflow
* Ações Rápidas

Todos os componentes devem seguir os mesmos princípios descritos aqui.

---

# Estados Oficiais

O Dashboard suporta os seguintes estados globais.

| Estado     | Descrição                                                         |
| ---------- | ----------------------------------------------------------------- |
| Loading    | A página está carregando os dados iniciais.                       |
| Ready      | Todos os dados foram carregados corretamente.                     |
| Refreshing | Atualização manual em andamento.                                  |
| Partial    | Apenas parte dos dados está disponível.                           |
| Empty      | Não existem informações para exibir.                              |
| Error      | O Dashboard não conseguiu obter os dados necessários.             |
| Blocked    | Existe um bloqueio crítico que impede a continuidade do Workflow. |

Esses estados são mutuamente exclusivos para a página, embora componentes individuais possam apresentar comportamentos específicos derivados deles.

---

# Estado: Loading

## Objetivo

Representar o carregamento inicial do Dashboard.

---

## Comportamento

Durante este estado:

* os componentes permanecem visíveis;
* informações reais ainda não são exibidas;
* skeletons substituem temporariamente o conteúdo.

---

## Componentes

| Componente    | Comportamento                   |
| ------------- | ------------------------------- |
| Cabeçalho     | Skeleton na data de atualização |
| Próximo Passo | Skeleton completo               |
| Métricas      | Skeleton em todos os cards      |
| Pendências    | Lista simulada                  |
| Integrações   | Lista simulada                  |
| Workflow      | Skeleton das etapas             |
| Ações Rápidas | Botões desabilitados            |

---

## Regras

* não exibir mensagens de erro;
* evitar mudanças bruscas no layout;
* preservar as dimensões finais dos componentes.

---

# Estado: Ready

## Objetivo

Representar o funcionamento normal da página.

Todos os componentes exibem dados válidos provenientes da API agregadora.

Este é o estado padrão da aplicação.

---

# Estado: Refreshing

## Objetivo

Representar uma atualização manual em andamento.

---

## Comportamento

Durante este estado:

* os dados atuais permanecem visíveis;
* o botão **Recarregar** permanece desabilitado;
* um indicador visual informa que a atualização está em andamento.

Não devem ser exibidos skeletons.

---

## Regras

* não substituir os dados atuais até que a atualização seja concluída;
* impedir atualizações simultâneas;
* preservar posição de rolagem.

---

# Estado: Partial

## Objetivo

Representar situações em que apenas parte das informações pôde ser carregada.

---

## Exemplo

O PostgreSQL respondeu normalmente, mas o serviço do Notion está indisponível.

Nesse caso:

* Métricas continuam disponíveis;
* Workflow continua disponível;
* Integrações indicam falha no Notion.

---

## Regras

* componentes com dados válidos permanecem funcionando normalmente;
* apenas os componentes afetados apresentam estado degradado;
* o Dashboard permanece totalmente utilizável.

---

# Estado: Empty

## Objetivo

Representar ausência legítima de dados.

Este estado **não** representa erro.

---

## Exemplos

* biblioteca ainda não cadastrada;
* nenhuma obra catalogada;
* nenhuma pendência encontrada;
* Workflow ainda não iniciado.

---

## Regras

Cada componente deve apresentar mensagens específicas de estado vazio.

Nenhum componente deve desaparecer.

---

# Estado: Error

## Objetivo

Representar falha na obtenção dos dados necessários para renderização do Dashboard.

---

## Comportamento

Sempre que possível:

* preservar o último estado conhecido;
* informar o erro ao usuário;
* permitir nova tentativa de atualização.

---

## Regras

* não ocultar componentes;
* evitar tela completamente vazia;
* manter a navegação disponível.

---

# Estado: Blocked

## Objetivo

Representar bloqueios críticos que impedem a continuidade do Workflow.

---

## Exemplos

* PostgreSQL indisponível;
* diretório da biblioteca inacessível;
* configuração obrigatória inexistente.

---

## Comportamento

O Dashboard deve:

* destacar visualmente o bloqueio;
* impedir recomendações inconsistentes;
* direcionar o usuário para Configurações quando aplicável.

---

# Transições de Estado

O Dashboard pode realizar as seguintes transições.

```text id="6lup2m"
Loading
   │
   ▼
Ready
   │
   ├────────► Refreshing
   │             │
   │             ▼
   │          Ready
   │
   ├────────► Partial
   │
   ├────────► Empty
   │
   ├────────► Error
   │
   └────────► Blocked
```

Transições inválidas devem ser evitadas pela aplicação.

---

# Regras Gerais

## RF-001

O layout nunca deve mudar de estrutura durante uma transição de estado.

---

## RF-002

Skeletons devem preservar o tamanho final dos componentes.

---

## RF-003

Os componentes devem permanecer independentes.

Uma falha em um componente não deve impedir a renderização dos demais.

---

## RF-004

Sempre que possível, preservar o último estado conhecido da interface.

---

## RF-005

Estados vazios não representam erro.

---

## RF-006

Mensagens de erro devem ser claras e objetivas.

---

## RF-007

Estados de carregamento não devem bloquear a navegação principal.

---

## RF-008

O Dashboard nunca deve apresentar tela completamente vazia durante mudanças de estado.

---

# Responsividade

Os estados definidos neste documento devem apresentar o mesmo comportamento em Desktop, Tablet e Mobile.

Apenas a disposição visual dos componentes poderá variar.

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

Todos esses componentes devem respeitar as definições estabelecidas nesta especificação.

---

# Critérios de Aceite

A implementação será considerada conforme esta especificação quando:

* suportar todos os estados oficiais definidos neste documento;
* manter comportamento consistente entre todos os componentes;
* preservar estabilidade visual durante transições de estado;
* permitir recuperação após falhas sem necessidade de recarregar a página;
* evitar mudanças estruturais no layout durante carregamentos ou erros;
* aplicar as mesmas regras de estados em todas as resoluções suportadas.
