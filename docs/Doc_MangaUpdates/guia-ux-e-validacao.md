# Guia de UX e validacao para telas MangaUpdates

Este guia registra as decisoes que devem orientar as proximas telas do fluxo MangaUpdates para evitar retrabalho e implementacoes desalinhadas.

## Principios de tela

- Existe apenas um protagonista por tela.
- Existe apenas uma acao principal por tela.
- A fila representa trabalho, nao navegacao.
- A experiencia deve lembrar uma fila de revisao, como Gmail, GitHub Issues ou Jira Queue.
- Evitar CRUD, painel administrativo, grade de dados ou excesso de informacao.
- Os candidatos representam a decisao principal.
- Usar espaco em branco como hierarquia visual.
- Informacoes secundarias devem ter baixo contraste.
- Em caso de duvida entre mostrar mais informacao ou simplificar, simplificar.

## Padrao visual

- Titulos internos de pagina: no maximo 32px, peso 700, cor `#2E262A`.
- Textos secundarios: 13px a 14px, peso 500, cor `#7A6F74`.
- Rose `#A44D69` deve destacar selecao ou CTA principal.
- O primeiro candidato recomendado pode ter selo e icone, mas o contorno rose deve indicar item selecionado.
- Botoes secundarios devem ser discretos.
- O botao "Salvar decisao" deve ser o unico CTA dominante.
- Itens da fila devem ser compactos, com altura aproximada entre 44px e 56px.

## Contrato de candidatos

- Exibir apenas candidatos com correspondencia acima de 64%.
- Ordenar sempre por maior correspondencia primeiro.
- Remover duplicados antes de renderizar.
- Exibir no maximo 5 candidatos por obra.
- Nao aplicar filtros nao especificados pela regra de negocio, como tipo, genero ou categoria, sem aprovacao explicita.

## Checklist antes de implementar

1. Confirmar o comportamento na documentacao da tela.
2. Validar a origem dos dados no banco ou no payload real da API.
3. Escrever ou ajustar teste para a transformacao de dados.
4. Implementar a UI consumindo o contrato oficial.
5. Conferir que a UI nao cria regra de negocio divergente do backend.
6. Validar visualmente que a tela tem um protagonista e uma acao principal.
7. Rodar `node --check` nos arquivos JS alterados.
8. Rodar testes especificos da area modificada.
9. Conferir que nenhum arquivo ultrapassou 250 linhas sem justificativa.

## Regra de diagnostico

Antes de corrigir a tela por tentativa visual, seguir esta ordem:

```text
Banco de dados
↓
Endpoint/API
↓
Transformacao do payload
↓
Estado local da UI
↓
Renderizacao
```

Se o erro estiver no payload, corrigir no backend. Se estiver apenas na apresentacao, corrigir no componente. Nao misturar as duas coisas no mesmo ajuste sem necessidade.
