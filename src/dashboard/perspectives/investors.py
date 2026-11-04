from dash import html
from ui_elements import page, section, card, chart, money, percent
from metrics_kpi.chart_descriptions import (
    get_scatter_description,
    get_value_cash_description,
    get_balance_description,
    get_distribution_description,
)


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
    latest_year=1,
    prev=None,
    risk=None,
    selected_metric="margem_ebitda",
    metric_labels=None,
):
    """Renderiza a perspectiva de Investidores / Acionistas com descrições dinâmicas aprofundadas."""
    metric_labels = metric_labels or {}

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

    desc_scatter = get_scatter_description(latest, latest_year)
    desc_value = get_value_cash_description(latest, prev, latest_year)
    desc_balance = get_balance_description(latest, latest_year)
    desc_dist = get_distribution_description(
        latest, selected_metric, metric_labels, latest_year, perspective="investidores"
    )

    return page(
        index_fig,
        subtitle,
        [
            section(
                "Retorno ao investidor",
                "Painel consolidado de rentabilidade e criação de riqueza aos acionistas no encerramento do exercício. "
                "Apresenta o resultado operacional (EBITDA), lucro líquido final, fluxo de caixa gerado, "
                "Retorno sobre o Patrimônio Líquido (ROE) e Valor Econômico Agregado (EVA) para avaliar a atratividade do capital investido.",
                [html.Div(investor_tiles, className="metrics-grid")],
            ),
            section(
                "Leituras para decisão de investimento",
                "Teses analíticas de valuation e retorno ajustado ao risco das projeções. "
                "Avalia a consistência da agregação de valor econômico acima do custo de oportunidade do capital (WACC), "
                "a sustentabilidade de dividendos e a assimetria estatística entre os cenários simulados.",
                [html.Div(investor_insights, className="insights-grid")],
            ),
            section(
                "Valor e potencial de retorno",
                "Modelagem integrada de precificação e risco financeiro para patrocinadores. "
                "Cruza a eficiência operacional com a criação de valor por cenário (Margem EBITDA x EVA), "
                "a evolução temporal do caixa livre frente ao EVA, e a decomposição da estrutura patrimonial entre ativos, dívidas e patrimônio líquido.",
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    chart(scatter),
                                    desc_scatter,
                                ],
                                className="chart-wrapper",
                            ),
                            html.Div(
                                [
                                    chart(value_fig),
                                    desc_value,
                                ],
                                className="chart-wrapper",
                            ),
                            html.Div(
                                [
                                    chart(balance_fig),
                                    desc_balance,
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
                "Análise probabilística de sensibilidade dos retornos aos acionistas. "
                "Mapeia a densidade de probabilidades, a concentração nos percentis centrais (Q1–Q3) e as caudas de risco (P10–P90) "
                "da métrica selecionada, quantificando o prêmio de risco do ativo e a probabilidade de perda patrimonial.",
                [
                    html.Div(
                        [
                            chart(distribution),
                            desc_dist,
                        ],
                        className="chart-wrapper",
                    )
                ],
            ),
        ],
    )
