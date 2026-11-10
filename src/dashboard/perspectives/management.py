from dash import html
from ui_elements import section, chart
from metrics_kpi.chart_descriptions import (
    get_trend_description,
    get_value_cash_description,
    get_risk_description,
    get_distribution_description,
)


def render_management_view(
    subtitle,
    latest,
    tiles1,
    management_insights,
    trend,
    value_fig,
    risk_fig,
    terminal_children,
    distribution,
    eva_fig=None,          
    cenarios_fig=None,
    latest_year=1,
    prev=None,
    risk=None,
    selected_metric="margem_ebitda",
    metric_labels=None,
):
    """Renderiza a perspectiva de Gestão Executiva com descrições dinâmicas aprofundadas."""
    metric_labels = metric_labels or {}

    desc_trend = get_trend_description(latest, prev, latest_year)
    desc_value = get_value_cash_description(latest, prev, latest_year)
    desc_risk = get_risk_description(latest, risk, latest_year, perspective="gestao")
    desc_dist = get_distribution_description(
        latest, selected_metric, metric_labels, latest_year, perspective="gestao"
    )

    secoes_dashboard = [
        section(
            "Resumo operacional",
            "Visão consolidada do desempenho econômico-financeiro no exercício selecionado. "
            "Apresenta faturamento bruto, margem operacional, lucro líquido, geração de caixa e perfil da dívida "
            "para avaliar a sustentabilidade do negócio e orientar decisões executivas de curto e médio prazo.",
            [html.Div(tiles1, className="metrics-grid")],
        ),

        section(
            "Leituras para gestão",
            "Diagnóstico executivo automatizado que cruza tração de receitas, eficiência operacional e risco de liquidez. "
            "Identifica desvios frente ao ciclo anterior e aponta sinais de alerta fundamentais para respaldar intervenções táticas da diretoria.",
            [html.Div(management_insights, className="insights-grid")],
        ),

        # EVA transformado em um gráfico comum de seção (com fundo branco e padrão igual aos demais)
        section(
            "Criação de Valor (EVA)",
            "Análise evolutiva do Economic Value Added (EVA) ao longo da concessão, medindo a real criação de valor econômico acima do custo de capital.",
            [
                html.Div(
                    [
                        html.Div(
                            [chart(eva_fig) if eva_fig else html.P("EVA indisponível")],
                            className="chart-wrapper"
                        )
                    ],
                    className="chart-grid",
                )
            ],
        ),

        section(
            "Acompanhamento da operação",
            "Monitoramento evolutivo e probabilístico da concessão ao longo dos anos. "
            "Compara a trajetória de expansão e margens operacionais, o confronto entre liquidez e criação de valor econômico "
            "e o mapeamento estocástico de riscos críticos.",
            [
                html.Div(
                    [
                        html.Div(
                            [chart(trend), desc_trend],
                            className="chart-wrapper"
                        ),
                        html.Div(
                            [chart(value_fig), desc_value],
                            className="chart-wrapper"
                        ),
                        html.Div(
                            [chart(risk_fig), desc_risk],
                            className="chart-wrapper"
                        ),
                    ],
                    className="chart-grid",
                )
            ],
        ),

        *terminal_children,

        section(
            "Distribuição de cenários",
            "Análise estocástica de sensibilidade e dispersão baseada nas iterações de Monte Carlo.",
            [
                html.Div(
                    [chart(distribution), desc_dist],
                    className="chart-wrapper",
                )
            ],
        ),
    ]

    return html.Div(
        [
            # CABEÇALHO DA PÁGINA
            html.Div(
                className="statement-header-card",
                children=[
                    html.H1(
                        "Visão do Gestor",
                        className="statement-title"
                    ),
                    html.P(
                        subtitle,
                        className="statement-subtitle"
                    ),
                ],
                style={"marginBottom": "24px"}
            ),

            # CORPO COM AS SEÇÕES EM PILHA
            html.Div(
                secoes_dashboard,
                className="management-main-layout",
                style={"display": "flex", "flexDirection": "column", "gap": "24px"}
            )
        ],
        className="statement-container",
        style={"paddingBottom": "40px"}
    )