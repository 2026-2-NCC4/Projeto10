import re
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

def create_eva_figure(w):
    """Gera o gráfico de EVA médio por ano exibindo explicitamente os anos no eixo X."""
    if w is None or w.empty or 'eva' not in w.columns:
        fig = go.Figure()
        fig.update_layout(
            title="EVA Médio por Ano (Aguardando base de dados)",
            height=320,
            plot_bgcolor="white",
            paper_bgcolor="white"
        )
        return fig
    
    # Agrupa por ano_num e calcula a média do EVA em milhões
    eva_medio = w.groupby('ano_num')['eva'].mean() / 1_000_000
    
    # Garante que os rótulos do eixo X fiquem claros (ex: "Ano 1", "Ano 2" ou apenas o número do ano)
    anos = [int(a) for a in eva_medio.index]
    
    fig = go.Figure(data=[
        go.Bar(
            x=anos,
            y=eva_medio.values,
            marker_color="#501839",
            hovertemplate="<b>Ano %{x}</b><br>EVA Médio: R$ %{y:,.2f} mi<extra></extra>"
        )
    ])
    fig.update_layout(
        title="EVA Médio por Ano (Criação de Valor)",
        xaxis_title="Ano da Concessão",
        yaxis_title="R$ milhões",
        height=320,
        margin=dict(l=40, r=20, t=40, b=30),
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(
            type="category", # Força o eixo X a tratar cada ano como uma categoria distinta para exibir todos os rótulos
            tickmode="linear"
        )
    )
    return fig


def create_cenarios_figure(w, ano_selecionado=1):
    """Gera o gráfico de barras com a contagem das categorias de cenários com proteção contra None."""
    if w is None or w.empty or 'categoria_cenario' not in w.columns:
        fig = go.Figure()
        fig.update_layout(
            title=f"Classificação dos Cenários (Ano {ano_selecionado}) - Aguardando base",
            height=320,
            plot_bgcolor="white",
            paper_bgcolor="white"
        )
        return fig

    df_ano = w[w['ano_num'] == ano_selecionado]
    
    if df_ano.empty:
        fig = go.Figure()
        fig.update_layout(
            title=f"Classificação dos Cenários (Ano {ano_selecionado}) - Sem dados",
            height=320,
            plot_bgcolor="white",
            paper_bgcolor="white"
        )
        return fig

    contagem = df_ano['categoria_cenario'].value_counts()
    
    fig = go.Figure(data=[
        go.Bar(
            x=contagem.index,
            y=contagem.values,
            marker_color="#a57592",
            hovertemplate="<b>%{x}</b><br>Qtd. Cenários: %{y}<extra></extra>"
        )
    ])
    fig.update_layout(
        title=f"Classificação dos 1.200 Cenários (Ano {ano_selecionado})",
        xaxis_title="Categoria",
        yaxis_title="Nº de Cenários",
        height=320,
        margin=dict(l=40, r=20, t=40, b=80),
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(tickangle=-20)
    )
    return fig

def pretty_label(col_name: str) -> str:
    """Convert snake_case column names to Title Case with spaces.
    Example: "ano_calendario" -> "Ano Calendário".
    """
    # Replace underscores with spaces and capitalize each word
    return " ".join(word.capitalize() for word in col_name.split("_"))


def create_trend_chart(by_year, colors):
    """Cria o gráfico de área de Receita com a linha de EBITDA sobreposta."""
    trend = px.area(
        by_year,
        x="ano_calendario",
        y="receita",
        title="Receita ao longo da concessão",
        labels={"ano_calendario": "Ano calendário", "receita": "Receita"},
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
    """Cria o mapa de calor de probabilidade do mapa de risco."""
    if risk_long.empty:
        return go.Figure().update_layout(title="Mapa de risco · probabilidade por ano")

    risk_matrix = risk_long.pivot(
        index="Evento", columns="ano_calendario", values="Probabilidade"
    )

    risk_fig = px.imshow(
        risk_matrix,
        text_auto=".0%",
        color_continuous_scale=["white", "#501839"],
        title="Mapa de risco · probabilidade por ano",
        aspect="auto",
        labels=dict(x="Ano calendário", y="", color="Probabilidade"),
    )

    # Força a exibição de todos os anos no eixo X e esconde o eixo de cores (já tem texto)
    risk_fig.update_xaxes(type="category")
    risk_fig.update_layout(coloraxis_showscale=False)

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
    """Cria o gráfico de eixos duplos comparando EVA (linha) e Geração de Caixa (barras)."""
    if by_year.empty:
        return go.Figure()
    value_fig = make_subplots(specs=[[{"secondary_y": True}]])

    value_fig.add_trace(
        go.Bar(
            x=by_year["ano_calendario"],
            y=by_year["geracao_caixa"],
            name="Geração de caixa",
            marker_color=colors.get("sky", "#55a9e8"),
        ),
        secondary_y=False,
    )
    value_fig.add_trace(
        go.Scatter(
            x=by_year["ano_calendario"],
            y=by_year["eva"],
            name="EVA",
            mode="lines+markers",
            line=dict(color=colors.get("plum", "#501839"), width=3),
        ),
        secondary_y=True,
    )

    value_fig.update_layout(
        title="EVA e Geração de caixa",
        plot_bgcolor="white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    value_fig.update_xaxes(
        title_text="Ano calendário", type="category", showgrid=True, gridcolor="#e5e7eb"
    )
    value_fig.update_yaxes(
        tickprefix="R$ ",
        tickformat="~s",
        secondary_y=False,
        showgrid=True,
        gridcolor="#e5e7eb",
    )
    value_fig.update_yaxes(
        tickprefix="R$ ", tickformat="~s", secondary_y=True, showgrid=False
    )

    return value_fig


def create_balance_chart(balance, latest_year):
    """Cria o gráfico de cascata (waterfall) da estrutura financeira."""
    if balance.empty:
        return go.Figure()

    balance_fig = go.Figure(
        go.Waterfall(
            name="Estrutura",
            orientation="v",
            measure=["relative"] * len(balance),
            x=balance["Componente"],
            y=balance["Valor"],
            text=balance["Valor"],
            textposition="outside",
            connector={"line": {"color": "#9ca3af"}},
            increasing={"marker": {"color": "#501839"}},
            decreasing={"marker": {"color": "#55a9e8"}},
            totals={"marker": {"color": "#7a4b69"}},
        )
    )

    balance_fig.update_layout(
        title=f"Estrutura financeira · Ano {latest_year}",
        showlegend=False,
        plot_bgcolor="white",
    )
    balance_fig.update_traces(texttemplate="R$ %{text:.2s}")

    return balance_fig


def create_distribution_chart(operating, selected_metric, metric_labels, colors):
    """Cria o gráfico de violino para a densidade de distribuição dos cenários por ano."""
    distribution = px.violin(
        operating,
        x="ano_calendario",
        y=selected_metric,
        box=True,
        points=False,
        title=f"Densidade e distribuição dos cenários · {metric_labels.get(selected_metric, selected_metric)}",
        labels={
            "ano_calendario": "Ano calendário",
            selected_metric: metric_labels.get(selected_metric, selected_metric),
        },
        color_discrete_sequence=[colors.get("plum", "#501839")],
    )

    distribution.update_layout(plot_bgcolor="white")
    distribution.update_xaxes(type="category", showgrid=True, gridcolor="#e5e7eb")

    if selected_metric in {"margem_ebitda", "roa", "roe", "composicao_endividamento"}:
        distribution.update_yaxes(tickformat=".0%", showgrid=True, gridcolor="#e5e7eb")
    else:
        distribution.update_yaxes(showgrid=True, gridcolor="#e5e7eb")

    return distribution
