# Dashboard — Especificação Funcional

## 11 - Navegação

---

# Objetivo do Documento

Este documento especifica as regras de navegação do Dashboard da Manhwateca.

Seu objetivo é definir como o usuário transita entre o Dashboard e os demais módulos da aplicação, garantindo uma experiência previsível, consistente e orientada por contexto.

Esta documentação implementa a **US-009 — Navegar para os módulos especializados**.

---

# Objetivo da Navegação

O Dashboard é o ponto de entrada da aplicação.

Sua principal responsabilidade é orientar o usuário e direcioná-lo ao módulo correto para executar determinada atividade.

O Dashboard **não executa funcionalidades operacionais**.

---

# User Story Relacionada

| ID     | Título                                 |
| ------ | -------------------------------------- |
| US-009 | Navegar para os módulos especializados |

---

# Módulos da Aplicação

A navegação do Dashboard envolve quatro módulos principais.

| Módulo        | Responsabilidade                     |
| ------------- | ------------------------------------ |
| Dashboard     | Informar e orientar                  |
| Biblioteca    | Consultar e editar obras             |
| Fluxos        | Executar o Workflow                  |
| Configurações | Configurar e diagnosticar o ambiente |

Nenhum outro módulo deve ser acessado diretamente pelo Dashboard.

---

# Princípios de Navegação

Toda navegação deve seguir os seguintes princípios.

## Direcionamento

O Dashboard orienta o usuário para o local correto.

---

## Não Duplicação

Nenhuma funcionalidade operacional deve ser executada diretamente pelo Dashboard.

---

## Preservação de Contexto

Sempre que possível, o usuário deve chegar exatamente ao ponto onde a ação deverá continuar.

---

## Consistência

Uma mesma ação deve sempre levar ao mesmo destino.

---

# Origens de Navegação

A navegação pode ser iniciada pelos seguintes componentes.

| Origem                    | Destino                             |
| ------------------------- | ----------------------------------- |
| Menu lateral              | Módulo correspondente               |
| Próximo Passo Recomendado | Fluxos                              |
| Pendências                | Fluxos ou Configurações             |
| Ações Rápidas             | Biblioteca, Fluxos ou Configurações |

Todos os componentes devem utilizar o mesmo mecanismo interno de navegação.

---

# Navegação pelo Menu

O menu lateral representa a navegação principal da aplicação.

Itens disponíveis:

```text
Dashboard
Biblioteca
Fluxos
Configurações
```

Cada item possui um único destino.

---

# Navegação pelo Próximo Passo

Ao selecionar o botão principal do componente **Próximo Passo Recomendado**, o Dashboard deve abrir o módulo Fluxos na etapa correspondente.

Exemplo:

```text
Dashboard

↓

Fluxos

↓

Resolver IDs
```

O Dashboard não inicia automaticamente a execução da etapa.

---

# Navegação pelas Pendências

Cada pendência possui um único destino.

| Pendência                  | Destino                       |
| -------------------------- | ----------------------------- |
| Organizar Biblioteca       | Fluxos → Organizar Biblioteca |
| Catalogar Arquivos         | Fluxos → Catalogar Arquivos   |
| Resolver IDs               | Fluxos → Resolver IDs         |
| Atualizar Metadados        | Fluxos → Atualizar Metadados  |
| Sincronizar Notion         | Fluxos → Sincronizar Notion   |
| Problema de infraestrutura | Configurações                 |

O Dashboard apenas realiza a navegação.

---

# Navegação pelas Ações Rápidas

As Ações Rápidas devem utilizar exatamente os mesmos destinos do menu principal.

| Ação                | Destino                   |
| ------------------- | ------------------------- |
| Biblioteca          | Biblioteca                |
| Fluxos              | Fluxos                    |
| Configurações       | Configurações             |
| Atualizar Dashboard | Permanece na página atual |

---

# Preservação de Contexto

Sempre que possível, a navegação deve preservar o contexto da ação iniciada.

Exemplos:

```text
Dashboard

↓

Resolver IDs

↓

Fluxos
```

```text
Dashboard

↓

Erro PostgreSQL

↓

Configurações
```

```text
Dashboard

↓

Abrir Biblioteca

↓

Biblioteca
```

O usuário não deve precisar procurar novamente a funcionalidade desejada.

---

# Navegação Bloqueada

Quando o destino estiver indisponível, a navegação não deve ocorrer.

O Dashboard deve informar o motivo ao usuário.

Exemplo:

```text
Módulo temporariamente indisponível.
```

---

# Atualização da Navegação

A navegação não deve provocar atualização automática do Dashboard.

Caso o usuário retorne posteriormente ao Dashboard, os dados poderão ser atualizados conforme definido em **10-atualizacao.md**.

---

# Regras Funcionais

## RF-001

Toda navegação deve utilizar o roteador interno da aplicação.

---

## RF-002

Cada ação possui um único destino.

---

## RF-003

O Dashboard nunca deve executar processos antes da navegação.

---

## RF-004

A navegação deve preservar o contexto sempre que possível.

---

## RF-005

A navegação deve ocorrer apenas após interação explícita do usuário.

---

## RF-006

Em caso de falha, o Dashboard deve permanecer funcional.

---

## RF-007

O histórico de navegação deve permitir retorno ao Dashboard.

---

## RF-008

O Dashboard não deve abrir telas internas de módulos diretamente, exceto quando necessário para preservar o contexto da ação iniciada.

---

# Fluxos de Navegação

## Fluxo Principal

```text
Dashboard

↓

Usuário seleciona ação

↓

Dashboard identifica destino

↓

Navegação

↓

Módulo correspondente
```

---

## Fluxo com Erro

```text
Dashboard

↓

Usuário seleciona ação

↓

Destino indisponível

↓

Mensagem ao usuário

↓

Permanece no Dashboard
```

---

# Responsividade

O comportamento da navegação deve ser idêntico em Desktop, Tablet e Mobile.

Apenas a forma de apresentação do menu poderá variar.

---

# Acessibilidade

A navegação deve:

* permitir uso por teclado;
* indicar visualmente o foco;
* fornecer rótulos acessíveis para todos os controles;
* manter comportamento consistente em leitores de tela.

---

# Dependências

Este documento possui relação direta com:

* 04-proximo-passo.md
* 06-pendencias.md
* 09-acoes-rapidas.md
* 10-atualizacao.md

Os destinos utilizados pela navegação são implementados pelos módulos Biblioteca, Fluxos e Configurações.

---

# Critérios de Aceite

A navegação será considerada conforme esta especificação quando:

* todas as ações do Dashboard possuírem um destino único e previsível;
* o contexto da ação for preservado sempre que possível;
* o Dashboard não executar funcionalidades operacionais antes da navegação;
* o usuário conseguir retornar ao Dashboard utilizando o histórico da aplicação;
* falhas de navegação não comprometerem o funcionamento da interface;
* todos os componentes utilizarem o mesmo mecanismo interno de roteamento;
* a experiência de navegação permanecer consistente em todas as resoluções suportadas.
