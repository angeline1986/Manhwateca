# 10. Atualização de Dados

O Dashboard não deve realizar polling constante para não sobrecarregar as APIs.

### Regras de Atualização:
1.  **No Carregamento:** Os dados são buscados ao abrir a página.
2.  **Manual:** Através do botão "Recarregar dados".
3.  **Cache:** Recomenda-se um cache de 5 minutos para os dados das métricas, exceto se o usuário forçar a atualização.