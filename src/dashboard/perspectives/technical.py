from dash import html
from ui_elements import page, section, chart, ratio


def render_technical_view(
    index_fig, subtitle, latest, tiles2, technical_insights, risk_fig, distribution
):

    liq_val = (
        latest.liquidez_corrente.median()
        if "liquidez_corrente" in latest.columns
        else 0
    )

    status_liq = "confortável" if liq_val >= 1 else "pressionada"

    desc_risk = f"Mapeamento de Risco: Com liquidez de curto prazo {status_liq} ({ratio(liq_val)} na mediana), o gráfico mensura a probabilidade de estresse financeiro."
    desc_dist = "Dispersão Estatística: Volatilidade, amplitude interquartil e limites de confiança (outliers) do indicador sob o blox plot."

    return page(
        index_fig,
        subtitle,
        [
            section(
                "Saúde financeira e controles",
                "Cobertura de curto prazo, estrutura de capital e retorno sobre o ativo.",
                [html.Div(tiles2, className="metrics-grid")],
            ),
            section(
                "Leituras para controle",
                "Interpretações calculadas a partir da mediana e da distribuição dos cenários selecionados.",
                [html.Div(technical_insights, className="insights-grid")],
            ),
            section(
                "Risco financeiro",
                "Probabilidade empírica de eventos de liquidez, resultado e criação de valor.",
                [
                    html.Div(
                        [
                            chart(risk_fig),
                            html.P(desc_risk, className="chart-description"),
                        ],
                        className="chart-wrapper",
                    )
                ],
            ),
            section(
                "Distribuição de cenários",
                "Dispersão do indicador financeiro selecionado por ano.",
                [
                    html.Div(
                        [
                            chart(distribution),
                            html.P(desc_dist, className="chart-description"),
                        ],
                        className="chart-wrapper",
                    )
                ],
            ),
        ],
    )
