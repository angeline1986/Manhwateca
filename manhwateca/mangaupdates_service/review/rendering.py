import html


def score_class(score):
    if score >= 0.9:
        return "score-high"
    if score >= 0.7:
        return "score-medium"
    return "score-low"


def render_candidate(candidate, suggested=False):
    series_id = str(candidate.get("id", ""))
    title = html.escape(str(candidate.get("titulo") or "Sem título"))
    url = html.escape(str(candidate.get("url") or ""), quote=True)
    description = html.escape(
        str(candidate.get("descricao") or "Sem descrição.")
    )
    score = float(candidate.get("pontuacao") or 0)
    row_class = "candidate suggested" if suggested else "candidate"
    link = (
        f"<a class='external' href='{url}' target='_blank' rel='noopener'>"
        "Abrir ficha ↗</a>"
        if url
        else "<span class='muted'>Sem link</span>"
    )
    suggested_label = (
        "<span class='suggested-label'>Melhor resultado</span>"
        if suggested
        else ""
    )
    bl_label = (
        "<span>BL confirmado pela API</span>"
        if candidate.get("bl")
        else ""
    )
    return f"""
    <article class="{row_class}">
      <div class="candidate-head">
        <div>
          <span class="position">#{candidate.get("posicao", "-")}</span>
          <strong>{title}</strong>
          {suggested_label}
        </div>
        <span class="score {score_class(score)}">{score:.2f}</span>
      </div>
      <div class="metadata">
        <span>{html.escape(str(candidate.get("tipo") or "Tipo desconhecido"))}</span>
        <span>{html.escape(str(candidate.get("ano") or "Ano desconhecido"))}</span>
        <span>ID {series_id}</span>
        {bl_label}
      </div>
      <p class="description">{description}</p>
      <div class="candidate-actions">
        {link}
        <button type="button" class="select-button"
          data-id="{html.escape(series_id, quote=True)}"
          data-title="{html.escape(str(candidate.get("titulo") or ""), quote=True)}">
          Selecionar este ID
        </button>
      </div>
    </article>
    """
