from ui_elements import card, money

def build_operational_overview_tiles(latest, prev):
    """Calcula as variações e monta os cartões operacionais (tiles1) da visão geral."""
    
    def delta(metric):
        if prev.empty or metric not in latest.columns or metric not in prev.columns:
            return None
        return latest[metric].median() - prev[metric].median()

    tiles1 = [
        card("Receita", money(latest.receita.median()), delta("receita")),
        card("EBITDA", money(latest.ebitda.median()), delta("ebitda")),
        card(
            "Resultado líquido",
            money(latest.resultado_liquido.median()),
            delta("resultado_liquido"),
        ),
        card(
            "Geração de caixa",
            money(latest.geracao_caixa.median()),
            delta("geracao_caixa"),
        ),
        card(
            "Dívida total", money(latest.divida_total.median()), delta("divida_total")
        ),
    ]
    
    return tiles1