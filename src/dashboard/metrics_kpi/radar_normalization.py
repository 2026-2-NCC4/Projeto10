# src/dashboard/metrics_kpis/radar_normalization.py
import pandas as pd


def compute_radar_scores(operating, latest):
    """Normaliza as métricas operacionais contra os percentis 5 e 95 para o gráfico radial."""
    radar_metrics = [
        ("Margem", "margem_ebitda"),
        ("ROE", "roe"),
        ("Liquidez", "liquidez_corrente"),
        ("EVA", "eva"),
        ("Caixa", "geracao_caixa"),
        ("Receita", "receita"),
    ]

    radar_values = []
    for label, key in radar_metrics:
        if operating.empty or key not in operating.columns or key not in latest.columns:
            radar_values.append((label, 50))
            continue

        vals, med = operating[key].dropna(), latest[key].median()
        lo, hi = vals.quantile(0.05), vals.quantile(0.95)
        score = (
            50
            if pd.isna(med) or hi == lo
            else max(8, min(100, 12 + 88 * (med - lo) / (hi - lo)))
        )
        radar_values.append((label, score))

    return radar_values
