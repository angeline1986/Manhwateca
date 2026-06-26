# Dashboard — User Story + Regras de Negócio

# 1. Objetivo do Módulo

## Visão Geral

O Dashboard é a porta de entrada da Manhwateca e representa a visão operacional consolidada do sistema.

Seu principal objetivo é informar ao usuário, de forma imediata e sem exigir navegação entre módulos técnicos, qual é o estado atual da biblioteca e qual deve ser a próxima ação recomendada.

O Dashboard não é responsável por executar processos complexos. Seu papel é consolidar informações provenientes dos demais módulos (Biblioteca, Workflow, MangaUpdates, Notion e Sistema), transformando dados técnicos em informações acionáveis.

A filosofia do Dashboard é orientada por decisão.

Ao abrir a aplicação, o usuário deve conseguir responder às seguintes perguntas em poucos segundos:

* Minha biblioteca está saudável?
* Existe alguma pendência importante?
* Posso continuar exatamente de onde parei?
* Existe algum problema que impeça a sincronização?
* Qual é a próxima ação recomendada?

O Dashboard deve reduzir a carga cognitiva do usuário, eliminando a necessidade de decidir manualmente qual ferramenta utilizar.

---

## Objetivos Funcionais

O Dashboard possui os seguintes objetivos funcionais:

### Consolidar o estado geral do sistema

Apresentar, em uma única tela, o resumo dos principais indicadores da Manhwateca, incluindo:

* quantidade total de obras;
* quantidade de novos capítulos detectados;
* obras pendentes de identificação;
* sincronizações pendentes;
* estado geral do ambiente.

---

### Priorizar pendências

Nem toda pendência possui a mesma importância.

O Dashboard deve apresentar primeiro as pendências que bloqueiam a continuidade do fluxo.

Exemplo:

```text
Biblioteca inacessível
↓

Banco indisponível
↓

IDs pendentes

↓

Metadados desatualizados

↓

Notion pendente
```

---

### Recomendar a próxima ação

O Dashboard deve calcular automaticamente qual ação oferece maior valor naquele momento.

Essa recomendação deve considerar:

* estado do workflow;
* bloqueios;
* pendências;
* tarefas em execução;
* erros recentes.

A recomendação deve ser apresentada como um único card de destaque.

---

### Direcionar o usuário

O Dashboard não substitui as páginas especializadas.

Ele atua como ponto de entrada para:

* Biblioteca;
* Fluxos;
* Configurações.

Sempre que uma ação exigir maior interação, o Dashboard deve encaminhar o usuário para a tela correspondente.

---

### Exibir informações sem sobrecarregar

O Dashboard deve privilegiar indicadores resumidos.

Não devem ser exibidos:

* listas extensas;
* tabelas grandes;
* detalhes técnicos;
* logs completos.

Essas informações pertencem aos módulos especializados.

---

## Responsabilidades

O Dashboard é responsável por:

* carregar indicadores consolidados;
* calcular o próximo passo recomendado;
* listar pendências críticas;
* exibir ações rápidas;
* apresentar o estado das integrações;
* encaminhar o usuário para o módulo correto.

---

## Não é responsabilidade do Dashboard

O Dashboard não deve:

* executar organização de arquivos;
* catalogar obras;
* resolver IDs;
* consultar MangaUpdates;
* sincronizar diretamente com o Notion;
* editar obras;
* exibir logs completos;
* mostrar configurações avançadas.

Essas responsabilidades pertencem aos respectivos módulos.

---

## Benefícios esperados

Após a implementação deste módulo, espera-se que o usuário consiga:

* compreender o estado geral da biblioteca em menos de 10 segundos;
* identificar rapidamente problemas críticos;
* retomar o trabalho exatamente do ponto onde parou;
* executar o fluxo correto sem precisar decidir entre diversas ferramentas;
* reduzir significativamente a navegação entre páginas.

---

# 2. Personas

O Dashboard foi projetado considerando diferentes perfis de utilização da Manhwateca.

Embora o sistema possa evoluir para suportar múltiplos usuários, sua arquitetura deve ser preparada desde o início para diferentes personas.

---

## Persona 1 — Curadora da Biblioteca (Primária)

### Perfil

Usuária responsável pela organização da coleção.

É quem utiliza o sistema diariamente.

Possui conhecimento sobre:

* manhwas;
* novels;
* danmei;
* Notion;
* MangaUpdates.

Não necessariamente possui conhecimento técnico.

---

### Objetivos

* manter a biblioteca organizada;
* acompanhar novos capítulos;
* atualizar progresso de leitura;
* enriquecer informações das obras;
* sincronizar com o Notion.

---

### Necessidades

* interface simples;
* fluxo guiado;
* pouca navegação;
* confirmação antes de alterações importantes.

---

### Principais ações

* abrir Dashboard;
* verificar pendências;
* continuar fluxo;
* consultar Biblioteca.

---

## Persona 2 — Operadora de Catalogação

Perfil responsável pela manutenção dos dados.

Seu foco é garantir que o catálogo permaneça consistente.

Normalmente trabalha em:

* catalogação;
* revisão de IDs;
* atualização de metadados.

---

### Objetivos

* eliminar inconsistências;
* revisar correspondências;
* atualizar catálogo.

---

### Necessidades

* visualizar pendências;
* executar etapas rapidamente;
* acompanhar progresso.

---

## Persona 3 — Desenvolvedora

Responsável pela manutenção da aplicação.

Utiliza o Dashboard para validar:

* estado do ambiente;
* integrações;
* erros;
* diagnósticos.

---

### Objetivos

* verificar rapidamente a saúde do sistema;
* identificar falhas;
* reproduzir problemas.

---

### Necessidades

* indicadores confiáveis;
* acesso rápido aos diagnósticos;
* separação entre operação e configuração.

---

## Persona 4 — Usuária Ocasional

Abre a aplicação apenas eventualmente.

Pode ficar semanas sem utilizar o sistema.

Quando retorna, precisa entender rapidamente:

* onde parou;
* o que mudou;
* qual é a próxima ação.

Essa persona justifica a existência do card "Próximo passo recomendado".

---

# 3. Objetivos do Dashboard

O Dashboard existe para transformar um conjunto complexo de processos técnicos em uma experiência simples e orientada por tarefas.

Os objetivos estratégicos do módulo são:

## O1 — Ser o ponto único de entrada

Todo uso da aplicação deve começar pelo Dashboard.

Nenhum outro módulo deve assumir esse papel.

---

## O2 — Informar antes de agir

Antes de executar qualquer operação, o Dashboard deve apresentar o estado atual da biblioteca e destacar possíveis impedimentos.

---

## O3 — Guiar o usuário

O Dashboard deve recomendar automaticamente a próxima ação mais adequada, evitando que o usuário tenha que decidir entre diferentes módulos técnicos.

---

## O4 — Reduzir carga cognitiva

A interface deve apresentar apenas informações relevantes para a tomada de decisão, ocultando detalhes operacionais que pertencem a outras áreas do sistema.

---

## O5 — Centralizar indicadores

O Dashboard deve consolidar métricas provenientes de diferentes componentes da aplicação, como Biblioteca, Workflow, MangaUpdates, Notion e Ambiente, exibindo uma visão única do estado do sistema.

---

## O6 — Evidenciar problemas críticos

Falhas que impeçam a continuidade do fluxo (como banco indisponível, biblioteca inacessível ou tarefas bloqueadas) devem ter prioridade máxima na apresentação.

---

## O7 — Facilitar a retomada do trabalho

Ao abrir a aplicação após qualquer período de inatividade, o usuário deve conseguir identificar rapidamente:

* o último ponto executado;
* as pendências existentes;
* a próxima etapa recomendada.

---

## O8 — Encaminhar para o módulo correto

Quando uma ação exigir maior interação, o Dashboard deve atuar apenas como ponto de entrada, direcionando o usuário para Biblioteca, Fluxos ou Configurações, sem replicar funcionalidades desses módulos.

---

Esse é o nível de detalhamento que eu seguiria para todo o restante da documentação. O documento completo teria esse mesmo padrão para User Stories, Regras de Negócio, Matrizes de Decisão, State Machines e demais seções.

# 4. Escopo

## Visão Geral

O Dashboard é responsável exclusivamente por consolidar informações operacionais da Manhwateca e orientar a tomada de decisão do usuário.

Seu escopo está limitado à apresentação do estado atual do sistema, recomendação da próxima ação e navegação para os módulos responsáveis pela execução das tarefas.

O Dashboard **não executa processos complexos**, apenas os inicia ou direciona o usuário para a área adequada.

---

## Funcionalidades contempladas

### 4.1 Estado Geral da Biblioteca

Exibir indicadores consolidados da biblioteca, como:

* total de obras cadastradas;
* obras em leitura;
* novos capítulos detectados;
* obras sem ID;
* obras com metadados pendentes;
* última catalogação realizada.

---

### 4.2 Próximo Passo Recomendado

Calcular automaticamente qual ação oferece maior valor naquele momento.

A recomendação deve considerar:

* workflow atual;
* bloqueios;
* pendências;
* erros;
* tarefas em execução.

O Dashboard deve apresentar apenas uma recomendação principal por vez.

---

### 4.3 Pendências Operacionais

Apresentar somente pendências que exigem ação do usuário.

Exemplos:

* obras sem ID;
* sincronização pendente;
* novos capítulos;
* conflitos de organização;
* erros de integração.

Cada pendência deve conter:

* descrição;
* criticidade;
* quantidade de itens;
* ação sugerida.

---

### 4.4 Indicadores do Sistema

Exibir informações resumidas sobre:

* PostgreSQL;
* Biblioteca local;
* MangaUpdates;
* Notion;
* ambiente da aplicação.

Esses indicadores possuem caráter informativo.

---

### 4.5 Ações Rápidas

Disponibilizar atalhos para os principais objetivos do usuário.

Exemplos:

* Atualizar capítulos
* Organizar biblioteca
* Continuar workflow
* Sincronizar Notion

As ações rápidas não substituem o Workflow.

---

### 4.6 Navegação

O Dashboard deve permitir acesso aos módulos:

* Biblioteca;
* Fluxos;
* Configurações.

---

### 4.7 Atualização das Informações

Permitir atualização manual dos indicadores através do botão:

> Recarregar

Esse botão deve consultar novamente todas as informações do Dashboard.

---

### 4.8 Resumo do Workflow

Exibir:

* etapa atual;
* progresso geral;
* última execução;
* próxima etapa.

Não deve permitir execução detalhada das etapas.

---

## Dados consumidos

O Dashboard deve consumir informações provenientes de:

* PostgreSQL;
* Workflow;
* Biblioteca local;
* MangaUpdates;
* Notion;
* Serviços internos.

Não deve acessar diretamente arquivos físicos da biblioteca.

---

# 5. Fora do Escopo

As funcionalidades abaixo pertencem a outros módulos e não fazem parte das responsabilidades do Dashboard.

---

## Organização da Biblioteca

O Dashboard não deve:

* gerar previews;
* mover arquivos;
* renomear capítulos;
* reorganizar diretórios;
* corrigir estrutura.

Essas ações pertencem ao módulo Fluxos.

---

## Catalogação

O Dashboard não deve:

* ler pastas;
* escanear capítulos;
* inserir registros no banco.

Pode apenas informar quando o catálogo estiver desatualizado.

---

## Resolução de IDs

O Dashboard não deve:

* pesquisar MangaUpdates;
* mostrar candidatos;
* permitir escolha manual;
* confirmar correspondências.

Essas ações pertencem ao Workflow.

---

## Atualização de Metadados

Não é responsabilidade do Dashboard:

* consultar APIs externas;
* atualizar capa;
* atualizar gêneros;
* atualizar autores;
* atualizar status;
* atualizar sinopse.

---

## Sincronização do Notion

O Dashboard não deve:

* criar páginas;
* atualizar páginas;
* excluir páginas;
* executar sincronização.

Pode apenas informar:

* sincronização pendente;
* última sincronização;
* resultado da última execução.

---

## Edição de Obras

O Dashboard não deve permitir:

* editar progresso;
* editar avaliação;
* alterar interesse;
* alterar picância;
* alterar tags;
* editar metadados.

Essa responsabilidade pertence à Biblioteca.

---

## Configurações

O Dashboard não deve:

* editar arquivos .env;
* configurar banco;
* configurar APIs;
* alterar diretórios;
* modificar parâmetros técnicos.

---

## Diagnóstico Avançado

Logs detalhados, stack traces, histórico de tarefas e informações técnicas pertencem ao módulo Configurações.

---

## Administração

O Dashboard não deve conter funcionalidades administrativas como:

* limpeza do banco;
* recriação de índices;
* migrações;
* importações em massa;
* manutenção interna.

---

# 6. Glossário

Este glossário estabelece uma linguagem única para toda a Manhwateca, evitando ambiguidades entre documentação, desenvolvimento e operação.

---

## Biblioteca

Conjunto de pastas contendo as obras armazenadas localmente.

É a fonte física dos arquivos.

---

## Obra

Unidade principal do catálogo.

Pode representar:

* Manhwa;
* Manga;
* Novel;
* Web Novel;
* Danmei;
* HQ.

---

## Capítulo

Menor unidade de leitura pertencente a uma obra.

---

## Catálogo

Base de dados local contendo todas as informações conhecidas sobre as obras.

O catálogo é armazenado no PostgreSQL.

---

## Catalogação

Processo de leitura da biblioteca física para atualizar o catálogo local.

Não consulta serviços externos.

---

## Organização

Processo responsável por validar e corrigir a estrutura física da biblioteca.

Inclui:

* nomes;
* pastas;
* capítulos;
* organização.

---

## Workflow

Sequência oficial de etapas executadas pela Manhwateca.

Atualmente composto por:

1. Organizar biblioteca
2. Catalogar arquivos
3. Resolver IDs
4. Atualizar metadados
5. Sincronizar Notion

---

## Próximo Passo Recomendado

Ação calculada automaticamente pelo sistema como sendo a mais importante naquele momento.

Existe apenas um por vez.

---

## Pendência

Qualquer situação que exige intervenção do usuário.

Exemplos:

* obra sem ID;
* novos capítulos;
* sincronização pendente.

---

## Bloqueio

Condição que impede a execução da próxima etapa do Workflow.

Exemplos:

* banco indisponível;
* biblioteca inacessível;
* IDs pendentes.

---

## ID

Identificador único de uma obra no MangaUpdates.

É utilizado para buscar metadados oficiais.

---

## Metadados

Informações complementares da obra.

Exemplos:

* autores;
* artistas;
* gêneros;
* categorias;
* status;
* descrição;
* capa.

---

## Catálogo Enriquecido

Catálogo local após receber metadados provenientes do MangaUpdates.

---

## Sincronização

Processo de atualização do Notion utilizando o catálogo local como fonte de verdade.

---

## Simulação

Execução que calcula todas as alterações sem modificar dados externos.

É obrigatória antes de qualquer sincronização com o Notion.

---

## Task

Processo assíncrono responsável pela execução de operações demoradas.

Exemplos:

* catalogação;
* atualização de metadados;
* sincronização.

---

## Ambiente

Conjunto de recursos necessários para funcionamento da Manhwateca.

Inclui:

* PostgreSQL;
* diretórios;
* APIs;
* arquivos de configuração.

---

## Dashboard

Tela inicial da aplicação responsável por consolidar indicadores, apresentar pendências e orientar o usuário para a próxima ação recomendada.

Não executa processos complexos; apenas informa e direciona.

 
# Dashboard
## User Story + Regras de Negócio
 
7. User Stories
    # US-001 — Visualizar o estado geral da biblioteca
    # US-002 — Receber a próxima ação recomendada
    # US-003 — Visualizar métricas operacionais
    # US-004 — Consultar pendências críticas
    # US-005 — Acessar ações rápidas
    # US-006 — Acompanhar o progresso do Workflow
    # US-007 — Consultar o estado das integrações
    # US-008 — Atualizar os dados do Dashboard
    # US-009 — Navegar para os módulos especializados

