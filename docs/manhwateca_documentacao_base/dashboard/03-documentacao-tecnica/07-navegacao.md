# Dashboard — Documentação Técnica

## 07 - Navegação

---

# Objetivo

Este documento define a arquitetura de navegação do módulo **Dashboard**, os fluxos entre módulos da Manhwateca, o gerenciamento do estado durante a navegação e as responsabilidades do Frontend e Backend.

O Dashboard atua como o **hub de navegação** da aplicação. Seu papel é orientar o usuário para o módulo correto, preservando o contexto e evitando navegação desnecessária.

---

# Objetivos da Navegação

A navegação do Dashboard foi projetada com os seguintes objetivos:

* minimizar o número de cliques;
* direcionar o usuário para a próxima ação relevante;
* manter o contexto entre módulos;
* evitar navegação circular;
* permitir retorno rápido ao Dashboard.

---

# Mapa de Navegação

O Dashboard é o ponto central da aplicação.

```text
                      Dashboard
                           │
      ┌─────────────┬──────┼──────────────┬──────────────┐
      ▼             ▼      ▼              ▼              ▼
 Biblioteca      Fluxos Configurações   Notion      Relatórios
      │             │
      └─────────────┴───────────────┐
                                    ▼
                               Dashboard
```

Nenhum módulo depende diretamente de outro módulo para navegação.

Sempre que possível, o retorno deve ocorrer para o Dashboard.

---

# Estrutura de Rotas

As rotas devem permanecer estáveis.

| Módulo        | Rota             |
| ------------- | ---------------- |
| Dashboard     | `/dashboard`     |
| Biblioteca    | `/biblioteca`    |
| Fluxos        | `/fluxos`        |
| Configurações | `/configuracoes` |
| Relatórios    | `/relatorios`    |

As rotas representam módulos completos.

Não devem existir URLs diferentes para componentes internos do Dashboard.

---

# Navegação por Ação Recomendada

O componente **NextActionCard** possui prioridade máxima.

Fluxo:

```text
Dashboard

↓

NextAction

↓

Fluxos

↓

Execução da atividade

↓

Dashboard
```

O Dashboard nunca executa a ação.

Ele apenas direciona.

---

# Navegação pelas Pendências

Cada pendência possui um destino.

Exemplo:

```text
Resolver IDs

↓

/fluxos#resolver-ids
```

```text
Configurar Notion

↓

/configuracoes#notion
```

A regra é simples:

Cada pendência conhece exatamente um destino.

---

# Navegação pelas Ações Rápidas

As Ações Rápidas representam atalhos.

| Botão         | Destino           |
| ------------- | ----------------- |
| Biblioteca    | `/biblioteca`     |
| Fluxos        | `/fluxos`         |
| Configurações | `/configuracoes`  |
| Recarregar    | Atualização local |

Nenhuma delas executa lógica de negócio.

---

# Navegação do Workflow

Cada etapa do Workflow deve permitir acesso direto ao módulo Fluxos.

```text
Workflow

↓

Resolver IDs

↓

Fluxos

↓

Resolver IDs
```

O Dashboard não conhece como a etapa será executada.

---

# Navegação Contextual

Quando possível, a navegação deve preservar contexto.

Exemplo:

```text
Dashboard

↓

Fluxos

↓

#resolver-ids
```

Em vez de:

```text
Fluxos

↓

Tela inicial
```

Essa estratégia reduz cliques e melhora a produtividade.

---

# Persistência de Contexto

Ao navegar entre módulos, o Frontend deve preservar:

* última atualização do Dashboard;
* filtros globais (quando existirem);
* posição de rolagem (opcional);
* estado de expansão de painéis (opcional).

Não devem ser preservados:

* estados temporários de loading;
* mensagens transitórias;
* erros já resolvidos.

---

# Retorno ao Dashboard

Após concluir qualquer operação, recomenda-se retornar ao Dashboard.

Fluxo esperado:

```text
Dashboard

↓

Fluxos

↓

Execução

↓

Dashboard

↓

Refresh
```

O retorno pode ser manual ou automático, conforme a funcionalidade.

---

# Deep Links

Os módulos podem expor âncoras internas.

Exemplo:

```text
/fluxos#resolver-ids

/configuracoes#notion

/configuracoes#database
```

Essas âncoras permitem que o Dashboard direcione o usuário exatamente para a área relevante.

---

# Histórico de Navegação

O navegador deve manter o histórico normalmente.

Fluxo:

```text
Dashboard

↓

Biblioteca

↓

Voltar

↓

Dashboard
```

Evitar redirecionamentos que removam entradas do histórico.

---

# Estratégia de Refresh

Ao retornar ao Dashboard:

1. restaurar a interface imediatamente;
2. manter dados anteriores;
3. iniciar atualização em segundo plano;
4. substituir o ViewModel apenas após sucesso.

Fluxo:

```text
Dashboard

↓

Fluxos

↓

Voltar

↓

Dashboard antigo

↓

Refreshing

↓

Dashboard atualizado
```

Essa abordagem evita telas vazias.

---

# Navegação durante Erros

Se um módulo não puder ser aberto:

* permanecer no Dashboard;
* exibir mensagem amigável;
* registrar log;
* permitir nova tentativa.

Nunca navegar para páginas de erro genéricas.

---

# Responsabilidade do Backend

O Backend é responsável por fornecer os destinos de navegação quando eles dependem das regras de negócio.

Exemplo:

```json
{
  "action": "/fluxos#resolver-ids"
}
```

O Frontend não deve decidir dinamicamente qual etapa do Workflow abrir.

---

# Responsabilidade do Frontend

O Frontend é responsável por:

* interpretar rotas;
* executar a navegação;
* preservar estado local;
* destacar o módulo ativo;
* iniciar atualização ao retornar.

Nunca calcular destinos.

---

# Diagrama de Navegação

```text
                 Dashboard
                      │
      ┌───────────────┼─────────────────┐
      ▼               ▼                 ▼
 Biblioteca       Fluxos        Configurações
      │               │                 │
      └───────────────┼─────────────────┘
                      ▼
                 Dashboard
```

O Dashboard permanece como centro da experiência.

---

# Regras Arquiteturais

A navegação deve obedecer às seguintes regras:

* nenhuma regra de negócio na camada de roteamento;
* URLs estáveis e previsíveis;
* destinos definidos pelo Backend quando dependentes do Workflow;
* suporte a deep links;
* preservação do histórico do navegador;
* atualização automática ao retornar de operações críticas.

---

# Casos de Uso

## Caso 1 — Resolver IDs

```text
Dashboard

↓

Próxima ação

↓

Fluxos#resolver-ids

↓

Resolver IDs

↓

Dashboard

↓

Refresh
```

---

## Caso 2 — Corrigir Integração

```text
Dashboard

↓

Integrações

↓

Configurações#notion

↓

Salvar

↓

Dashboard
```

---

## Caso 3 — Consultar Biblioteca

```text
Dashboard

↓

Biblioteca

↓

Visualizar obra

↓

Dashboard
```

---

# Checklist

Antes da implementação, verificar:

| Item                              | Obrigatório |
| --------------------------------- | ----------- |
| Rotas centralizadas               | ✅           |
| Deep links suportados             | ✅           |
| Histórico preservado              | ✅           |
| Refresh ao retornar               | ✅           |
| Destinos definidos pelo Backend   | ✅           |
| Sem lógica de negócio no roteador | ✅           |

---

# Relação com outros documentos

| Documento           | Conteúdo relacionado                      |
| ------------------- | ----------------------------------------- |
| 03-api-dashboard.md | Campo `action` do contrato da API         |
| 05-componentes.md   | Componentes que iniciam navegação         |
| 06-estados.md       | Atualização da interface após retorno     |
| 08-atualizacao.md   | Estratégias de revalidação após navegação |

---

# Conclusão

A navegação do Dashboard foi projetada para ser **orientada por contexto**, com o Dashboard atuando como ponto central da experiência do usuário. O Backend define os destinos quando dependem das regras de negócio, enquanto o Frontend é responsável apenas pela execução da navegação e pela preservação do estado da interface. Essa separação reduz o acoplamento, simplifica a evolução do sistema e garante uma experiência consistente entre os diferentes módulos da Manhwateca.
