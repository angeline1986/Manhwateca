# 08. Integrações (Status do Ambiente)

Monitora a conectividade com serviços externos e locais.

### Itens Monitorados:
- **Catálogo local:** Conexão com o banco PostgreSQL.
- **Biblioteca no Drive:** Acessibilidade do diretório configurado.
- **MangaUpdates:** Status da API/Scraper.
- **Notion:** Validação do Token de integração.

### Lógica de exibição:
- Se a conexão falhar, o status deve mudar para `danger` ("Erro de Conexão").
- Se houver pendências de dados (mesmo com conexão ativa), exibir `warn` ("Atenção").