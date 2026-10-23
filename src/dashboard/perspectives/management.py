from dash import html
from ui_elements import page, section, chart

def render_management_view(index_fig, subtitle, tiles1, management_insights, trend, value_fig, risk_fig, terminal_children, distribution):
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
                        [chart(trend), chart(value_fig), chart(risk_fig)],
                        className="chart-grid",
                    )
                ],
            ),
            *terminal_children,
            section(
                "Distribuição de cenários",
                "Dispersão do indicador operacional selecionado por ano.",
                [chart(distribution)],
            ),
        ],
    )