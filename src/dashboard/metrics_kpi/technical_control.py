from ui_elements import card, percent, ratio


def build_technical_controls_tiles(latest, prev):
    """Calcula e monta os cartões de controles técnicos e liquidez (tiles2)."""

    def delta(metric):
        if prev.empty or metric not in latest.columns or metric not in prev.columns:
            return None
        return latest[metric].median() - prev[metric].median()

    tiles2 = [
        card(
            "Margem EBITDA",
            percent(latest.margem_ebitda.median()),
            delta("margem_ebitda"),
            subtitle="Rentabilidade operacional",
            icon="iconoven:market-analysis",
        ),
        card(
            "ROA",
            percent(latest.roa.median()),
            delta("roa"),
            subtitle="Retorno sobre ativos",
            icon="cil:graph",
        ),
        card(
            "ROE",
            percent(latest.roe.median()),
            delta("roe"),
            subtitle="Retorno sobre patrimônio",
            icon="iconmind:dep-graph-outline-thin",
        ),
        card(
            "Liquidez corrente",
            ratio(latest.liquidez_corrente.median()),
            subtitle="Cobertura de curto prazo",
            icon="energy-icons:alternating-current-20",
        ),
        card(
            "Liquidez geral",
            ratio(latest.liquidez_geral.median()),
            subtitle="Solvência de longo prazo",
            icon="lucide:droplet",
        ),
    ]

    return tiles2
