# 03 — Aplicar Decisões — Documento de Produto

> Especificação funcional e de experiência do usuário.

Este documento descreve **o comportamento esperado da tela**, o valor entregue ao usuário, a percepção desejada da interface e os critérios de sucesso do fluxo.

# 1. Propósito da Tela


A tela **Aplicar Decisões** é a etapa de confirmação do fluxo MangaUpdates.

Toda a análise aconteceu anteriormente.

Nesta tela o usuário **não decide** qual ID utilizar.

Ele apenas confirma que as decisões revisadas podem ser persistidas.

## Objetivos

- transmitir confiança;
- reduzir ansiedade;
- eliminar dúvidas antes da gravação;
- tornar a confirmação rápida.


# 2. Princípios de Produto


1. Uma única ação principal.
2. Uma única pergunta: *"Está tudo pronto para gravar?"*
3. O usuário deve gastar menos tempo confirmando do que revisando.
4. O sistema deve impedir aplicações inseguras.
5. O fluxo deve incentivar continuidade.


# 3. Jornada do Usuário


```text
Buscar candidatos
      ↓
Revisar pendências
      ↓
Aplicar decisões
      ↓
Atualizar metadados
      ↓
Sincronizar Notion
```

Ao chegar nesta etapa, a percepção deve ser de **conclusão**, não de trabalho pendente.


# 4. Perguntas Respondidas pela Tela


Em até dois segundos o usuário deve saber:

- Quantas decisões serão aplicadas?
- Há conflitos?
- Existe algum bloqueio?
- Posso aplicar agora?
- O que acontecerá após clicar no botão principal?


# 5. Estados Funcionais


## Tudo pronto
Resumo positivo e CTA habilitado.

## Existem bloqueios
Resumo evidencia quantidade e motivo.
O CTA principal fica indisponível ou substituído por "Resolver bloqueios".

## Não existem decisões
Mensagem orientativa e CTA para retornar à revisão.

## Aplicação em andamento
Mostrar progresso e impedir dupla execução.

## Concluído
Resumo da execução com sucessos e falhas.


# 6. Objetivo Perceptivo


A interface deve transmitir:

- confiança;
- clareza;
- previsibilidade;
- sensação de encerramento da etapa.

Nunca deve transmitir:

- necessidade de investigação;
- excesso de leitura;
- aparência de planilha;
- sensação de risco.


# 7. Critérios de UX


- Existe apenas um CTA dominante.
- O resumo ocupa maior destaque que a lista.
- A lista serve como conferência.
- O usuário não precisa abrir detalhes para confirmar o lote.
- Os conflitos são autoexplicativos.


# 8. Casos de Uso


### Caso 1
Todas as decisões válidas → Aplicar → Sucesso.

### Caso 2
Existem bloqueios → Corrigir → Retornar.

### Caso 3
Job falha parcialmente → Exibir relatório → Reprocessar apenas bloqueados.


# 9. Critérios de Aceite


- Estado do lote compreendido em até 2 segundos.
- Aplicação iniciada por um único CTA.
- Não existe caminho para gravar decisões inválidas.
- Resultado final informa claramente sucesso e falhas.


# 10. Evoluções Futuras


- Dry-run visual.
- Histórico de aplicações.
- Exportação do relatório.
- Filtros por origem.
- Comparação entre execução anterior e atual.


# Anexo A.1 — Diretriz de Produto


### Objetivo

Detalhar uma expectativa de comportamento do fluxo.

### Diretriz

- Priorizar simplicidade sobre quantidade de informação.
- Evitar decisões adicionais nesta etapa.
- Toda mensagem deve orientar a próxima ação.
- Feedbacks devem ser objetivos e consistentes.

### Exemplo

Quando houver conflitos, a interface deve explicar o motivo e indicar claramente
que o usuário precisa retornar para a etapa **Revisar pendências** antes de prosseguir.

### Critério

Se o usuário precisar interpretar tecnicamente um erro para decidir o próximo passo,
a experiência deve ser considerada inadequada.


# Anexo A.2 — Diretriz de Produto


### Objetivo

Detalhar uma expectativa de comportamento do fluxo.

### Diretriz

- Priorizar simplicidade sobre quantidade de informação.
- Evitar decisões adicionais nesta etapa.
- Toda mensagem deve orientar a próxima ação.
- Feedbacks devem ser objetivos e consistentes.

### Exemplo

Quando houver conflitos, a interface deve explicar o motivo e indicar claramente
que o usuário precisa retornar para a etapa **Revisar pendências** antes de prosseguir.

### Critério

Se o usuário precisar interpretar tecnicamente um erro para decidir o próximo passo,
a experiência deve ser considerada inadequada.


# Anexo A.3 — Diretriz de Produto


### Objetivo

Detalhar uma expectativa de comportamento do fluxo.

### Diretriz

- Priorizar simplicidade sobre quantidade de informação.
- Evitar decisões adicionais nesta etapa.
- Toda mensagem deve orientar a próxima ação.
- Feedbacks devem ser objetivos e consistentes.

### Exemplo

Quando houver conflitos, a interface deve explicar o motivo e indicar claramente
que o usuário precisa retornar para a etapa **Revisar pendências** antes de prosseguir.

### Critério

Se o usuário precisar interpretar tecnicamente um erro para decidir o próximo passo,
a experiência deve ser considerada inadequada.


# Anexo A.4 — Diretriz de Produto


### Objetivo

Detalhar uma expectativa de comportamento do fluxo.

### Diretriz

- Priorizar simplicidade sobre quantidade de informação.
- Evitar decisões adicionais nesta etapa.
- Toda mensagem deve orientar a próxima ação.
- Feedbacks devem ser objetivos e consistentes.

### Exemplo

Quando houver conflitos, a interface deve explicar o motivo e indicar claramente
que o usuário precisa retornar para a etapa **Revisar pendências** antes de prosseguir.

### Critério

Se o usuário precisar interpretar tecnicamente um erro para decidir o próximo passo,
a experiência deve ser considerada inadequada.


# Anexo A.5 — Diretriz de Produto


### Objetivo

Detalhar uma expectativa de comportamento do fluxo.

### Diretriz

- Priorizar simplicidade sobre quantidade de informação.
- Evitar decisões adicionais nesta etapa.
- Toda mensagem deve orientar a próxima ação.
- Feedbacks devem ser objetivos e consistentes.

### Exemplo

Quando houver conflitos, a interface deve explicar o motivo e indicar claramente
que o usuário precisa retornar para a etapa **Revisar pendências** antes de prosseguir.

### Critério

Se o usuário precisar interpretar tecnicamente um erro para decidir o próximo passo,
a experiência deve ser considerada inadequada.


# Anexo A.6 — Diretriz de Produto


### Objetivo

Detalhar uma expectativa de comportamento do fluxo.

### Diretriz

- Priorizar simplicidade sobre quantidade de informação.
- Evitar decisões adicionais nesta etapa.
- Toda mensagem deve orientar a próxima ação.
- Feedbacks devem ser objetivos e consistentes.

### Exemplo

Quando houver conflitos, a interface deve explicar o motivo e indicar claramente
que o usuário precisa retornar para a etapa **Revisar pendências** antes de prosseguir.

### Critério

Se o usuário precisar interpretar tecnicamente um erro para decidir o próximo passo,
a experiência deve ser considerada inadequada.


# Anexo A.7 — Diretriz de Produto


### Objetivo

Detalhar uma expectativa de comportamento do fluxo.

### Diretriz

- Priorizar simplicidade sobre quantidade de informação.
- Evitar decisões adicionais nesta etapa.
- Toda mensagem deve orientar a próxima ação.
- Feedbacks devem ser objetivos e consistentes.

### Exemplo

Quando houver conflitos, a interface deve explicar o motivo e indicar claramente
que o usuário precisa retornar para a etapa **Revisar pendências** antes de prosseguir.

### Critério

Se o usuário precisar interpretar tecnicamente um erro para decidir o próximo passo,
a experiência deve ser considerada inadequada.


# Anexo A.8 — Diretriz de Produto


### Objetivo

Detalhar uma expectativa de comportamento do fluxo.

### Diretriz

- Priorizar simplicidade sobre quantidade de informação.
- Evitar decisões adicionais nesta etapa.
- Toda mensagem deve orientar a próxima ação.
- Feedbacks devem ser objetivos e consistentes.

### Exemplo

Quando houver conflitos, a interface deve explicar o motivo e indicar claramente
que o usuário precisa retornar para a etapa **Revisar pendências** antes de prosseguir.

### Critério

Se o usuário precisar interpretar tecnicamente um erro para decidir o próximo passo,
a experiência deve ser considerada inadequada.


# Anexo A.9 — Diretriz de Produto


### Objetivo

Detalhar uma expectativa de comportamento do fluxo.

### Diretriz

- Priorizar simplicidade sobre quantidade de informação.
- Evitar decisões adicionais nesta etapa.
- Toda mensagem deve orientar a próxima ação.
- Feedbacks devem ser objetivos e consistentes.

### Exemplo

Quando houver conflitos, a interface deve explicar o motivo e indicar claramente
que o usuário precisa retornar para a etapa **Revisar pendências** antes de prosseguir.

### Critério

Se o usuário precisar interpretar tecnicamente um erro para decidir o próximo passo,
a experiência deve ser considerada inadequada.


# Anexo A.10 — Diretriz de Produto


### Objetivo

Detalhar uma expectativa de comportamento do fluxo.

### Diretriz

- Priorizar simplicidade sobre quantidade de informação.
- Evitar decisões adicionais nesta etapa.
- Toda mensagem deve orientar a próxima ação.
- Feedbacks devem ser objetivos e consistentes.

### Exemplo

Quando houver conflitos, a interface deve explicar o motivo e indicar claramente
que o usuário precisa retornar para a etapa **Revisar pendências** antes de prosseguir.

### Critério

Se o usuário precisar interpretar tecnicamente um erro para decidir o próximo passo,
a experiência deve ser considerada inadequada.


# Anexo A.11 — Diretriz de Produto


### Objetivo

Detalhar uma expectativa de comportamento do fluxo.

### Diretriz

- Priorizar simplicidade sobre quantidade de informação.
- Evitar decisões adicionais nesta etapa.
- Toda mensagem deve orientar a próxima ação.
- Feedbacks devem ser objetivos e consistentes.

### Exemplo

Quando houver conflitos, a interface deve explicar o motivo e indicar claramente
que o usuário precisa retornar para a etapa **Revisar pendências** antes de prosseguir.

### Critério

Se o usuário precisar interpretar tecnicamente um erro para decidir o próximo passo,
a experiência deve ser considerada inadequada.


# Anexo A.12 — Diretriz de Produto


### Objetivo

Detalhar uma expectativa de comportamento do fluxo.

### Diretriz

- Priorizar simplicidade sobre quantidade de informação.
- Evitar decisões adicionais nesta etapa.
- Toda mensagem deve orientar a próxima ação.
- Feedbacks devem ser objetivos e consistentes.

### Exemplo

Quando houver conflitos, a interface deve explicar o motivo e indicar claramente
que o usuário precisa retornar para a etapa **Revisar pendências** antes de prosseguir.

### Critério

Se o usuário precisar interpretar tecnicamente um erro para decidir o próximo passo,
a experiência deve ser considerada inadequada.


# Anexo A.13 — Diretriz de Produto


### Objetivo

Detalhar uma expectativa de comportamento do fluxo.

### Diretriz

- Priorizar simplicidade sobre quantidade de informação.
- Evitar decisões adicionais nesta etapa.
- Toda mensagem deve orientar a próxima ação.
- Feedbacks devem ser objetivos e consistentes.

### Exemplo

Quando houver conflitos, a interface deve explicar o motivo e indicar claramente
que o usuário precisa retornar para a etapa **Revisar pendências** antes de prosseguir.

### Critério

Se o usuário precisar interpretar tecnicamente um erro para decidir o próximo passo,
a experiência deve ser considerada inadequada.


# Anexo A.14 — Diretriz de Produto


### Objetivo

Detalhar uma expectativa de comportamento do fluxo.

### Diretriz

- Priorizar simplicidade sobre quantidade de informação.
- Evitar decisões adicionais nesta etapa.
- Toda mensagem deve orientar a próxima ação.
- Feedbacks devem ser objetivos e consistentes.

### Exemplo

Quando houver conflitos, a interface deve explicar o motivo e indicar claramente
que o usuário precisa retornar para a etapa **Revisar pendências** antes de prosseguir.

### Critério

Se o usuário precisar interpretar tecnicamente um erro para decidir o próximo passo,
a experiência deve ser considerada inadequada.


# Anexo A.15 — Diretriz de Produto


### Objetivo

Detalhar uma expectativa de comportamento do fluxo.

### Diretriz

- Priorizar simplicidade sobre quantidade de informação.
- Evitar decisões adicionais nesta etapa.
- Toda mensagem deve orientar a próxima ação.
- Feedbacks devem ser objetivos e consistentes.

### Exemplo

Quando houver conflitos, a interface deve explicar o motivo e indicar claramente
que o usuário precisa retornar para a etapa **Revisar pendências** antes de prosseguir.

### Critério

Se o usuário precisar interpretar tecnicamente um erro para decidir o próximo passo,
a experiência deve ser considerada inadequada.


# Anexo A.16 — Diretriz de Produto


### Objetivo

Detalhar uma expectativa de comportamento do fluxo.

### Diretriz

- Priorizar simplicidade sobre quantidade de informação.
- Evitar decisões adicionais nesta etapa.
- Toda mensagem deve orientar a próxima ação.
- Feedbacks devem ser objetivos e consistentes.

### Exemplo

Quando houver conflitos, a interface deve explicar o motivo e indicar claramente
que o usuário precisa retornar para a etapa **Revisar pendências** antes de prosseguir.

### Critério

Se o usuário precisar interpretar tecnicamente um erro para decidir o próximo passo,
a experiência deve ser considerada inadequada.


# Anexo A.17 — Diretriz de Produto


### Objetivo

Detalhar uma expectativa de comportamento do fluxo.

### Diretriz

- Priorizar simplicidade sobre quantidade de informação.
- Evitar decisões adicionais nesta etapa.
- Toda mensagem deve orientar a próxima ação.
- Feedbacks devem ser objetivos e consistentes.

### Exemplo

Quando houver conflitos, a interface deve explicar o motivo e indicar claramente
que o usuário precisa retornar para a etapa **Revisar pendências** antes de prosseguir.

### Critério

Se o usuário precisar interpretar tecnicamente um erro para decidir o próximo passo,
a experiência deve ser considerada inadequada.


# Anexo A.18 — Diretriz de Produto


### Objetivo

Detalhar uma expectativa de comportamento do fluxo.

### Diretriz

- Priorizar simplicidade sobre quantidade de informação.
- Evitar decisões adicionais nesta etapa.
- Toda mensagem deve orientar a próxima ação.
- Feedbacks devem ser objetivos e consistentes.

### Exemplo

Quando houver conflitos, a interface deve explicar o motivo e indicar claramente
que o usuário precisa retornar para a etapa **Revisar pendências** antes de prosseguir.

### Critério

Se o usuário precisar interpretar tecnicamente um erro para decidir o próximo passo,
a experiência deve ser considerada inadequada.


# Anexo A.19 — Diretriz de Produto


### Objetivo

Detalhar uma expectativa de comportamento do fluxo.

### Diretriz

- Priorizar simplicidade sobre quantidade de informação.
- Evitar decisões adicionais nesta etapa.
- Toda mensagem deve orientar a próxima ação.
- Feedbacks devem ser objetivos e consistentes.

### Exemplo

Quando houver conflitos, a interface deve explicar o motivo e indicar claramente
que o usuário precisa retornar para a etapa **Revisar pendências** antes de prosseguir.

### Critério

Se o usuário precisar interpretar tecnicamente um erro para decidir o próximo passo,
a experiência deve ser considerada inadequada.


# Anexo A.20 — Diretriz de Produto


### Objetivo

Detalhar uma expectativa de comportamento do fluxo.

### Diretriz

- Priorizar simplicidade sobre quantidade de informação.
- Evitar decisões adicionais nesta etapa.
- Toda mensagem deve orientar a próxima ação.
- Feedbacks devem ser objetivos e consistentes.

### Exemplo

Quando houver conflitos, a interface deve explicar o motivo e indicar claramente
que o usuário precisa retornar para a etapa **Revisar pendências** antes de prosseguir.

### Critério

Se o usuário precisar interpretar tecnicamente um erro para decidir o próximo passo,
a experiência deve ser considerada inadequada.


# Anexo A.21 — Diretriz de Produto


### Objetivo

Detalhar uma expectativa de comportamento do fluxo.

### Diretriz

- Priorizar simplicidade sobre quantidade de informação.
- Evitar decisões adicionais nesta etapa.
- Toda mensagem deve orientar a próxima ação.
- Feedbacks devem ser objetivos e consistentes.

### Exemplo

Quando houver conflitos, a interface deve explicar o motivo e indicar claramente
que o usuário precisa retornar para a etapa **Revisar pendências** antes de prosseguir.

### Critério

Se o usuário precisar interpretar tecnicamente um erro para decidir o próximo passo,
a experiência deve ser considerada inadequada.


# Anexo A.22 — Diretriz de Produto


### Objetivo

Detalhar uma expectativa de comportamento do fluxo.

### Diretriz

- Priorizar simplicidade sobre quantidade de informação.
- Evitar decisões adicionais nesta etapa.
- Toda mensagem deve orientar a próxima ação.
- Feedbacks devem ser objetivos e consistentes.

### Exemplo

Quando houver conflitos, a interface deve explicar o motivo e indicar claramente
que o usuário precisa retornar para a etapa **Revisar pendências** antes de prosseguir.

### Critério

Se o usuário precisar interpretar tecnicamente um erro para decidir o próximo passo,
a experiência deve ser considerada inadequada.


# Anexo A.23 — Diretriz de Produto


### Objetivo

Detalhar uma expectativa de comportamento do fluxo.

### Diretriz

- Priorizar simplicidade sobre quantidade de informação.
- Evitar decisões adicionais nesta etapa.
- Toda mensagem deve orientar a próxima ação.
- Feedbacks devem ser objetivos e consistentes.

### Exemplo

Quando houver conflitos, a interface deve explicar o motivo e indicar claramente
que o usuário precisa retornar para a etapa **Revisar pendências** antes de prosseguir.

### Critério

Se o usuário precisar interpretar tecnicamente um erro para decidir o próximo passo,
a experiência deve ser considerada inadequada.


# Anexo A.24 — Diretriz de Produto


### Objetivo

Detalhar uma expectativa de comportamento do fluxo.

### Diretriz

- Priorizar simplicidade sobre quantidade de informação.
- Evitar decisões adicionais nesta etapa.
- Toda mensagem deve orientar a próxima ação.
- Feedbacks devem ser objetivos e consistentes.

### Exemplo

Quando houver conflitos, a interface deve explicar o motivo e indicar claramente
que o usuário precisa retornar para a etapa **Revisar pendências** antes de prosseguir.

### Critério

Se o usuário precisar interpretar tecnicamente um erro para decidir o próximo passo,
a experiência deve ser considerada inadequada.


# Anexo A.25 — Diretriz de Produto


### Objetivo

Detalhar uma expectativa de comportamento do fluxo.

### Diretriz

- Priorizar simplicidade sobre quantidade de informação.
- Evitar decisões adicionais nesta etapa.
- Toda mensagem deve orientar a próxima ação.
- Feedbacks devem ser objetivos e consistentes.

### Exemplo

Quando houver conflitos, a interface deve explicar o motivo e indicar claramente
que o usuário precisa retornar para a etapa **Revisar pendências** antes de prosseguir.

### Critério

Se o usuário precisar interpretar tecnicamente um erro para decidir o próximo passo,
a experiência deve ser considerada inadequada.

