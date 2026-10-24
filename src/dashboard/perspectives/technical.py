from dash import html
from ui_elements import page, section, chart


def render_technical_view(
    index_fig, subtitle, tiles2, technical_insights, risk_fig, distribution
):
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
                [chart(risk_fig)],
            ),
            section(
                "Distribuição de cenários",
                "Dispersão do indicador financeiro selecionado por ano.",
                [chart(distribution)],
            ),
        ],
    )
