from dash import html
from ui_elements import page, section, chart
from metrics_kpi.chart_descriptions import (
    get_risk_description,
    get_distribution_description,
)


def render_technical_view(
    index_fig,
    subtitle,
    latest,
    tiles2,
    technical_insights,
    risk_fig,
    distribution,
    latest_year=1,
    prev=None,
    risk=None,
    selected_metric="liquidez_corrente",
    metric_labels=None,
):
    """Renderiza a perspectiva Técnica / Controladoria com descrições dinâmicas aprofundadas."""
    metric_labels = metric_labels or {}

    desc_risk = get_risk_description(latest, risk, latest_year, perspective="tecnica")
    desc_dist = get_distribution_description(
        latest, selected_metric, metric_labels, latest_year, perspective="tecnica"
    )

    return html.Div(
    [
        html.Div(
            [
                html.H1(
                    "Visão Técnica",
                    className="statement-title",
                ),
                html.P(
                    "Solidez financeira, controles prudenciais e monitoramento dos riscos do negócio.",
                    className="statement-subtitle",
                ),
            ],
            className="statement-header-card",
            style={"marginBottom": "24px"},
        ),

        # CONTEÚDO DA PÁGINA
        page(
            index_fig,
            subtitle,
            [
                section(
                    "Saúde financeira e controles",
                    "Painel de controle contábil e auditoria financeira prudencial. "
                    "Avalia a suficiência de liquidez corrente, os índices de cobertura de obrigações de curto prazo, "
                    "a proporção de capital de terceiros frente aos recursos próprios e o retorno dos ativos operacionais (ROA) "
                    "para garantir aderência a covenants e diretrizes de tesouraria.",
                    [html.Div(tiles2, className="metrics-grid")],
                ),

                section(
                    "Leituras para controle",
                    "Alertas técnicos de conformidade e solvência patrimonial baseados na mediana e dispersão das projeções. "
                    "Evidencia a margem de folga do capital circulante líquido, a dependência de passivos onerosos e a faixa de incerteza "
                    "estatística para subsidiar o controle interno e a governança orçamentária.",
                    [html.Div(technical_insights, className="insights-grid")],
                ),

                section(
                    "Risco financeiro",
                    "Matriz quantitativa de vulnerabilidade estrutural calibrada pelas simulações de Monte Carlo. "
                    "Calcula a probabilidade empírica de rompimento de limites prudenciais, como liquidez abaixo de 1,0x, "
                    "saldo de caixa descoberto, prejuízo contábil e destruição de valor, para embasar testes de estresse "
                    "e dimensionamento de garantias.",
                    [
                        html.Div(
                            [
                                chart(risk_fig),
                                desc_risk,
                            ],
                            className="chart-wrapper",
                        )
                    ],
                ),

                section(
                    "Distribuição de cenários",
                    "Distribuição estatística contínua, com Box Plot e Densidade de Violino, do indicador financeiro selecionado "
                    "ao longo da concessão. Permite examinar a simetria de resultados, a amplitude interquartil (IQR) e os riscos "
                    "de cauda, como outliers, para calibração de bandas de controle e limites de compliance.",
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
        ),
    ],
    className="statement-container",
    style={"paddingBottom": "40px"},
)
