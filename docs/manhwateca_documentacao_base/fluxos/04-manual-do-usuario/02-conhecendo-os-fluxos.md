# Conhecendo os Fluxos

> Documento: **02-conhecendo-os-fluxos.md**

---

# Objetivo

Este capítulo apresenta todos os elementos da interface da página **Fluxos**, explicando a função de cada área, como interpretar as informações exibidas e como interagir com elas durante uma execução do Workflow.

Ao final da leitura, você será capaz de identificar rapidamente onde cada informação está localizada e compreender o papel de cada componente da tela.

---

# Visão Geral da Página

A página **Fluxos** foi organizada para acompanhar todo o ciclo de processamento da biblioteca.

Cada área possui uma responsabilidade específica.

A estrutura geral é semelhante ao exemplo abaixo.

```text
┌──────────────────────────────────────────────────────────────┐
│ Cabeçalho                                                    │
├──────────────────────────────────────────────────────────────┤
│ Barra de Progresso Global                                    │
├──────────────────────────────────────────────────────────────┤
│ Workflow                                                     │
│                                                              │
│ ① Organizar Biblioteca                                       │
│ ② Catalogar Obras                                            │
│ ③ Resolver IDs                                               │
│ ④ Atualizar Metadados                                        │
│ ⑤ Sincronizar Notion                                         │
├──────────────────────────────────────────────────────────────┤
│ Painel de Execução                                           │
├──────────────────────────────────────────────────────────────┤
│ Resumo da Execução                                           │
└──────────────────────────────────────────────────────────────┘
```

Durante uma execução, essas áreas são atualizadas automaticamente.

---

# Cabeçalho

O cabeçalho apresenta as principais informações da página.

Normalmente você encontrará:

* título da página;
* descrição do módulo;
* data e horário da última execução;
* botão **Executar Workflow**;
* botão **Cancelar Workflow** (quando houver processamento em andamento).

É também pelo cabeçalho que uma nova execução é iniciada.

---

# Barra de Progresso Global

Logo abaixo do cabeçalho encontra-se a barra de progresso geral.

Ela informa:

* percentual concluído;
* etapa atual;
* quantidade de etapas finalizadas.

Exemplo:

```text
Workflow

████████░░░░░░░░░░

40%

Etapa 2 de 5
```

Essa barra representa o progresso do Workflow completo e não de uma etapa específica.

---

# Área do Workflow

Esta é a principal região da página.

Nela são exibidas as cinco etapas que compõem o processamento da biblioteca.

```text
① Organizar Biblioteca

② Catalogar Obras

③ Resolver IDs

④ Atualizar Metadados

⑤ Sincronizar Notion
```

Cada etapa possui seu próprio estado e pode exibir informações adicionais durante a execução.

---

# Cartões das Etapas

Cada etapa é apresentada em um cartão independente.

Em cada cartão você encontrará:

* nome da etapa;
* descrição resumida;
* estado atual;
* ações disponíveis;
* informações de progresso (quando aplicável).

Quando uma etapa estiver em execução, seu cartão será destacado em relação aos demais.

---

# Painel de Execução

Durante o processamento, a página exibe um painel com informações em tempo real.

Entre elas:

* etapa atual;
* obra em processamento;
* quantidade processada;
* percentual concluído;
* tempo decorrido.

Exemplo:

```text
Atualizando Metadados

Obra atual

Solo Leveling

248 de 731 obras

34%

Tempo: 02m18s
```

Essas informações mudam automaticamente conforme o Workflow avança.

---

# Resumo da Execução

Quando o Workflow termina, um resumo é exibido na parte inferior da página.

Ele reúne os principais resultados da execução.

Exemplo:

```text
Workflow concluído

684 obras analisadas

31 IDs resolvidos

612 metadados atualizados

598 sincronizações

3 alertas
```

Esse resumo permanece disponível até que uma nova execução seja iniciada.

---

# Estados das Etapas

Cada etapa pode apresentar diferentes estados.

Os mais comuns são:

| Estado                | Significado                    |
| --------------------- | ------------------------------ |
| Aguardando            | Ainda não iniciada             |
| Em execução           | Está sendo processada          |
| Concluída             | Finalizada com sucesso         |
| Concluída com alertas | Finalizada, mas requer atenção |
| Falhou                | Não pôde ser concluída         |
| Cancelada             | Interrompida pelo usuário      |

O estado de cada etapa é atualizado automaticamente.

---

# Mensagens e Alertas

Durante o processamento, a página poderá apresentar mensagens informativas.

Exemplos:

* início de uma etapa;
* conclusão de uma operação;
* identificação de pendências;
* indisponibilidade de uma integração.

Sempre leia essas mensagens antes de iniciar uma nova execução.

> **Importante**
>
> Um alerta não significa necessariamente que o Workflow falhou. Muitas vezes ele apenas informa que determinadas obras precisarão de revisão posterior.

---

# Acompanhando uma Execução

Quando o Workflow estiver em andamento:

* acompanhe a barra de progresso;
* observe qual etapa está destacada;
* consulte o painel de execução para verificar a obra atualmente processada;
* leia as mensagens exibidas durante a execução.

Você não precisa atualizar a página manualmente.

---

# Navegação Durante o Processamento

Mesmo durante uma execução é possível navegar para outros módulos da Manhwateca.

Ao retornar para **Fluxos**, a página recuperará automaticamente:

* a etapa atual;
* o progresso;
* as mensagens recentes;
* o estado das integrações.

Isso permite acompanhar o Workflow sem interromper o processamento.

---

# Boas Práticas

Para obter os melhores resultados durante o uso da página:

* execute o Workflow completo após grandes alterações na biblioteca;
* acompanhe os alertas exibidos ao final da execução;
* reexecute apenas etapas específicas quando necessário;
* evite iniciar uma nova execução enquanto outra ainda estiver em andamento.

Essas práticas ajudam a manter a biblioteca consistente e reduzem o tempo gasto com reprocessamentos.

---

# Próximo passo

Agora que você conhece toda a interface da página **Fluxos**, o próximo capítulo explicará a primeira etapa do Workflow: **Organizar Biblioteca**, responsável por preparar sua coleção para as etapas seguintes.

---

# Conclusão

A página **Fluxos** foi projetada para oferecer uma visão clara de todo o processamento da biblioteca. Compreender a função de cada área da interface facilita o acompanhamento do Workflow, a interpretação dos resultados e a identificação rápida de eventuais problemas durante a execução.
