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

    eva_val = latest.eva.median()
    caixa_val = latest.geracao_caixa.median()
    res_liq_val = latest.resultado_liquido.median()

    margem_val = (
        latest.margem_ebitda.median() if "margem_ebitda" in latest.columns else 0
    )
    endiv_val = (
        latest.endividamento.median() if "endividamento" in latest.columns else 0
    )

    status_eva = "criação" if eva_val > 0 else "destruição"
    status_caixa = "positiva" if caixa_val > 0 else "negativa"
    status_lucro = "lucro" if res_liq_val > 0 else "prejuízo"

    desc_scatter = f"Risco-Retorno: Com margem EBITDA mediana de {percent(margem_val)}, a operação projeta {status_eva} de valor ({money(eva_val)})."
    desc_value = f"Trajetória de Caixa: A geração de caixa {status_caixa} de {money(caixa_val)} sustenta a projeção de valor livre."
    desc_balance = f"Estrutura de Capital: O nível de endividamento da concessão atinge {percent(endiv_val)} no ano atual."
    desc_dist = f"Dispersão de Risco: Ao longo dos cenários, a tendência central consolida um {status_lucro} de {money(res_liq_val)}."

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
                        [
                            html.Div(
                                [
                                    chart(scatter),
                                    html.P(desc_scatter, className="chart-description"),
                                ],
                                className="chart-wrapper",
                            ),
                            html.Div(
                                [
                                    chart(value_fig),
                                    html.P(desc_value, className="chart-description"),
                                ],
                                className="chart-wrapper",
                            ),
                            html.Div(
                                [
                                    chart(balance_fig),
                                    html.P(desc_balance, className="chart-description"),
                                ],
                                className="chart-wrapper",
                            ),
                        ],
                        className="chart-grid",
                    )
                ],
            ),
            *terminal_children,
            section(
                "Distribuição de cenários",
                "Amplitude dos retornos e indicadores observados nos cenários selecionados.",
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
