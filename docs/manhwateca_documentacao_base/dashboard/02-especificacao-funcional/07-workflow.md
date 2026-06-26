# 07. Workflow (Fluxo Guiado)

Visualizador de progresso linear do processo da Manhwateca.

### As 5 Etapas:
1.  **Organizar biblioteca:** Verificação de nomenclatura de pastas e arquivos.
2.  **Catalogar arquivos:** Ingestão de dados no PostgreSQL.
3.  **Resolver IDs:** Vinculação com MangaUpdates.
4.  **Atualizar metadados:** Download de capas, sinopses e status.
5.  **Sincronizar Notion:** Upload de dados para a nuvem.

### Estados Visuais:
- **Concluído (`.done`):** Ícone de check e cores suaves.
- **Em andamento:** Número da etapa em destaque.
- **Aguardando (`.waiting`):** Opacidade reduzida e cores neutras.