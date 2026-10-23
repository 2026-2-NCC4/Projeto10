import plotly.express as px
import plotly.graph_objects as go

def create_trend_chart(by_year, colors):
    """Cria o gráfico de área de Receita com a linha de EBITDA sobreposta."""
    trend = px.area(
        by_year,
        x="ano_calendario",
        y="receita",
        title="Receita ao longo da concessão",
        color_discrete_sequence=[colors["teal"]],
    )
    trend.add_trace(
        go.Scatter(
            x=by_year.ano_calendario,
            y=by_year.ebitda,
            mode="lines+markers",
            name="EBITDA",
            line={"color": colors["amber"], "width": 3},
            marker={"size": 7},
        )
    )
    trend.update_yaxes(tickprefix="R$ ", tickformat="~s")
    return trend

def create_risk_chart(risk_long, risk_labels):
    """Cria o gráfico de área empilhada/probabilidade do mapa de risco."""
    if risk_long.empty:
        return px.title(title="Mapa de risco · probabilidade por ano")

    risk_fig = px.area(
        risk_long,
        x="ano_calendario",
        y="Probabilidade",
        color="Evento",
        title="Mapa de risco · probabilidade por ano",
        labels={"ano_calendario": "Ano calendário"},
        color_discrete_map={
            risk_labels["prejuizo"]: "#501839",
            risk_labels["caixa_negativo"]: "#55a9e8",
            risk_labels["liquidez_critica"]: "#7a4b69",
            risk_labels["eva_negativo"]: "#2e7fb9",
        },
    )
    risk_fig.update_yaxes(tickformat=".0%")
    return risk_fig

