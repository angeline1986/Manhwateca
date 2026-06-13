import html


def render_summary_cards(cards):
    parts = ["<div class='summary-grid' aria-label='Resumo'>"]
    for card in cards:
        parts.append(
            "<div class='summary-card'><div class='summary-label'>{label}</div>"
            "<div class='summary-value'>{value}</div></div>".format(
                label=html.escape(str(card["label"])),
                value=html.escape(str(card["value"])),
            )
        )
    parts.append("</div>")
    return "\n".join(parts)
