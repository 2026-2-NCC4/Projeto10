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
        ),
        card("ROA", percent(latest.roa.median()), delta("roa")),
        card("ROE", percent(latest.roe.median()), delta("roe")),
        card("Liquidez corrente", ratio(latest.liquidez_corrente.median())),
        card("Liquidez geral", ratio(latest.liquidez_geral.median())),
    ]
    
    return tiles2