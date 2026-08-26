MANHWATECA — AJUSTES ACOMPANHAMENTO
Data: 24/08/2026

ESCOPO
------
1. O botão "Verificar agora" passa a aguardar a task por até 10 minutos, em vez
   de parar silenciosamente após 30 segundos. Assim a tela só recarrega
   subscriptions/topbar depois da conclusão real da verificação.

2. O histórico de uma obra mostra 5 lançamentos inicialmente, com:
   - Ver mais (N)
   - Ver menos

3. A coluna esquerda de "Busca e favoritas" deixa de esticar KPIs, busca e
   filtros quando o histórico do painel direito é grande.

NÃO ALTERADO
------------
- migration/schema;
- favorite;
- ReleaseMonitorRepository.update_favorite();
- ReleaseMonitorService;
- endpoints;
- Dashboard;
- Organização v2.

Observação: não foi alterada a semântica de favorite/monitoramento porque
preservar perfeitamente o estado implícito vs explícito exigiria uma decisão
de schema além deste ajuste.

COMO APLICAR
------------
1. Extraia o ZIP.
2. Entre na raiz do Manhwateca.
3. Confira:
     git status
4. Execute:
     python /CAMINHO/DO/PACOTE/apply_patch.py

Exemplo:
     python ~/Downloads/manhwateca-acompanhamento-ajustes-20260824/apply_patch.py

VALIDAÇÃO
---------
  node --check web/js/pages/trackingPage.js

  .venv/bin/python -m pytest \
    tests/test_tracking_frontend.py \
    tests/test_tracking_followup_regressions.py \
    tests/test_release_monitor.py

Depois:
  ./start_manhwateca.command

Valide:
- o botão geral e o individual aguardam a task;
- após conclusão, a topbar recarrega com last_checked_at;
- histórico mostra 5 linhas por padrão;
- "Ver mais" expande;
- a fila esquerda permanece compacta.

O patch é defensivo: se o código local não corresponder aos trechos esperados,
ele interrompe sem tentar adivinhar mudanças.
