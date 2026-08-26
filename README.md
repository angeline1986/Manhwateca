# Manhwateca — ajustes de Acompanhamento (24/08/2026)

Pacote conservador: altera somente os arquivos já responsáveis pela página **Acompanhamento**.

## Ajustes

- Histórico da obra limitado aos **6 lançamentos mais recentes**.
- Remove a necessidade de **Ver mais**.
- Espera a task de **Verificar agora** realmente terminar (até 10 min) antes de recarregar subscriptions; evita atualizar o cabeçalho cedo demais com `Sem registro`.
- Se a task falhar, não trata a falha como conclusão bem-sucedida.
- Corrige a geometria dos cards `Último lançamento / Última verificação / Status`: o painel deixa de esticar os cards quando há pouco conteúdo.
- Alinha o enquadramento externo da página ao padrão de Organização: `padding: 16px`, conteúdo com `max-width: 1180px`, fila de `340px` e detalhe flexível.
- Não altera migration, banco, favoritos, endpoints, release service, slider, menu ou outras páginas.

## Como aplicar

1. Extraia este ZIP.
2. Copie `apply_updates.py` para a **raiz do repositório Manhwateca**.
3. Na raiz do projeto, execute:

```bash
python apply_updates.py
```

O script cria automaticamente um backup em:

```text
.tracking_patch_backup_20260824/
```

Depois inicie normalmente:

```bash
./start_manhwateca.command
```

## Observação sobre “Última verificação”

O cabeçalho continua usando o dado real `last_checked_at`. O pacote não inventa horário nem usa a hora do clique. A correção impede o frontend de desistir após apenas 30 segundos e recarregar dados antigos enquanto a task ainda está executando.
