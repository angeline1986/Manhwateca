# Ajuda

> Documento: **10-ajuda.md**

---

# Objetivo

Este capítulo reúne informações de apoio para utilização do módulo **Fluxos**.

Aqui você encontrará:

* respostas para dúvidas frequentes;
* soluções para os problemas mais comuns;
* explicação dos principais termos utilizados pela Manhwateca.

Sempre que surgir alguma dúvida durante a utilização do Workflow, consulte este documento antes de repetir uma execução ou alterar configurações da aplicação.

---

# Perguntas Frequentes (FAQ)

## O que acontece quando clico em **Executar Workflow**?

A Manhwateca inicia automaticamente todas as etapas do processamento na seguinte ordem:

1. Organizar Biblioteca;
2. Catalogar Obras;
3. Resolver IDs;
4. Atualizar Metadados;
5. Sincronizar Notion.

Cada etapa somente começa quando a anterior for concluída.

---

## Preciso executar todas as etapas sempre?

Não.

Em muitas situações é possível executar apenas uma etapa específica.

Exemplos:

| Situação                    | Etapa recomendada   |
| --------------------------- | ------------------- |
| Novos capítulos disponíveis | Atualizar Metadados |
| Falha na sincronização      | Sincronizar Notion  |
| Obras sem ID                | Resolver IDs        |
| Alterações na biblioteca    | Workflow completo   |

---

## Posso fechar a página durante a execução?

Sim.

O Workflow continuará sendo executado normalmente.

Ao retornar para **Fluxos**, o estado da execução será recuperado automaticamente.

---

## Posso utilizar outros módulos da aplicação?

Sim.

Você pode navegar livremente pela Manhwateca enquanto o Workflow continua em execução.

---

## Posso interromper uma execução?

Sim.

Basta clicar em **Cancelar Workflow**.

A Manhwateca encerrará a execução de forma segura, preservando todas as operações já concluídas.

---

## A sincronização altera meus dados de leitura?

Não.

Informações pessoais como:

* progresso de leitura;
* notas;
* favoritos;
* comentários;

continuam preservadas.

A sincronização atualiza apenas as propriedades configuradas para integração.

---

## Uma obra sem ID é um problema?

Não.

Ela continuará disponível na biblioteca.

Entretanto, recursos que dependem do MangaUpdates, como atualização automática de metadados, não poderão ser utilizados até que um ID válido seja associado.

---

## Posso executar novamente apenas uma etapa?

Sim.

Sempre que necessário, você poderá reexecutar individualmente:

* Resolver IDs;
* Atualizar Metadados;
* Sincronizar Notion.

Essa é a forma recomendada para corrigir problemas específicos.

---

# Solução de Problemas

## PostgreSQL indisponível

### Sintomas

* Workflow não inicia.
* Mensagem indicando indisponibilidade do banco.

### Possíveis causas

* PostgreSQL desligado.
* Configuração incorreta.
* Problema de conexão.

### O que fazer

1. Verifique se o PostgreSQL está em execução.
2. Confirme as configurações da aplicação.
3. Tente iniciar novamente o Workflow.

---

## Biblioteca não encontrada

### Sintomas

* Falha na etapa **Organizar Biblioteca**.

### Possíveis causas

* Diretório removido.
* Caminho incorreto.
* Unidade desconectada.

### O que fazer

1. Confirme o local configurado para a biblioteca.
2. Verifique se o diretório ainda existe.
3. Execute novamente o Workflow.

---

## MangaUpdates indisponível

### Sintomas

* Falha em **Resolver IDs**.
* Falha em **Atualizar Metadados**.

### Possíveis causas

* Instabilidade temporária.
* Problemas de conexão com a internet.
* Limitação temporária da API.

### O que fazer

1. Aguarde alguns minutos.
2. Execute novamente apenas a etapa afetada.

---

## Falha na sincronização com o Notion

### Sintomas

* Páginas não atualizadas.
* Mensagens de erro durante a sincronização.

### Possíveis causas

* Token inválido.
* Banco não encontrado.
* Instabilidade temporária da API.

### O que fazer

1. Verifique as configurações da integração.
2. Confirme o acesso ao banco do Notion.
3. Execute novamente **Sincronizar Notion**.

---

## Workflow muito lento

### Sintomas

* Processamento aparentemente parado.
* Tempo elevado entre etapas.

### Possíveis causas

* Biblioteca muito grande.
* Conexão lenta.
* APIs externas com resposta demorada.

### O que fazer

* Aguarde a conclusão da etapa atual.
* Evite cancelar a execução apenas por lentidão.
* Consulte os alertas exibidos pela aplicação.

---

# Glossário

## Biblioteca

Conjunto de pastas onde suas obras estão armazenadas.

---

## Workflow

Sequência de etapas executadas automaticamente pela Manhwateca para organizar, atualizar e sincronizar a biblioteca.

---

## Etapa

Cada fase individual do Workflow.

Exemplos:

* Organizar Biblioteca;
* Resolver IDs;
* Atualizar Metadados.

---

## MangaUpdates ID

Identificador oficial utilizado para localizar uma obra no MangaUpdates.

Cada obra possui um ID único.

---

## Metadados

Informações oficiais de uma obra.

Exemplos:

* título;
* autores;
* artistas;
* gêneros;
* status;
* quantidade de capítulos.

---

## Sincronização

Processo de atualização das informações entre a Manhwateca e o Notion.

---

## Integração

Comunicação entre a Manhwateca e um serviço externo.

Exemplos:

* PostgreSQL;
* MangaUpdates;
* Notion.

---

## Alerta

Mensagem indicando uma situação que merece atenção, mas que não impede necessariamente a conclusão do Workflow.

---

## Erro

Situação que impede a execução de uma operação específica.

Dependendo do caso, apenas uma etapa poderá ser afetada.

---

## Reprocessamento

Execução novamente de uma etapa do Workflow para corrigir falhas ou atualizar informações.

---

## Dashboard

Página inicial da Manhwateca que apresenta o estado geral da biblioteca e recomendações de ações.

---

# Onde obter ajuda

Caso uma dúvida permaneça mesmo após consultar este manual:

1. Revise as mensagens exibidas pelo Workflow.
2. Consulte os alertas apresentados ao final da execução.
3. Verifique as configurações das integrações utilizadas.
4. Consulte a documentação técnica da Manhwateca, caso tenha acesso.

Na maioria dos casos, essas informações são suficientes para identificar a causa do problema.

---

# Conclusão

O módulo **Fluxos** foi projetado para automatizar as tarefas mais importantes da Manhwateca de forma segura e previsível. Este capítulo reúne as principais dúvidas, soluções para problemas frequentes e definições dos termos utilizados ao longo do Workflow, servindo como referência rápida para o uso diário da aplicação.
