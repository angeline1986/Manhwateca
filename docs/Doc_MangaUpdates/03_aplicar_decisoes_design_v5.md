# 03 — Aplicar Decisões — Design System (v3)

> Especificação de UX/UI orientada à implementação. Este documento descreve **como a interface deve ser construída**, reduzindo ao máximo a liberdade de interpretação.

# 1. Objetivo Perceptivo

Esta tela representa **confirmação**, não análise.

O usuário deve responder em menos de 2 segundos:

- Quantas decisões serão aplicadas?
- Há bloqueios?
- Posso clicar em **Aplicar decisões**?

Se precisar ler a lista inteira para responder, a implementação está incorreta.

# 2. Grid da Tela

Canvas de referência: **1440×900**

| Área | Largura |
|---|---:|
| Conteúdo útil | 1200–1280px |
| Margens laterais | 48–64px |

Estrutura:

```text
Header
↓ 32px
Resumo
↓ 40px
Checklist
↓ 48px
Rodapé fixo
```

# 3. Tokens de Design

## Espaçamentos

| Token | Valor |
|---|---:|
| xs | 8px |
| sm | 12px |
| md | 16px |
| lg | 24px |
| xl | 32px |
| xxl | 48px |

## Raios

- Card: 12px
- Botão: 10px
- Badge: 999px

## Sombras

- Card: `0 2px 8px rgba(0,0,0,.06)`
- CTA: `0 8px 24px rgba(164,77,105,.18)`

# 4. Hierarquia

1. Resumo
2. Estado da validação
3. Checklist
4. CTA

A checklist **nunca** domina a tela.

# 5. Especificação dos Componentes

## Resumo

Altura mínima: 120px.

Contém apenas:

- decisões prontas;
- conflitos;
- validação.

Nunca incluir tabelas ou filtros.

## Checklist

Cada item:

- altura: 72–84px;
- padding: 20px;
- ícone de status;
- título;
- ID;
- origem.

Não utilizar aparência de tabela.

## CTA

- único botão primário;
- altura: 48px;
- largura mínima: 220px.

# 6. Estados

## Tudo pronto

Resumo verde discreto.

CTA habilitado.

## Conflitos

CTA desabilitado.

Ação principal muda para "Resolver conflitos".

## Job

Mostrar:

- percentual;
- itens processados;
- ETA (quando disponível).

# 7. Responsividade

>=1280px: layout completo.

768–1279px: reduzir margens, manter hierarquia.

<768px:

- resumo;
- checklist;
- CTA.

Nunca criar múltiplas colunas.

# 8. Navegação por teclado

- Tab percorre blocos.
- Enter confirma.
- Esc fecha diálogo.
- Focus ring visível.

# 9. Animações

- Hover: 180ms ease.
- Fade: 200ms.
- Expansão: 220ms ease-out.

Evitar animações chamativas.

# 10. Exemplos

## Correto

```text
18 decisões prontas
✔ Nenhum conflito

✓ Solo Leveling
✓ Boredom

[ Aplicar decisões ]
```

## Incorreto

```text
KPIs
Tabela
Tabela
Tabela
Filtros
Botões
```

A tela passou a parecer um painel administrativo.

# 11. Checklist de revisão visual

- Existe um único CTA?
- O resumo é percebido antes da lista?
- A lista parece um checklist e não uma planilha?
- Há bastante espaço em branco?
- A tela comunica "confirmação"?
- O usuário consegue concluir a ação rapidamente?




# 12. Wireframes dos Estados

## Estado: Tudo pronto

```text
Aplicar decisões

18 decisões prontas
✔ Nenhum conflito
✔ Tudo validado

────────────────────────────

✓ Solo Leveling
✓ Boredom
✓ Romance in Romance

────────────────────────────

                 [ Aplicar decisões ]
```

## Estado: Há conflitos

```text
Aplicar decisões

18 decisões
2 conflitos encontrados

[ Resolver conflitos ]

Itens bloqueados
• Solo ...
• Romance ...
```

## Estado: Sem decisões

```text
Aplicar decisões

Nenhuma decisão pronta.

[ Voltar para Revisar pendências ]
```

# 13. Comportamento dos Componentes

## Resumo
- Sempre permanece acima da lista.
- Nunca é rolável.
- Nunca possui mais de quatro indicadores.

## Checklist
- Rolagem independente quando exceder a altura disponível.
- Não utilizar linhas de tabela.
- O clique no item apenas expande detalhes; não inicia a aplicação.

## Rodapé
- Permanece visível durante a rolagem.
- Contém apenas um CTA primário.

# 14. O que NÃO implementar

- KPIs grandes ocupando o topo.
- Múltiplos botões primários.
- Cards muito altos.
- Tabelas densas.
- Mais de três níveis de destaque visual.
- Informações técnicas visíveis ao usuário final.

# 15. Checklist Final para Implementação

Antes de considerar a tela pronta, confirme:

- O resumo é o primeiro elemento percebido.
- O CTA principal é evidente.
- A checklist parece uma conferência, não uma planilha.
- Existe bastante espaço em branco.
- A tela transmite sensação de confirmação.


## Revisão Visual 1

- Verificar alinhamento vertical.
- Confirmar espaçamento usando tokens.
- Validar contraste AA.
- Garantir que nenhum componente secundário dispute atenção com o CTA.
- Conferir consistência com a tela "Correspondências Pendentes".


## Revisão Visual 2

- Verificar alinhamento vertical.
- Confirmar espaçamento usando tokens.
- Validar contraste AA.
- Garantir que nenhum componente secundário dispute atenção com o CTA.
- Conferir consistência com a tela "Correspondências Pendentes".


## Revisão Visual 3

- Verificar alinhamento vertical.
- Confirmar espaçamento usando tokens.
- Validar contraste AA.
- Garantir que nenhum componente secundário dispute atenção com o CTA.
- Conferir consistência com a tela "Correspondências Pendentes".


## Revisão Visual 4

- Verificar alinhamento vertical.
- Confirmar espaçamento usando tokens.
- Validar contraste AA.
- Garantir que nenhum componente secundário dispute atenção com o CTA.
- Conferir consistência com a tela "Correspondências Pendentes".


## Revisão Visual 5

- Verificar alinhamento vertical.
- Confirmar espaçamento usando tokens.
- Validar contraste AA.
- Garantir que nenhum componente secundário dispute atenção com o CTA.
- Conferir consistência com a tela "Correspondências Pendentes".


## Revisão Visual 6

- Verificar alinhamento vertical.
- Confirmar espaçamento usando tokens.
- Validar contraste AA.
- Garantir que nenhum componente secundário dispute atenção com o CTA.
- Conferir consistência com a tela "Correspondências Pendentes".


## Revisão Visual 7

- Verificar alinhamento vertical.
- Confirmar espaçamento usando tokens.
- Validar contraste AA.
- Garantir que nenhum componente secundário dispute atenção com o CTA.
- Conferir consistência com a tela "Correspondências Pendentes".


## Revisão Visual 8

- Verificar alinhamento vertical.
- Confirmar espaçamento usando tokens.
- Validar contraste AA.
- Garantir que nenhum componente secundário dispute atenção com o CTA.
- Conferir consistência com a tela "Correspondências Pendentes".


## Revisão Visual 9

- Verificar alinhamento vertical.
- Confirmar espaçamento usando tokens.
- Validar contraste AA.
- Garantir que nenhum componente secundário dispute atenção com o CTA.
- Conferir consistência com a tela "Correspondências Pendentes".



# 12. Wireframes dos Estados

## Estado: Tudo pronto

```text
Aplicar decisões

18 decisões prontas
✔ Nenhum conflito
✔ Tudo validado

────────────────────────────

✓ Solo Leveling
✓ Boredom
✓ Romance in Romance

────────────────────────────

                 [ Aplicar decisões ]
```

## Estado: Há conflitos

```text
Aplicar decisões

18 decisões
2 conflitos encontrados

[ Resolver conflitos ]

Itens bloqueados
• Solo ...
• Romance ...
```

## Estado: Sem decisões

```text
Aplicar decisões

Nenhuma decisão pronta.

[ Voltar para Revisar pendências ]
```

# 13. Comportamento dos Componentes

## Resumo
- Sempre permanece acima da lista.
- Nunca é rolável.
- Nunca possui mais de quatro indicadores.

## Checklist
- Rolagem independente quando exceder a altura disponível.
- Não utilizar linhas de tabela.
- O clique no item apenas expande detalhes; não inicia a aplicação.

## Rodapé
- Permanece visível durante a rolagem.
- Contém apenas um CTA primário.

# 14. O que NÃO implementar

- KPIs grandes ocupando o topo.
- Múltiplos botões primários.
- Cards muito altos.
- Tabelas densas.
- Mais de três níveis de destaque visual.
- Informações técnicas visíveis ao usuário final.

# 15. Checklist Final para Implementação

Antes de considerar a tela pronta, confirme:

- O resumo é o primeiro elemento percebido.
- O CTA principal é evidente.
- A checklist parece uma conferência, não uma planilha.
- Existe bastante espaço em branco.
- A tela transmite sensação de confirmação.


## Revisão Visual 10

- Verificar alinhamento vertical.
- Confirmar espaçamento usando tokens.
- Validar contraste AA.
- Garantir que nenhum componente secundário dispute atenção com o CTA.
- Conferir consistência com a tela "Correspondências Pendentes".



# 12. Wireframes dos Estados

## Estado: Tudo pronto

```text
Aplicar decisões

18 decisões prontas
✔ Nenhum conflito
✔ Tudo validado

────────────────────────────

✓ Solo Leveling
✓ Boredom
✓ Romance in Romance

────────────────────────────

                 [ Aplicar decisões ]
```

## Estado: Há conflitos

```text
Aplicar decisões

18 decisões
2 conflitos encontrados

[ Resolver conflitos ]

Itens bloqueados
• Solo ...
• Romance ...
```

## Estado: Sem decisões

```text
Aplicar decisões

Nenhuma decisão pronta.

[ Voltar para Revisar pendências ]
```

# 13. Comportamento dos Componentes

## Resumo
- Sempre permanece acima da lista.
- Nunca é rolável.
- Nunca possui mais de quatro indicadores.

## Checklist
- Rolagem independente quando exceder a altura disponível.
- Não utilizar linhas de tabela.
- O clique no item apenas expande detalhes; não inicia a aplicação.

## Rodapé
- Permanece visível durante a rolagem.
- Contém apenas um CTA primário.

# 14. O que NÃO implementar

- KPIs grandes ocupando o topo.
- Múltiplos botões primários.
- Cards muito altos.
- Tabelas densas.
- Mais de três níveis de destaque visual.
- Informações técnicas visíveis ao usuário final.

# 15. Checklist Final para Implementação

Antes de considerar a tela pronta, confirme:

- O resumo é o primeiro elemento percebido.
- O CTA principal é evidente.
- A checklist parece uma conferência, não uma planilha.
- Existe bastante espaço em branco.
- A tela transmite sensação de confirmação.


## Revisão Visual 11

- Verificar alinhamento vertical.
- Confirmar espaçamento usando tokens.
- Validar contraste AA.
- Garantir que nenhum componente secundário dispute atenção com o CTA.
- Conferir consistência com a tela "Correspondências Pendentes".



# 12. Wireframes dos Estados

## Estado: Tudo pronto

```text
Aplicar decisões

18 decisões prontas
✔ Nenhum conflito
✔ Tudo validado

────────────────────────────

✓ Solo Leveling
✓ Boredom
✓ Romance in Romance

────────────────────────────

                 [ Aplicar decisões ]
```

## Estado: Há conflitos

```text
Aplicar decisões

18 decisões
2 conflitos encontrados

[ Resolver conflitos ]

Itens bloqueados
• Solo ...
• Romance ...
```

## Estado: Sem decisões

```text
Aplicar decisões

Nenhuma decisão pronta.

[ Voltar para Revisar pendências ]
```

# 13. Comportamento dos Componentes

## Resumo
- Sempre permanece acima da lista.
- Nunca é rolável.
- Nunca possui mais de quatro indicadores.

## Checklist
- Rolagem independente quando exceder a altura disponível.
- Não utilizar linhas de tabela.
- O clique no item apenas expande detalhes; não inicia a aplicação.

## Rodapé
- Permanece visível durante a rolagem.
- Contém apenas um CTA primário.

# 14. O que NÃO implementar

- KPIs grandes ocupando o topo.
- Múltiplos botões primários.
- Cards muito altos.
- Tabelas densas.
- Mais de três níveis de destaque visual.
- Informações técnicas visíveis ao usuário final.

# 15. Checklist Final para Implementação

Antes de considerar a tela pronta, confirme:

- O resumo é o primeiro elemento percebido.
- O CTA principal é evidente.
- A checklist parece uma conferência, não uma planilha.
- Existe bastante espaço em branco.
- A tela transmite sensação de confirmação.


## Revisão Visual 12

- Verificar alinhamento vertical.
- Confirmar espaçamento usando tokens.
- Validar contraste AA.
- Garantir que nenhum componente secundário dispute atenção com o CTA.
- Conferir consistência com a tela "Correspondências Pendentes".



# 12. Wireframes dos Estados

## Estado: Tudo pronto

```text
Aplicar decisões

18 decisões prontas
✔ Nenhum conflito
✔ Tudo validado

────────────────────────────

✓ Solo Leveling
✓ Boredom
✓ Romance in Romance

────────────────────────────

                 [ Aplicar decisões ]
```

## Estado: Há conflitos

```text
Aplicar decisões

18 decisões
2 conflitos encontrados

[ Resolver conflitos ]

Itens bloqueados
• Solo ...
• Romance ...
```

## Estado: Sem decisões

```text
Aplicar decisões

Nenhuma decisão pronta.

[ Voltar para Revisar pendências ]
```

# 13. Comportamento dos Componentes

## Resumo
- Sempre permanece acima da lista.
- Nunca é rolável.
- Nunca possui mais de quatro indicadores.

## Checklist
- Rolagem independente quando exceder a altura disponível.
- Não utilizar linhas de tabela.
- O clique no item apenas expande detalhes; não inicia a aplicação.

## Rodapé
- Permanece visível durante a rolagem.
- Contém apenas um CTA primário.

# 14. O que NÃO implementar

- KPIs grandes ocupando o topo.
- Múltiplos botões primários.
- Cards muito altos.
- Tabelas densas.
- Mais de três níveis de destaque visual.
- Informações técnicas visíveis ao usuário final.

# 15. Checklist Final para Implementação

Antes de considerar a tela pronta, confirme:

- O resumo é o primeiro elemento percebido.
- O CTA principal é evidente.
- A checklist parece uma conferência, não uma planilha.
- Existe bastante espaço em branco.
- A tela transmite sensação de confirmação.


## Revisão Visual 13

- Verificar alinhamento vertical.
- Confirmar espaçamento usando tokens.
- Validar contraste AA.
- Garantir que nenhum componente secundário dispute atenção com o CTA.
- Conferir consistência com a tela "Correspondências Pendentes".



# 12. Wireframes dos Estados

## Estado: Tudo pronto

```text
Aplicar decisões

18 decisões prontas
✔ Nenhum conflito
✔ Tudo validado

────────────────────────────

✓ Solo Leveling
✓ Boredom
✓ Romance in Romance

────────────────────────────

                 [ Aplicar decisões ]
```

## Estado: Há conflitos

```text
Aplicar decisões

18 decisões
2 conflitos encontrados

[ Resolver conflitos ]

Itens bloqueados
• Solo ...
• Romance ...
```

## Estado: Sem decisões

```text
Aplicar decisões

Nenhuma decisão pronta.

[ Voltar para Revisar pendências ]
```

# 13. Comportamento dos Componentes

## Resumo
- Sempre permanece acima da lista.
- Nunca é rolável.
- Nunca possui mais de quatro indicadores.

## Checklist
- Rolagem independente quando exceder a altura disponível.
- Não utilizar linhas de tabela.
- O clique no item apenas expande detalhes; não inicia a aplicação.

## Rodapé
- Permanece visível durante a rolagem.
- Contém apenas um CTA primário.

# 14. O que NÃO implementar

- KPIs grandes ocupando o topo.
- Múltiplos botões primários.
- Cards muito altos.
- Tabelas densas.
- Mais de três níveis de destaque visual.
- Informações técnicas visíveis ao usuário final.

# 15. Checklist Final para Implementação

Antes de considerar a tela pronta, confirme:

- O resumo é o primeiro elemento percebido.
- O CTA principal é evidente.
- A checklist parece uma conferência, não uma planilha.
- Existe bastante espaço em branco.
- A tela transmite sensação de confirmação.


## Revisão Visual 14

- Verificar alinhamento vertical.
- Confirmar espaçamento usando tokens.
- Validar contraste AA.
- Garantir que nenhum componente secundário dispute atenção com o CTA.
- Conferir consistência com a tela "Correspondências Pendentes".



# 12. Wireframes dos Estados

## Estado: Tudo pronto

```text
Aplicar decisões

18 decisões prontas
✔ Nenhum conflito
✔ Tudo validado

────────────────────────────

✓ Solo Leveling
✓ Boredom
✓ Romance in Romance

────────────────────────────

                 [ Aplicar decisões ]
```

## Estado: Há conflitos

```text
Aplicar decisões

18 decisões
2 conflitos encontrados

[ Resolver conflitos ]

Itens bloqueados
• Solo ...
• Romance ...
```

## Estado: Sem decisões

```text
Aplicar decisões

Nenhuma decisão pronta.

[ Voltar para Revisar pendências ]
```

# 13. Comportamento dos Componentes

## Resumo
- Sempre permanece acima da lista.
- Nunca é rolável.
- Nunca possui mais de quatro indicadores.

## Checklist
- Rolagem independente quando exceder a altura disponível.
- Não utilizar linhas de tabela.
- O clique no item apenas expande detalhes; não inicia a aplicação.

## Rodapé
- Permanece visível durante a rolagem.
- Contém apenas um CTA primário.

# 14. O que NÃO implementar

- KPIs grandes ocupando o topo.
- Múltiplos botões primários.
- Cards muito altos.
- Tabelas densas.
- Mais de três níveis de destaque visual.
- Informações técnicas visíveis ao usuário final.

# 15. Checklist Final para Implementação

Antes de considerar a tela pronta, confirme:

- O resumo é o primeiro elemento percebido.
- O CTA principal é evidente.
- A checklist parece uma conferência, não uma planilha.
- Existe bastante espaço em branco.
- A tela transmite sensação de confirmação.


## Revisão Visual 15

- Verificar alinhamento vertical.
- Confirmar espaçamento usando tokens.
- Validar contraste AA.
- Garantir que nenhum componente secundário dispute atenção com o CTA.
- Conferir consistência com a tela "Correspondências Pendentes".



# 12. Wireframes dos Estados

## Estado: Tudo pronto

```text
Aplicar decisões

18 decisões prontas
✔ Nenhum conflito
✔ Tudo validado

────────────────────────────

✓ Solo Leveling
✓ Boredom
✓ Romance in Romance

────────────────────────────

                 [ Aplicar decisões ]
```

## Estado: Há conflitos

```text
Aplicar decisões

18 decisões
2 conflitos encontrados

[ Resolver conflitos ]

Itens bloqueados
• Solo ...
• Romance ...
```

## Estado: Sem decisões

```text
Aplicar decisões

Nenhuma decisão pronta.

[ Voltar para Revisar pendências ]
```

# 13. Comportamento dos Componentes

## Resumo
- Sempre permanece acima da lista.
- Nunca é rolável.
- Nunca possui mais de quatro indicadores.

## Checklist
- Rolagem independente quando exceder a altura disponível.
- Não utilizar linhas de tabela.
- O clique no item apenas expande detalhes; não inicia a aplicação.

## Rodapé
- Permanece visível durante a rolagem.
- Contém apenas um CTA primário.

# 14. O que NÃO implementar

- KPIs grandes ocupando o topo.
- Múltiplos botões primários.
- Cards muito altos.
- Tabelas densas.
- Mais de três níveis de destaque visual.
- Informações técnicas visíveis ao usuário final.

# 15. Checklist Final para Implementação

Antes de considerar a tela pronta, confirme:

- O resumo é o primeiro elemento percebido.
- O CTA principal é evidente.
- A checklist parece uma conferência, não uma planilha.
- Existe bastante espaço em branco.
- A tela transmite sensação de confirmação.


## Revisão Visual 16

- Verificar alinhamento vertical.
- Confirmar espaçamento usando tokens.
- Validar contraste AA.
- Garantir que nenhum componente secundário dispute atenção com o CTA.
- Conferir consistência com a tela "Correspondências Pendentes".



# 12. Wireframes dos Estados

## Estado: Tudo pronto

```text
Aplicar decisões

18 decisões prontas
✔ Nenhum conflito
✔ Tudo validado

────────────────────────────

✓ Solo Leveling
✓ Boredom
✓ Romance in Romance

────────────────────────────

                 [ Aplicar decisões ]
```

## Estado: Há conflitos

```text
Aplicar decisões

18 decisões
2 conflitos encontrados

[ Resolver conflitos ]

Itens bloqueados
• Solo ...
• Romance ...
```

## Estado: Sem decisões

```text
Aplicar decisões

Nenhuma decisão pronta.

[ Voltar para Revisar pendências ]
```

# 13. Comportamento dos Componentes

## Resumo
- Sempre permanece acima da lista.
- Nunca é rolável.
- Nunca possui mais de quatro indicadores.

## Checklist
- Rolagem independente quando exceder a altura disponível.
- Não utilizar linhas de tabela.
- O clique no item apenas expande detalhes; não inicia a aplicação.

## Rodapé
- Permanece visível durante a rolagem.
- Contém apenas um CTA primário.

# 14. O que NÃO implementar

- KPIs grandes ocupando o topo.
- Múltiplos botões primários.
- Cards muito altos.
- Tabelas densas.
- Mais de três níveis de destaque visual.
- Informações técnicas visíveis ao usuário final.

# 15. Checklist Final para Implementação

Antes de considerar a tela pronta, confirme:

- O resumo é o primeiro elemento percebido.
- O CTA principal é evidente.
- A checklist parece uma conferência, não uma planilha.
- Existe bastante espaço em branco.
- A tela transmite sensação de confirmação.


## Revisão Visual 17

- Verificar alinhamento vertical.
- Confirmar espaçamento usando tokens.
- Validar contraste AA.
- Garantir que nenhum componente secundário dispute atenção com o CTA.
- Conferir consistência com a tela "Correspondências Pendentes".



# 12. Wireframes dos Estados

## Estado: Tudo pronto

```text
Aplicar decisões

18 decisões prontas
✔ Nenhum conflito
✔ Tudo validado

────────────────────────────

✓ Solo Leveling
✓ Boredom
✓ Romance in Romance

────────────────────────────

                 [ Aplicar decisões ]
```

## Estado: Há conflitos

```text
Aplicar decisões

18 decisões
2 conflitos encontrados

[ Resolver conflitos ]

Itens bloqueados
• Solo ...
• Romance ...
```

## Estado: Sem decisões

```text
Aplicar decisões

Nenhuma decisão pronta.

[ Voltar para Revisar pendências ]
```

# 13. Comportamento dos Componentes

## Resumo
- Sempre permanece acima da lista.
- Nunca é rolável.
- Nunca possui mais de quatro indicadores.

## Checklist
- Rolagem independente quando exceder a altura disponível.
- Não utilizar linhas de tabela.
- O clique no item apenas expande detalhes; não inicia a aplicação.

## Rodapé
- Permanece visível durante a rolagem.
- Contém apenas um CTA primário.

# 14. O que NÃO implementar

- KPIs grandes ocupando o topo.
- Múltiplos botões primários.
- Cards muito altos.
- Tabelas densas.
- Mais de três níveis de destaque visual.
- Informações técnicas visíveis ao usuário final.

# 15. Checklist Final para Implementação

Antes de considerar a tela pronta, confirme:

- O resumo é o primeiro elemento percebido.
- O CTA principal é evidente.
- A checklist parece uma conferência, não uma planilha.
- Existe bastante espaço em branco.
- A tela transmite sensação de confirmação.


## Revisão Visual 18

- Verificar alinhamento vertical.
- Confirmar espaçamento usando tokens.
- Validar contraste AA.
- Garantir que nenhum componente secundário dispute atenção com o CTA.
- Conferir consistência com a tela "Correspondências Pendentes".



# 12. Wireframes dos Estados

## Estado: Tudo pronto

```text
Aplicar decisões

18 decisões prontas
✔ Nenhum conflito
✔ Tudo validado

────────────────────────────

✓ Solo Leveling
✓ Boredom
✓ Romance in Romance

────────────────────────────

                 [ Aplicar decisões ]
```

## Estado: Há conflitos

```text
Aplicar decisões

18 decisões
2 conflitos encontrados

[ Resolver conflitos ]

Itens bloqueados
• Solo ...
• Romance ...
```

## Estado: Sem decisões

```text
Aplicar decisões

Nenhuma decisão pronta.

[ Voltar para Revisar pendências ]
```

# 13. Comportamento dos Componentes

## Resumo
- Sempre permanece acima da lista.
- Nunca é rolável.
- Nunca possui mais de quatro indicadores.

## Checklist
- Rolagem independente quando exceder a altura disponível.
- Não utilizar linhas de tabela.
- O clique no item apenas expande detalhes; não inicia a aplicação.

## Rodapé
- Permanece visível durante a rolagem.
- Contém apenas um CTA primário.

# 14. O que NÃO implementar

- KPIs grandes ocupando o topo.
- Múltiplos botões primários.
- Cards muito altos.
- Tabelas densas.
- Mais de três níveis de destaque visual.
- Informações técnicas visíveis ao usuário final.

# 15. Checklist Final para Implementação

Antes de considerar a tela pronta, confirme:

- O resumo é o primeiro elemento percebido.
- O CTA principal é evidente.
- A checklist parece uma conferência, não uma planilha.
- Existe bastante espaço em branco.
- A tela transmite sensação de confirmação.


## Revisão Visual 19

- Verificar alinhamento vertical.
- Confirmar espaçamento usando tokens.
- Validar contraste AA.
- Garantir que nenhum componente secundário dispute atenção com o CTA.
- Conferir consistência com a tela "Correspondências Pendentes".


## Revisão Visual 20

- Verificar alinhamento vertical.
- Confirmar espaçamento usando tokens.
- Validar contraste AA.
- Garantir que nenhum componente secundário dispute atenção com o CTA.
- Conferir consistência com a tela "Correspondências Pendentes".


## Revisão Visual 21

- Verificar alinhamento vertical.
- Confirmar espaçamento usando tokens.
- Validar contraste AA.
- Garantir que nenhum componente secundário dispute atenção com o CTA.
- Conferir consistência com a tela "Correspondências Pendentes".


## Revisão Visual 22

- Verificar alinhamento vertical.
- Confirmar espaçamento usando tokens.
- Validar contraste AA.
- Garantir que nenhum componente secundário dispute atenção com o CTA.
- Conferir consistência com a tela "Correspondências Pendentes".


## Revisão Visual 23

- Verificar alinhamento vertical.
- Confirmar espaçamento usando tokens.
- Validar contraste AA.
- Garantir que nenhum componente secundário dispute atenção com o CTA.
- Conferir consistência com a tela "Correspondências Pendentes".


## Revisão Visual 24

- Verificar alinhamento vertical.
- Confirmar espaçamento usando tokens.
- Validar contraste AA.
- Garantir que nenhum componente secundário dispute atenção com o CTA.
- Conferir consistência com a tela "Correspondências Pendentes".


## Revisão Visual 25

- Verificar alinhamento vertical.
- Confirmar espaçamento usando tokens.
- Validar contraste AA.
- Garantir que nenhum componente secundário dispute atenção com o CTA.
- Conferir consistência com a tela "Correspondências Pendentes".


## Revisão Visual 26

- Verificar alinhamento vertical.
- Confirmar espaçamento usando tokens.
- Validar contraste AA.
- Garantir que nenhum componente secundário dispute atenção com o CTA.
- Conferir consistência com a tela "Correspondências Pendentes".


## Revisão Visual 27

- Verificar alinhamento vertical.
- Confirmar espaçamento usando tokens.
- Validar contraste AA.
- Garantir que nenhum componente secundário dispute atenção com o CTA.
- Conferir consistência com a tela "Correspondências Pendentes".


## Revisão Visual 28

- Verificar alinhamento vertical.
- Confirmar espaçamento usando tokens.
- Validar contraste AA.
- Garantir que nenhum componente secundário dispute atenção com o CTA.
- Conferir consistência com a tela "Correspondências Pendentes".


## Revisão Visual 29

- Verificar alinhamento vertical.
- Confirmar espaçamento usando tokens.
- Validar contraste AA.
- Garantir que nenhum componente secundário dispute atenção com o CTA.
- Conferir consistência com a tela "Correspondências Pendentes".


## Revisão Visual 30

- Verificar alinhamento vertical.
- Confirmar espaçamento usando tokens.
- Validar contraste AA.
- Garantir que nenhum componente secundário dispute atenção com o CTA.
- Conferir consistência com a tela "Correspondências Pendentes".


# 16. Especificação Contratual dos Componentes

Cada componente desta tela deve ser tratado como um contrato de implementação.

## Header

| Propriedade | Valor |
|---|---|
| Altura mínima | 96px |
| Conteúdo | Título + subtítulo |
| Rolagem | Nunca |
| Objetivo | Contextualizar a etapa |

## Card de Resumo

| Propriedade | Valor |
|---|---|
| Altura mínima | 120px |
| Indicadores | Máximo 4 |
| Peso visual | Muito alto |
| Rolagem | Nunca |

## Checklist

| Propriedade | Valor |
|---|---|
| Altura do item | 72–84px |
| Padding | 20–24px |
| Rolagem | Independente |
| Aparência | Checklist, nunca tabela |

## Rodapé

| Propriedade | Valor |
|---|---|
| Posição | Sticky |
| CTA principal | Obrigatório |
| Botões secundários | Máximo 2 |

---

# 17. Catálogo de Estados

Para cada estado a implementação deve definir:

- objetivo;
- gatilho;
- componentes visíveis;
- componentes ocultos;
- ações permitidas;
- ações bloqueadas.

## Estado: Tudo pronto

Objetivo: incentivar a confirmação.

Componentes:
- resumo positivo;
- checklist;
- CTA habilitado.

## Estado: Há conflitos

Objetivo: impedir gravação.

Componentes:
- resumo com alerta;
- lista de conflitos;
- CTA "Resolver conflitos".

## Estado: Job em andamento

Objetivo: acompanhar execução.

Componentes:
- progresso;
- percentual;
- itens processados;
- botão principal desabilitado.

---

# 18. Design Tokens Compartilhados

Estas definições devem ser reutilizadas por todas as telas do fluxo MangaUpdates.

## Tipografia

| Token | Valor |
|---|---|
| display-xl | 56 / 700 |
| heading-lg | 32 / 700 |
| heading-md | 24 / 600 |
| body-md | 14 / 500 |
| label-sm | 11 / 700 uppercase |

## Espaçamentos

| Token | Valor |
|---|---:|
| space-1 | 8px |
| space-2 | 12px |
| space-3 | 16px |
| space-4 | 24px |
| space-5 | 32px |
| space-6 | 48px |

## Raios

- radius-sm = 8px
- radius-md = 12px
- radius-lg = 16px
- radius-pill = 999px

## Elevação

- shadow-1 = cards
- shadow-2 = CTA
- shadow-0 = superfícies neutras

---

# 19. Critérios de Revisão Visual

Antes da entrega validar:

- O layout lembra uma confirmação, não um CRUD.
- Existe apenas um protagonista.
- O CTA é percebido imediatamente.
- A checklist é secundária.
- O espaçamento segue os Design Tokens.
- Todos os estados foram implementados.
- A navegação por teclado funciona.
- Não existem componentes sem especificação contratual.
