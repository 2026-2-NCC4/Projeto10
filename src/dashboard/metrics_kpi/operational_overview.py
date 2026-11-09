from ui_elements import card, money


def build_operational_overview_tiles(latest, prev):
    """Calcula as variações e monta os cartões operacionais."""
    
    def delta(metric):
        if prev.empty or metric not in latest.columns or metric not in prev.columns:
            return None

        return latest[metric].median() - prev[metric].median()

    tiles1 = [
        card(
            "Receita",
            money(latest.receita.median()),
            delta("receita"),
            subtitle="Faturamento consolidado",
            icon="cuida:sort-ascending-duotone",
        ),
        card(
            "EBITDA",
            money(latest.ebitda.median()),
            delta("ebitda"),
            subtitle="Resultado operacional",
            icon="iconoven:currency-real",
        ),
        card(
            "Resultado líquido",
            money(latest.resultado_liquido.median()),
            delta("resultado_liquido"),
            subtitle="Resultado após despesas e impostos",
            icon="cuida:sort-ascending-duotone",
        ),
        card(
            "Geração de caixa",
            money(latest.geracao_caixa.median()),
            delta("geracao_caixa"),
            subtitle="Caixa gerado pela operação",
            icon="entypo:line-graph",
        ),
        card(
            "Dívida total",
            money(latest.divida_total.median()),
            delta("divida_total"),
            subtitle="Endividamento consolidado",
            icon="andrsrxn:money-bag",
        ),
    ]

    return tiles1