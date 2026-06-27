# Processamento e Validações

> Documento: **04-processamento-e-validacoes.md**

---

# Objetivo

Este documento define o comportamento funcional do processamento executado pela página **Fluxos**, bem como todas as validações que devem ocorrer antes, durante e após cada etapa do Workflow.

Seu objetivo é garantir que o processamento ocorra de forma consistente, previsível e resiliente, preservando a integridade dos dados mesmo diante de falhas parciais ou interrupções.

Este documento descreve **o comportamento esperado da aplicação**, sem entrar em detalhes de implementação técnica.

---

# Modelo de Processamento

O Workflow é executado como um processo sequencial composto por cinco etapas independentes.

Cada etapa:

* recebe dados produzidos pela etapa anterior;
* realiza validações próprias;
* executa seu processamento;
* registra o resultado;
* disponibiliza informações para a próxima etapa.

A conclusão de uma etapa representa um ponto consistente do processamento.

---

# Fluxo Geral

```text
Iniciar Workflow

↓

Validar Pré-requisitos

↓

Executar Etapa

↓

Validar Resultado

↓

Registrar Estado

↓

Existe próxima etapa?

├── Sim
│
▼
Executar próxima etapa

└── Não
     │
     ▼
Finalizar Workflow
```

---

# Pré-validações

Antes do início da execução, o sistema deve validar:

| Validação                    | Obrigatória |
| ---------------------------- | ----------- |
| Banco PostgreSQL disponível  | Sim         |
| Biblioteca configurada       | Sim         |
| Diretório acessível          | Sim         |
| Workflow anterior finalizado | Sim         |

Caso qualquer validação obrigatória falhe, o Workflow não deve ser iniciado.

---

# Validações por Etapa

## Organizar Biblioteca

Validar:

* diretório configurado;
* permissão de leitura;
* existência da biblioteca.

---

## Catalogar Obras

Validar:

* etapa anterior concluída;
* índice da biblioteca atualizado.

---

## Resolver IDs

Validar:

* existência de obras catalogadas;
* conectividade com MangaUpdates.

---

## Atualizar Metadados

Validar:

* existência de `mangaupdates_id`;
* disponibilidade da API do MangaUpdates.

---

## Sincronizar Notion

Validar:

* integração configurada;
* acesso ao banco do Notion;
* disponibilidade da API.

---

# Validações de Integridade

Durante todo o Workflow, o sistema deve garantir:

* ausência de registros duplicados;
* consistência dos identificadores;
* preservação dos relacionamentos;
* persistência correta das alterações;
* atualização das datas de processamento.

Nenhuma etapa deve produzir dados inconsistentes.

---

# Regras de Continuidade

O Workflow deve continuar sua execução sempre que possível.

Exemplos:

| Situação                 | Comportamento                         |
| ------------------------ | ------------------------------------- |
| Uma obra falhou          | Continuar processando as demais       |
| API externa indisponível | Encerrar apenas a etapa afetada       |
| Registro inválido        | Ignorar o registro e registrar alerta |
| Falha de uma integração  | Preservar os resultados já obtidos    |

O objetivo é maximizar a quantidade de processamento concluído.

---

# Validações de Elegibilidade

Cada obra deve ser avaliada antes de entrar em uma etapa.

Exemplos:

## Resolver IDs

Elegível quando:

* catalogada;
* sem `mangaupdates_id`.

---

## Atualizar Metadados

Elegível quando:

* possui `mangaupdates_id`;
* sincronização habilitada.

---

## Sincronizar Notion

Elegível quando:

* possui dados válidos;
* integração configurada.

Obras não elegíveis devem ser ignoradas e registradas no resumo da execução.

---

# Validações de Entrada

Toda informação recebida pelo Workflow deve ser validada antes de ser utilizada.

Exemplos:

* nomes vazios;
* caminhos inválidos;
* identificadores inexistentes;
* propriedades obrigatórias ausentes;
* formatos incompatíveis.

Dados inválidos não devem interromper o processamento global.

---

# Reprocessamento

Uma etapa poderá ser executada novamente quando:

* houver falha anterior;
* novos dados estiverem disponíveis;
* o usuário solicitar atualização;
* uma integração voltar a ficar disponível.

O reprocessamento deve afetar apenas a etapa selecionada e suas dependências diretas, sem reiniciar automaticamente todo o Workflow.

---

# Cancelamento

Quando o usuário cancelar a execução:

O sistema deve:

* concluir a operação corrente, sempre que possível;
* persistir os resultados já obtidos;
* registrar o ponto de interrupção;
* atualizar o estado da interface.

Nenhuma alteração já confirmada deve ser revertida automaticamente.

---

# Registro das Validações

Toda validação relevante deve produzir um resultado.

Possíveis resultados:

* validado;
* ignorado;
* alerta;
* erro.

Esses resultados alimentam o resumo apresentado ao final do Workflow.

---

# Resumo da Execução

Ao concluir o processamento, a interface deve informar:

* obras analisadas;
* obras processadas;
* obras ignoradas;
* obras com erro;
* alertas encontrados;
* tempo total da execução;
* etapa final alcançada.

Essas informações devem permanecer disponíveis até uma nova execução.

---

# Mensagens ao Usuário

Toda validação relevante deve gerar um feedback compreensível.

Exemplos:

* "Biblioteca validada com sucesso."
* "15 obras ignoradas por não possuírem ID."
* "Sincronização concluída com 3 alertas."
* "Workflow interrompido pelo usuário."

Mensagens técnicas detalhadas devem permanecer restritas aos logs.

---

# Relação com outros documentos

| Documento                 | Conteúdo relacionado              |
| ------------------------- | --------------------------------- |
| 03-etapas-do-workflow.md  | Sequência de execução             |
| 05-integracoes.md         | Dependências externas             |
| 06-estados-e-mensagens.md | Estados e feedback visual         |
| 07-regras-de-navegacao.md | Navegação durante o processamento |

---

# Conclusão

O processamento do módulo **Fluxos** deve ser resiliente, incremental e orientado à integridade dos dados. As validações definidas neste documento garantem que apenas informações consistentes avancem entre as etapas do Workflow, enquanto falhas localizadas são tratadas de forma isolada, preservando o máximo possível dos resultados obtidos durante a execução.
