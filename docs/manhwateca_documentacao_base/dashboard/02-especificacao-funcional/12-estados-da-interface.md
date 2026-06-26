# 12. Estados da Interface

Diferentes visualizações baseadas no estado da aplicação:

### 1. Estado de Carregamento (Loading):
- Shimmer effect (esqueleto) nos cards de métricas e na lista de pendências.

### 2. Estado Vazio (Empty State):
- Se não houver obras catalogadas, o Hero deve exibir um botão "Iniciar primeira catalogação" e as métricas devem zerar.

### 3. Estado de Erro Crítico:
- Caso o banco de dados esteja offline, exibir um overlay ou banner de aviso impedindo o uso do Dashboard.