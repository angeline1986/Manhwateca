# US-009 — Navegar para os módulos especializados

## Identificação

| Campo            | Valor                                  |
| ---------------- | -------------------------------------- |
| **ID**           | US-009                                 |
| **Título**       | Navegar para os módulos especializados |
| **Módulo**       | Dashboard                              |
| **Prioridade**   | Alta                                   |
| **Tipo**         | Funcionalidade                         |
| **Epic**         | Dashboard                              |
| **Dependências** | Biblioteca, Fluxos, Configurações      |

---

# Objetivo

Como **usuária da Manhwateca**,

quero **acessar rapidamente o módulo mais adequado para realizar uma determinada tarefa**,

para que **eu consiga continuar meu trabalho sem precisar procurar funcionalidades espalhadas pela aplicação**.

---

# Descrição

O Dashboard é a porta de entrada da Manhwateca.

Seu papel é orientar o usuário e direcioná-lo para o módulo correto conforme a ação desejada.

O Dashboard não deve replicar funcionalidades existentes em outros módulos. Sempre que uma atividade exigir interação detalhada, o sistema deve encaminhar o usuário para a página responsável.

A navegação deve preservar o contexto do usuário, posicionando-o exatamente na tela ou etapa relacionada à ação iniciada.

---

# Valor de Negócio

Ao centralizar a navegação no Dashboard, a aplicação torna-se mais previsível e reduz a necessidade de memorizar onde cada funcionalidade está localizada.

Isso proporciona:

* menor curva de aprendizado;
* redução da navegação desnecessária;
* melhor organização entre módulos;
* separação clara entre orientação e execução.

---

# Fluxo Principal

1. O usuário acessa o Dashboard.
2. O usuário identifica a ação desejada.
3. O usuário seleciona um botão, card ou pendência.
4. O Dashboard determina qual módulo é responsável por aquela atividade.
5. O sistema navega automaticamente para a página correspondente.
6. O módulo de destino é aberto já no contexto correto.

---

# Fluxos Alternativos

### FA-01 — Navegação para Biblioteca

Quando o usuário desejar consultar ou editar obras, o Dashboard deve abrir o módulo **Biblioteca**.

---

### FA-02 — Navegação para Fluxos

Quando a ação estiver relacionada à execução do Workflow, o Dashboard deve abrir o módulo **Fluxos** diretamente na etapa correspondente.

---

### FA-03 — Navegação para Configurações

Quando existir um problema de infraestrutura ou quando o usuário desejar alterar configurações da aplicação, o Dashboard deve abrir **Configurações**.

---

### FA-04 — Destino indisponível

Caso o módulo de destino não possa ser carregado, o Dashboard deve informar o erro e permanecer funcional.

---

# Critérios de Aceite

| ID     | Critério                                                                                     |
| ------ | -------------------------------------------------------------------------------------------- |
| AC-001 | O Dashboard deve permitir navegar para Biblioteca, Fluxos e Configurações.                   |
| AC-002 | Cada ação do Dashboard deve possuir um único destino definido.                               |
| AC-003 | O módulo de destino deve ser aberto preservando o contexto da ação iniciada.                 |
| AC-004 | O Dashboard não deve duplicar funcionalidades existentes em outros módulos.                  |
| AC-005 | Em caso de falha na navegação, o Dashboard deve permanecer operacional e informar o usuário. |
| AC-006 | O usuário deve conseguir retornar ao Dashboard sem perda de informações.                     |

---

# Componentes Relacionados

## Navegação — Biblioteca

Destino para atividades de consulta e gerenciamento das obras.

Exemplos:

* consultar obras;
* editar informações;
* atualizar progresso de leitura;
* pesquisar no catálogo.

---

## Navegação — Fluxos

Destino para atividades operacionais.

Exemplos:

* organizar biblioteca;
* catalogar arquivos;
* resolver IDs;
* atualizar metadados;
* sincronizar Notion.

O Dashboard deve encaminhar o usuário diretamente para a etapa apropriada.

---

## Navegação — Configurações

Destino para administração do ambiente.

Exemplos:

* configurar diretórios;
* validar integrações;
* alterar parâmetros;
* consultar diagnósticos.

---

# Regras de Negócio Relacionadas

### RN-061

O Dashboard é o ponto de entrada da aplicação.

---

### RN-062

Cada funcionalidade pertence exclusivamente a um módulo.

Não deve existir duplicação de responsabilidades.

---

### RN-063

O Dashboard deve apenas orientar e navegar.

A execução das funcionalidades ocorre exclusivamente no módulo de destino.

---

### RN-064

Toda navegação deve preservar o contexto da ação iniciada.

Exemplo:

Selecionar uma pendência de **Resolver IDs** deve abrir **Fluxos** já posicionado na etapa **Resolver IDs**, e não apenas a página inicial do módulo.

---

### RN-065

O menu principal da aplicação deve conter apenas os módulos de primeiro nível:

* Dashboard
* Biblioteca
* Fluxos
* Configurações

---

### RN-066

O Dashboard não deve permitir navegação para telas internas de administração ou manutenção que não façam parte da experiência do usuário.

---

### RN-067

Caso uma funcionalidade esteja temporariamente indisponível, o Dashboard deve informar o motivo antes da navegação.

---

### RN-068

O histórico de navegação deve permitir que o usuário retorne ao Dashboard sem perder o estado da aplicação.

---

# Matriz de Navegação

| Origem                      | Destino       | Contexto Preservado              |
| --------------------------- | ------------- | -------------------------------- |
| Próximo Passo Recomendado   | Fluxos        | Etapa recomendada                |
| Pendência                   | Fluxos        | Etapa relacionada à pendência    |
| Ação "Organizar biblioteca" | Fluxos        | Etapa 1                          |
| Ação "Catalogar arquivos"   | Fluxos        | Etapa 2                          |
| Ação "Resolver IDs"         | Fluxos        | Etapa 3                          |
| Ação "Atualizar metadados"  | Fluxos        | Etapa 4                          |
| Ação "Sincronizar Notion"   | Fluxos        | Etapa 5                          |
| Ação "Abrir Biblioteca"     | Biblioteca    | Tela principal da biblioteca     |
| Problema de integração      | Configurações | Seção correspondente ao problema |

---

# Fonte de Navegação

Toda navegação deve utilizar o roteador interno da aplicação.

O Dashboard não deve conhecer a implementação interna dos módulos; apenas seus pontos de entrada.

---

# Pós-condições

Após utilizar esta funcionalidade, o usuário deve ser capaz de:

* acessar rapidamente o módulo correto;
* continuar uma atividade exatamente do ponto necessário;
* evitar navegar por diferentes páginas para localizar funcionalidades;
* compreender claramente a divisão de responsabilidades entre Dashboard, Biblioteca, Fluxos e Configurações.

---

# Observações de UX

A navegação deve ser **orientada por intenção**, e não por tecnologia.

O usuário nunca deve precisar pensar:

> "Em qual página fica essa funcionalidade?"

Em vez disso, ele deve pensar:

> "Quero resolver IDs."

E o Dashboard deve levá-lo automaticamente ao local correto.

Além disso, o Dashboard deve permanecer uma tela **leve e estratégica**, atuando como centro de comando da aplicação, enquanto Biblioteca, Fluxos e Configurações concentram as funcionalidades operacionais e administrativas.
