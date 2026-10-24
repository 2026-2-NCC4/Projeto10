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


def create_investor_scatter_chart(latest, latest_year, colors):
    """Cria o gráfico de dispersão (Margem EBITDA vs EVA por cenário)."""
    scatter = px.scatter(
        latest,
        x="margem_ebitda",
        y="eva",
        color="Cenário",
        size="receita",
        size_max=20,
        opacity=0.72,
        title=f"Cenários · margem EBITDA e EVA · Ano {latest_year}",
        labels={"margem_ebitda": "Margem EBITDA", "eva": "EVA (R$)"},
        color_discrete_sequence=[colors["plum"], colors["sky"]],
    )
    scatter.update_xaxes(tickformat=".0%")
    return scatter


def create_value_cash_chart(by_year, colors):
    """Cria o gráfico de linha comparando EVA e Geração de Caixa ao longo do tempo."""
    value_fig = px.line(
        by_year,
        x="ano_calendario",
        y=["eva", "geracao_caixa"],
        markers=True,
        title="EVA e geração de caixa",
        labels={
            "ano_calendario": "Ano calendário",
            "value": "Valor",
            "eva": "EVA",
            "geracao_caixa": "Geração de caixa",
        },
        color_discrete_sequence=[colors["plum"], colors["sky"]],
    )
    value_fig.for_each_trace(
        lambda trace: trace.update(
            name={"eva": "EVA", "geracao_caixa": "Geração de caixa"}[trace.name]
        )
    )
    value_fig.update_yaxes(tickprefix="R$ ", tickformat="~s")
    return value_fig


def create_balance_chart(balance, latest_year):
    """Cria o gráfico de barras da estrutura financeira."""
    balance_fig = px.bar(
        balance,
        x="Componente",
        y="Valor",
        title=f"Estrutura financeira · Ano {latest_year}",
        color="Componente",
        color_discrete_map={
            "Dívida total": "#501839",
            "Caixa disponível": "#55a9e8",
            "Patrimônio líquido": "#7a4b69",
        },
    )
    balance_fig.update_layout(showlegend=False)
    return balance_fig


def create_distribution_chart(operating, selected_metric, metric_labels, colors):
    """Cria o gráfico de caixa (box plot) para a distribuição dos cenários por ano."""
    distribution = px.box(
        operating,
        x="ano_calendario",
        y=selected_metric,
        points=False,
        title=f"Distribuição dos cenários · {metric_labels[selected_metric]}",
        labels={
            "ano_calendario": "Ano calendário",
            selected_metric: metric_labels[selected_metric],
        },
        color_discrete_sequence=[colors["plum"]],
    )
    if selected_metric in {"margem_ebitda", "roa", "roe", "composicao_endividamento"}:
        distribution.update_yaxes(tickformat=".0%")

    return distribution
