from dash import html
from ui_elements import page, section, card, chart, money, percent


def render_investor_view(
    index_fig,
    subtitle,
    latest,
    delta,
    investor_insights,
    scatter,
    value_fig,
    balance_fig,
    terminal_children,
    distribution,
):
    investor_tiles = [
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
        card("ROE", percent(latest.roe.median()), delta("roe")),
        card("EVA", money(latest.eva.median()), delta("eva")),
    ]
    return page(
        index_fig,
        subtitle,
        [
            section(
                "Retorno ao investidor",
                "Resultado, caixa e criação de valor no último ano do recorte.",
                [html.Div(investor_tiles, className="metrics-grid")],
            ),
            section(
                "Leituras para decisão de investimento",
                "O retorno é apresentado com sua incerteza; os textos acompanham o recorte de anos e cenários aplicado.",
                [html.Div(investor_insights, className="insights-grid")],
            ),
            section(
                "Valor e potencial de retorno",
                "Relação entre rentabilidade, criação de valor, caixa e estrutura de capital.",
                [
                    html.Div(
                        [chart(scatter), chart(value_fig), chart(balance_fig)],
                        className="chart-grid",
                    )
                ],
            ),
            *terminal_children,
            section(
                "Distribuição de cenários",
                "Amplitude dos retornos e indicadores observados nos cenários selecionados.",
                [chart(distribution)],
            ),
        ],
    )
