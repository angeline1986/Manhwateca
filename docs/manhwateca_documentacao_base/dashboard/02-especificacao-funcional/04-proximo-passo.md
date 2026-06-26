# 04. Próximo Passo Recomendado (Hero)

Este é o componente de maior destaque visual da página. Ele atua como um assistente inteligente.

### Comportamento Lógico:
O sistema deve identificar a primeira tarefa incompleta no workflow e exibi-la aqui.
- **Exemplo atual:** Se existem obras catalogadas mas sem ID do MangaUpdates, o Hero exibe: "Resolver 8 obras sem ID".

### Elementos:
- **Badge:** "Etapa atual" com o número da fase.
- **Texto:** Título e descrição detalhando o impacto da pendência.
- **Botões:** 
    - `Continuar fluxo`: Direciona para a página de **Fluxos** na etapa específica.
    - `Ver pendências`: Abre uma lista detalhada (pode ser um modal ou scroll para a seção de pendências).