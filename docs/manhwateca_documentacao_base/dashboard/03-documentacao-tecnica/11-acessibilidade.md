# Dashboard — Documentação Técnica

## 11 - Acessibilidade

---

# Objetivo

Este documento define os requisitos de acessibilidade (Accessibility / A11y) para o módulo **Dashboard** da Manhwateca.

O objetivo é garantir que a interface seja utilizável por qualquer usuário, independentemente de limitações físicas, cognitivas ou tecnológicas, seguindo as recomendações da **WCAG 2.2 AA**, das especificações **WAI-ARIA** e das boas práticas de HTML semântico.

Os requisitos aqui descritos são obrigatórios para todos os componentes do Dashboard.

---

# Objetivos de Engenharia

A implementação deve garantir que o Dashboard seja:

* navegável exclusivamente pelo teclado;
* compatível com leitores de tela;
* utilizável sem depender exclusivamente de cores;
* semanticamente correto;
* responsivo;
* previsível.

---

# Normas Adotadas

A implementação deve seguir:

| Norma           | Nível       |
| --------------- | ----------- |
| WCAG 2.2        | AA          |
| WAI-ARIA 1.2    | Obrigatório |
| HTML5 Semântico | Obrigatório |

---

# Estrutura Semântica da Página

O Dashboard deve utilizar landmarks HTML.

```html
<body>

<header>
</header>

<nav>
</nav>

<main>

<section>

<section>

<section>

</main>

<footer>

</footer>
```

Evitar `<div>` quando existir um elemento semântico equivalente.

---

# Hierarquia de Títulos

A página deve possuir apenas um `<h1>`.

Exemplo:

```html
<h1>Dashboard</h1>

<h2>Próximo Passo</h2>

<h2>Métricas</h2>

<h2>Pendências</h2>

<h2>Integrações</h2>

<h2>Workflow</h2>

<h2>Ações Rápidas</h2>
```

Nunca utilizar níveis de título para fins exclusivamente visuais.

---

# Navegação por Teclado

Todos os elementos interativos devem ser acessíveis via teclado.

Sequência esperada:

```text
Tab

↓

Botão Recarregar

↓

Botão Próxima Ação

↓

Pendências

↓

Workflow

↓

Ações Rápidas
```

Não deve existir nenhum elemento inacessível por teclado.

---

# Ordem do Foco

A ordem do foco deve seguir a disposição visual da página.

Nunca alterar artificialmente a sequência utilizando `tabindex` positivo.

Utilizar apenas:

```html
tabindex="0"
```

quando necessário.

---

# Indicador Visual de Foco

Todo elemento interativo deve possuir foco visível.

Exemplo CSS:

```css
:focus-visible{
    outline:2px solid #2563eb;
    outline-offset:2px;
}
```

Nunca remover:

```css
outline:none;
```

sem fornecer alternativa equivalente.

---

# Botões

Todos os botões devem possuir texto acessível.

Correto:

```html
<button>

Recarregar Dashboard

</button>
```

Quando utilizar apenas ícones:

```html
<button
aria-label="Recarregar Dashboard">
```

---

# Ícones

Ícones decorativos:

```html
aria-hidden="true"
```

Ícones com significado:

```html
role="img"

aria-label="Integração operacional"
```

---

# Cards

Cada card deve ser anunciado corretamente pelo leitor de tela.

Exemplo:

```html
<section
aria-labelledby="metric-library">

<h2 id="metric-library">

Biblioteca

</h2>

...
```

---

# Métricas

Os valores devem ser lidos juntamente com seus rótulos.

Exemplo esperado:

> Biblioteca: 347 obras

Não:

> 347

sozinho.

---

# Pendências

Cada pendência deve possuir estrutura navegável.

Exemplo:

```html
<article>

<h3>

Resolver IDs

</h3>

<p>

Existem oito obras...

</p>

<button>

Abrir Fluxos

</button>

</article>
```

---

# Workflow

Cada etapa deve informar seu estado.

Exemplo:

```html
<li
aria-current="step">
```

ou

```html
aria-label="Etapa concluída"
```

Leitores de tela devem conseguir identificar:

* etapa atual;
* etapas concluídas;
* etapas pendentes.

---

# Integrações

Nunca utilizar apenas cores.

Exemplo incorreto:

```text
🟢
```

Exemplo correto:

```text
🟢 PostgreSQL

Operacional
```

O texto é obrigatório.

---

# Mensagens Dinâmicas

Atualizações devem utilizar regiões ARIA.

Exemplo:

```html
<div
aria-live="polite">
```

Utilizar para:

* atualização concluída;
* erro de carregamento;
* sucesso no refresh.

Nunca utilizar:

```html
aria-live="assertive"
```

para mensagens informativas.

---

# Skeleton Loading

Durante o carregamento:

```html
aria-busy="true"
```

Após carregamento:

```html
aria-busy="false"
```

---

# Contraste

Todos os textos devem respeitar WCAG AA.

| Elemento       | Contraste mínimo |
| -------------- | ---------------- |
| Texto normal   | 4.5:1            |
| Texto grande   | 3:1              |
| Componentes UI | 3:1              |

---

# Cores

Nenhuma informação pode depender exclusivamente da cor.

Exemplo incorreto:

```text
🔴
```

Exemplo correto:

```text
🔴

Erro
```

---

# Responsividade

O Dashboard deve permanecer funcional em:

* desktop;
* notebook;
* tablet;
* telas menores.

Mesmo em layouts responsivos:

* foco preservado;
* landmarks preservados;
* ordem lógica preservada.

---

# Tabelas

Caso futuramente sejam adicionadas:

```html
<table>

<thead>

<tbody>
```

Nunca utilizar tabelas para layout.

---

# Links

Todo link deve possuir descrição clara.

Evitar:

```text
Clique aqui
```

Preferir:

```text
Abrir módulo Fluxos
```

---

# Formulários

Embora o Dashboard possua poucos campos editáveis, qualquer entrada futura deve possuir:

```html
<label>

<input>

aria-describedby
```

Nunca depender apenas de placeholders.

---

# Erros

Mensagens de erro devem:

* explicar o problema;
* indicar ação recomendada;
* permanecer acessíveis.

Exemplo:

```html
role="alert"
```

apenas para erros importantes.

---

# Compatibilidade

O Dashboard deve ser compatível com:

* NVDA
* JAWS
* VoiceOver
* Narrador do Windows

A implementação não deve depender de um leitor específico.

---

# Testes de Acessibilidade

Antes da entrega, validar:

* navegação apenas por teclado;
* foco visível;
* contraste;
* HTML semântico;
* ARIA;
* leitura correta pelo VoiceOver/NVDA.

Ferramentas recomendadas:

* Lighthouse
* axe DevTools
* WAVE
* Accessibility Insights

---

# Anti-patterns

São proibidos:

* remover outline do foco;
* utilizar apenas cor para transmitir informação;
* imagens sem texto alternativo;
* botões sem nome acessível;
* landmarks duplicados;
* ordem de foco diferente da ordem visual;
* uso excessivo de `aria-*` quando HTML semântico resolve o problema.

---

# Checklist

| Item                                 | Obrigatório |
| ------------------------------------ | ----------- |
| HTML semântico                       | ✅           |
| Landmarks                            | ✅           |
| Navegação por teclado                | ✅           |
| Foco visível                         | ✅           |
| ARIA apenas quando necessário        | ✅           |
| Contraste WCAG AA                    | ✅           |
| Compatibilidade com leitores de tela | ✅           |
| Sem dependência exclusiva de cor     | ✅           |

---

# Relação com outros documentos

| Documento         | Conteúdo relacionado                               |
| ----------------- | -------------------------------------------------- |
| 05-componentes.md | Estrutura dos componentes                          |
| 06-estados.md     | Estados acessíveis da interface                    |
| 07-navegacao.md   | Fluxo de navegação por teclado                     |
| 12-testes.md      | Testes automatizados e validação de acessibilidade |

---

# Conclusão

A acessibilidade do Dashboard deve ser tratada como um requisito funcional e não como uma melhoria opcional. A combinação de HTML semântico, suporte completo à navegação por teclado, uso adequado de WAI-ARIA e conformidade com WCAG 2.2 AA garante uma interface mais robusta, inclusiva e fácil de manter. Além de beneficiar usuários que utilizam tecnologias assistivas, essas práticas melhoram a qualidade geral do código, a consistência da interface e a experiência de uso para todos os usuários.
