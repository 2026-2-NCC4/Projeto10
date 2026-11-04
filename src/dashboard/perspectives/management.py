from dash import html
from ui_elements import page, section, chart, money

def render_management_view(
    index_fig,
    subtitle,
    latest,
    tiles1,
    management_insights,
    trend,
    value_fig,
    risk_fig,
    terminal_children,
    distribution,
):
    
    ebitda_val = latest.ebitda.median() if 'ebitda' in latest.columns else 0
    caixa_val = latest.geracao_caixa.median() if 'geracao_caixa' in latest.columns else 0
    
    status_ebitda = "positivo" if ebitda_val > 0 else "negativo"
    status_caixa = "positiva" if caixa_val > 0 else "deficiente"
    
    desc_trend = f"Evolução Operacional: No ano selecionado, a operação consolida um EBITDA {status_ebitda} de {money(ebitda_val)}."
    desc_value = f"Gestão de Caixa: A operação apresenta uma geração de caixa {status_caixa} de {money(caixa_val)} na mediana."
    desc_risk = "Mapeamento de Riscos: Frequência de cenários onde a concessão apresenta déficit operacional ou quebra de liquidez."
    desc_dist = "Dispersão Operacional: Amplitude de variação do indicador escolhido frente às incertezas da simulação."

  
    return page(
        index_fig,
        subtitle,
        [
            section(
                "Resumo operacional",
                "Receita, resultado e caixa no último ano do recorte.",
                [html.Div(tiles1, className="metrics-grid")],
            ),
            section(
                "Leituras para gestão",
                "Sinais que conectam desempenho, margem e risco de execução no recorte selecionado.",
                [html.Div(management_insights, className="insights-grid")],
            ),
            section(
                "Acompanhamento da operação",
                "Evolução de receita, EBITDA e riscos que exigem ação de gestão.",
                [
                    html.Div(
                        [
                            html.Div([
                                chart(trend),
                                html.P(desc_trend, className="chart-description")
                            ], className="chart-wrapper"),
                            
                            html.Div([
                                chart(value_fig),
                                html.P(desc_value, className="chart-description")
                            ], className="chart-wrapper"),
                            
                            html.Div([
                                chart(risk_fig),
                                html.P(desc_risk, className="chart-description")
                            ], className="chart-wrapper"),
                        ],
                        className="chart-grid",
                    )
                ],
            ),
            *terminal_children,
            section(
                "Distribuição de cenários",
                "Dispersão do indicador operacional selecionado por ano.",
                [
                    html.Div([
                        chart(distribution),
                        html.P(desc_dist, className="chart-description")
                    ], className="chart-wrapper")
                ],
            ),
        ],
    )