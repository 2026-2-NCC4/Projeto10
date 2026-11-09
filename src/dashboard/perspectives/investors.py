from dash import html, dcc
import pandas as pd
from ui_elements import money, percent, card, chart
import plotly.graph_objects as go
from dash_iconify import DashIconify
from metrics_kpi.chart_descriptions import (
    get_trend_description,
    get_value_cash_description,
    get_risk_description,
    get_distribution_description,
)


def _metric_value(data, key, formatter):
    """Retorna uma métrica somente quando a coluna existe na base."""
    if key not in data.columns:
        return None
    value = data[key].median()
    return formatter(value)

def _get_column(data, column):
    """Retorna uma coluna numérica da base."""
    if column not in data.columns:
        raise ValueError(f"Coluna necessária não encontrada na base: {column}")
    return pd.to_numeric(data[column], errors="coerce")

def _investor_metrics(data):
    """Calcula os indicadores financeiros da visão do investidor."""
    lucro_liquido = _get_column(data, "investor_lucro_liquido")
    receita_liquida = _get_column(data, "investor_receita_liquida")
    margem_liquida = _get_column(data, "investor_margem_liquida")
    divida_ebitda = _get_column(data, "investor_divida_ebitda")

    return {
        "lucro_liquido": lucro_liquido.median(),
        "receita_liquida": receita_liquida.median(),
        "margem_liquida": margem_liquida.median(),
        "divida_ebitda": divida_ebitda.median(),
    }

def investor_graph(fig, height=320):
    return dcc.Graph(
        figure=fig,
        config={"displayModeBar": False, "responsive": True},
        className="investor-graph",
        style={"height": f"{height}px", "width": "100%"},
    )

def investor_panel(title, children, class_name="investor-panel"):
    return html.Section(
        [
            html.H3(title, className="investor-panel-title"),
            html.Div(children, className="investor-panel-content"),
        ],
        className=class_name,
    )

def _mini_indicator(label, value, variation=None):
    children = [
        html.Div(label, className="investor-mini-label"),
        html.Div(value, className="investor-mini-value"),
    ]
    if variation is not None:
        children.append(
            html.Div(f"{variation:+.1%} vs. período anterior", className="investor-mini-delta")
        )
    return html.Div(children, className="investor-mini-indicator")

def _median_value(data, column):
    if data is None or data.empty or column not in data.columns:
        return None
    values = pd.to_numeric(data[column], errors="coerce").dropna()
    if values.empty:
        return None
    return values.median()

def _format_percent(value):
    if value is None or pd.isna(value):
        return "—"
    return f"{value:.1f}%".replace(".", ",")

def _format_money_millions(value):
    if value is None or pd.isna(value):
        return "—"
    if abs(value) >= 1_000_000:
        formatted = f"{value / 1_000_000:,.1f}"
        formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {formatted} mi"
    return money(value)

def _calculate_variation(current, previous, percentage_points=False):
    if current is None or previous is None or pd.isna(current) or pd.isna(previous):
        return None
    if percentage_points:
        return current - previous
    if previous == 0:
        return None
    return ((current / previous) - 1) * 100

def _variation_badge(value, suffix):
    if value is None or pd.isna(value):
        text = "Sem comparação"
        color_class = "badge-neutral"
    else:
        positive = value >= 0
        arrow = "↑" if positive else "↓"
        color_class = "badge-positive" if positive else "badge-negative"
        formatted = f"{abs(value):.1f}".replace(".", ",")
        sign = "+" if positive else "-"
        text = f"{arrow} {sign}{formatted} {suffix}"

    return html.Div(text, className=f"investor-badge {color_class}")

def _performance_item(icon, label, value, variation, suffix, icon_color):
    return html.Div(
        [
            html.Div(icon, className="performance-icon", style={"color": icon_color}),
            html.Div(
                [
                    html.Div(label, className="performance-label"),
                    html.Div(value, className="performance-value"),
                ],
                className="performance-text",
            ),
            _variation_badge(variation, suffix),
        ],
        className="performance-item",
    )

def _performance_panel(latest, prev):
    margem = _median_value(latest, "investor_margem_liquida")
    roe = _median_value(latest, "roe")
    roic = _median_value(latest, "roic")
    ebitda = _median_value(latest, "ebitda")

    margem_prev = _median_value(prev, "investor_margem_liquida")
    roe_prev = _median_value(prev, "roe")
    roic_prev = _median_value(prev, "roic")
    ebitda_prev = _median_value(prev, "ebitda")

    roe = roe * 100 if roe is not None else None
    roe_prev = roe_prev * 100 if roe_prev is not None else None
    roic = roic * 100 if roic is not None else None
    roic_prev = roic_prev * 100 if roic_prev is not None else None

    margem_delta = _calculate_variation(margem, margem_prev, percentage_points=True)
    roe_delta = _calculate_variation(roe, roe_prev, percentage_points=True)
    roic_delta = _calculate_variation(roic, roic_prev, percentage_points=True)
    ebitda_delta = _calculate_variation(ebitda, ebitda_prev)

        # Escala visual do medidor
    gauge_min = 0
    gauge_max = 100

    gauge_value = (
        margem
        if margem is not None and not pd.isna(margem)
        else 0
)

    # Limita o valor entre 0% e 100%
    gauge_percent = max(
        0,
        min(
            100,
            ((gauge_value - gauge_min) / (gauge_max - gauge_min)) * 100,
        ),
    )

    # Semicírculo: -90 graus até +90 graus
    needle_angle = -180 + (gauge_percent * 1.8)

    # Preenchimento do arco
    gauge_angle = gauge_percent * 1.8

    gauge = html.Div(
        [
            # Medidor
            html.Div(
                [
                    # Arco colorido
                    html.Div(
                        className="gauge-arc",
                        style={
                                "background": (
                                    f"conic-gradient("
                                    f"from 270deg at 50% 100%, "
                                    f"#a57592 0deg {gauge_angle}deg, "
                                    f"#e5e7eb {gauge_angle}deg 180deg, "
                                    f"transparent 180deg 360deg"
                                    f")"
                                )
                        },
                        children=[
                            html.Div(className="gauge-inner-cover"),
                        ],
                    ),

                    # Agulha
                    html.Div(
                        className="gauge-needle",
                        style={
                            "transform": f"rotate({needle_angle}deg)",
                        },
                    ),

                    # Centro da agulha
                    html.Div(
                        className="gauge-needle-center",
                    ),

                    # Limites da escala
                    html.Span("0%", className="gauge-scale gauge-scale-min"),
                    html.Span("100%", className="gauge-scale gauge-scale-max"),
                ],
                className="gauge-meter",
            ),

            # Valor
            html.Div(
                _format_percent(margem),
                className="gauge-value",
            ),

            html.Div(
                "Margem Líquida",
                className="gauge-label",
            ),

            _variation_badge(
                margem_delta,
                "p.p.",
            ),
        ],
        className="gauge-container",
    )

    indicators = [
        _performance_item(
            DashIconify(icon="lucide:trending-up", width=24, color="#501839"), 
            "ROE", _format_percent(roe), roe_delta, "p.p.", "#501839"
        ),
        _performance_item(
            DashIconify(icon="lucide:coins", width=24, color="#501839"), 
            "ROIC", _format_percent(roic), roic_delta, "p.p.", "#501839"
        ),
        _performance_item(
            DashIconify(icon="lucide:badge-dollar-sign", width=24, color="#501839"), 
            "EBITDA", _format_money_millions(ebitda), ebitda_delta, "%", "#501839"
        ),
    ]

    return html.Div(
        [
            html.Div(
                [
                    html.Span(
                        DashIconify(
                            icon="material-symbols:target",  # ou o nome exato do ícone alvo que deseja
                            width=20, 
                            color="#501839"
                        ), 
                        className="panel-header-icon"
                    ),

                    html.H3("Indicadores de Desempenho", className="panel-header-title"),
                ],
                className="panel-header",
            ),
            html.Div(
                [
                    html.Div(gauge, className="performance-gauge-wrapper"),
                    html.Div(className="performance-divider"),
                    html.Div(indicators, className="performance-indicators"),
                ],
                className="performance-body",
            ),
        ],
        className="performance-panel-container",
    )

def _asset_composition_panel(data):
    colunas = ["BAL Ativo Circulante", "BAL Realizavel a Longo Prazo", "BAL Permanente"]

    if data is None or data.empty:
        return html.Div("Dados insuficientes...", className="investor-panel")

    faltantes = [col for col in colunas if col not in data.columns]
    if faltantes:
        return html.Div(f"Colunas não encontradas: {', '.join(faltantes)}", className="investor-panel")

    df = data[colunas].copy()
    for coluna in colunas:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    df = df.dropna(subset=colunas)
    if df.empty:
        return html.Div("Valores indisponíveis...", className="investor-panel")

    circulante = df["BAL Ativo Circulante"].median()
    realizavel_lp = df["BAL Realizavel a Longo Prazo"].median()
    permanente = df["BAL Permanente"].median()

    labels = ["Ativo Circulante", "Realizavel a Longo Prazo", "Ativo Permanente"]
    valores = [circulante, realizavel_lp, permanente]
    total = sum(valores)

    if total <= 0 or any(pd.isna(v) or v < 0 for v in valores):
        return html.Div("Valores inconsistentes...", className="investor-panel")

    cores = ["#173F7A", "#2563A6", "#60A5FA"]
    percentuais = [(v / total) * 100 for v in valores]

    fig = go.Figure(
        data=[go.Pie(
            labels=labels, values=valores, hole=0.70, sort=False,
            marker=dict(colors=cores), textinfo="none",
            hovertemplate="%{label}<br>Valor: R$ %{value:,.2f}<br>Participação: %{percent:.1%}<extra></extra>",
        )]
    )

    fig.update_layout(
        height=260, showlegend=False, margin=dict(l=5, r=5, t=5, b=5),
        annotations=[dict(
            text=(f"<b>{_format_money_millions(total)}</b><br><span style='font-size:11px'>Total do Ativo</span>"),
            x=0.5, y=0.5, showarrow=False, font=dict(size=15, color="#172033"),
        )],
    )

    legenda = []
    for label, percentual, cor in zip(labels, percentuais, cores):
        legenda.append(
            html.Div(
                [
                    html.Span(className="legend-dot", style={"backgroundColor": cor}),
                    html.Span(label, className="legend-label"),
                    html.Span(f"{percentual:.1f}%".replace(".", ","), className="legend-value"),
                ],
                className="legend-item",
            )
        )

    return html.Div(
        [
            # Cabeçalho do painel unificando ícone e título de forma limpa
            html.Div(
                [
                    DashIconify(
                        icon="energy-icons:chart-pie-slice-20", 
                        width=20, 
                        color="#0284c7"
                    ),
                    html.H3("Composição do Ativo", className="investor-panel-title"),
                ],
                className="panel-header",
                style={
                    "display": "flex", 
                    "alignItems": "center", 
                    "gap": "10px", 
                    "marginBottom": "15px"
                }
            ),
            # Corpo do painel com o gráfico e a legenda
            html.Div(
                [
                    investor_graph(fig, height=260),
                    html.Div(legenda, className="legend-container"),
                ],
                className="asset-composition-grid",
            ),
        ],
        className="investor-panel",
    )
def _evolution_result_panel(data):
    colunas = [
        "Ano",
        "investor_receita_liquida",
        "investor_lucro_liquido",
        "investor_margem_liquida",
    ]

    if data is None or data.empty:
        return html.Div(
            "Dados insuficientes...",
            className="investor-panel",
        )

    faltantes = [
        coluna
        for coluna in colunas
        if coluna not in data.columns
    ]

    if faltantes:
        return html.Div(
            f"Colunas não encontradas: {', '.join(faltantes)}",
            className="investor-panel",
        )

    df = data[colunas].copy()

    df["ano_num"] = pd.to_numeric(
        df["Ano"]
        .astype(str)
        .str.extract(r"(\d+)")[0],
        errors="coerce",
    )

    metricas = [
        "investor_receita_liquida",
        "investor_lucro_liquido",
        "investor_margem_liquida",
    ]

    for coluna in metricas:
        df[coluna] = pd.to_numeric(
            df[coluna],
            errors="coerce",
        )

    df = (
        df.dropna(subset=["ano_num"])
        .groupby("ano_num", as_index=False)[metricas]
        .median()
        .sort_values("ano_num")
    )

    if df.empty:
        return html.Div(
            "Não existem dados válidos para montar o gráfico.",
            className="investor-panel",
        )

    anos = [
        f"Ano {int(ano)}"
        for ano in df["ano_num"]
    ]

    receita = df["investor_receita_liquida"] / 1_000_000
    lucro = df["investor_lucro_liquido"] / 1_000_000
    margem = df["investor_margem_liquida"]

    # Cores do gráfico
    preto = "#111111"
    azul_escuro = "#075985"
    azul_principal = "#0284c7"
    azul_claro = "#38bdf8"
    azul_muito_claro = "#e0f2fe"
    cinza_grid = "#e5e7eb"

    # Configurações das métricas exibidas
    configuracoes = [
        {
            "nome": "Receita",
            "valores": receita,
            "formato": "R$ %{y:,.1f} mi",
            "eixo": "R$ milhões",
        },
        {
            "nome": "Lucro Líquido",
            "valores": lucro,
            "formato": "R$ %{y:,.1f} mi",
            "eixo": "R$ milhões",
        },
        {
            "nome": "Margem",
            "valores": margem,
            "formato": "%{y:.1f}%",
            "eixo": "Percentual (%)",
        },
    ]

    # Criação da figura
    fig = go.Figure()

    for indice, config in enumerate(configuracoes):
        fig.add_trace(
            go.Bar(
                x=anos,
                y=config["valores"],
                name=config["nome"],
                marker=dict(
                    color=azul_escuro,
                    line=dict(
                        color=azul_escuro,
                        width=0,
                    ),
                ),
                opacity=0.95,
                visible=(indice == 0),
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    + config["formato"]
                    + "<extra></extra>"
                ),
            )
        )

        # Linha e pontos em azul-claro
        fig.add_trace(
            go.Scatter(
                x=anos,
                y=config["valores"],
                name="Evolução",
                mode="lines+markers",
                line=dict(
                    color=azul_claro,
                    width=3,
                ),
                marker=dict(
                    size=9,
                    color=azul_claro,
                    line=dict(
                        color=azul_claro,
                        width=2,
                    ),
                ),
                visible=(indice == 0),
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    + config["formato"]
                    + "<extra></extra>"
                ),
            )
        )

    # Botões para alternar as métricas
    botoes = []

    for indice, config in enumerate(configuracoes):
        visibilidade = [False] * len(fig.data)

        visibilidade[indice * 2] = True
        visibilidade[indice * 2 + 1] = True


    fig.update_layout(
        height=370,
        autosize=True,
        showlegend=False,

        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",

        font=dict(
            family="Inter, Segoe UI, Arial, sans-serif",
            color=preto,
            size=12,
        ),

        margin=dict(
            l=55,
            r=25,
            t=70,
            b=45,
        ),

        xaxis=dict(
            title=dict(
                text="Anos",
                font=dict(
                    color=preto,
                    size=12,
                ),
            ),
            showgrid=False,
            showline=True,
            linecolor="#d1d5db",
            linewidth=1,
            zeroline=False,
            tickfont=dict(
                color=preto,
                size=11,
            ),
        ),

        yaxis=dict(
            title=dict(
                text="R$ milhões",
                font=dict(
                    color=preto,
                    size=12,
                ),
            ),
            rangemode="tozero",
            showgrid=True,
            gridcolor=cinza_grid,
            gridwidth=1,
            showline=False,
            zeroline=False,
            tickfont=dict(
                color=preto,
                size=11,
            ),
        ),

        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                buttons=botoes,
                active=0,

                x=1,
                y=1.20,
                xanchor="right",
                yanchor="top",

                bgcolor=azul_muito_claro,
                bordercolor=azul_principal,
                borderwidth=1,

                font=dict(
                    family="Inter, Segoe UI, Arial, sans-serif",
                    color=azul_escuro,
                    size=11,
                ),

                pad=dict(
                    l=8,
                    r=8,
                    t=6,
                    b=6,
                ),

                showactive=True,
            )
        ],

        hovermode="x unified",

        hoverlabel=dict(
            bgcolor="#ffffff",
            bordercolor=azul_claro,
            font=dict(
                color=preto,
                size=12,
            ),
        ),
    )

    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Span(
                                DashIconify(
                                    icon="uis:graph-bar",
                                    width=24,
                                    color=azul_principal,
                                ),
                                className="panel-header-icon",
                            ),
                            html.H3(
                                "Evolução do Resultado",
                                className="panel-header-title",
                            ),
                        ],
                        className="panel-header",
                    ),
                ],
                className="panel-header-wrapper",
            ),

            dcc.Graph(
                id="investor-evolution-chart",
                figure=fig,
                config={
                    "displayModeBar": False,
                    "responsive": True,
                },
                style={
                    "width": "100%",
                    "height": "390px",
                },
            ),
        ],
        className="investor-panel",
    )

def _cash_flow_panel(data):
    required_columns = [
        "FLU Geracao de Caixa", "FLU Investimentos", "FLU Entradas",
        "FLU Despesas Financeiras", "FLU Distribuicao para Acionista",
    ]

    if data is None or data.empty:
        return html.Div("Dados insuficientes...", className="investor-panel")

    missing = [col for col in required_columns if col not in data.columns]
    if missing:
        return html.Div(f"Colunas ausentes: {', '.join(missing)}", className="investor-panel")

    df = data.copy()
    df["ano_num"] = pd.to_numeric(df.get("ano_num", df["Ano"].astype(str).str.extract(r"(\d+)")[0]), errors="coerce")

    for col in required_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["ano_num"])
    if df.empty:
        return html.Div("Não foi possível identificar os anos...", className="investor-panel")

    df["Operacional"] = df["FLU Geracao de Caixa"]
    df["Investimento"] = df["FLU Investimentos"]
    df["Financiamento"] = df["FLU Entradas"] + df["FLU Despesas Financeiras"] + df["FLU Distribuicao para Acionista"]

    yearly = df.groupby("ano_num")[["Operacional", "Investimento", "Financiamento"]].median().sort_index()
    if yearly.empty:
        return html.Div("Não existem dados para montar o gráfico.", className="investor-panel")

    yearly = yearly / 1_000_000
    anos = [f"Ano {int(ano)}" for ano in yearly.index]

    fig = go.Figure()
    series = [("Operacional", "#501839"), ("Investimento", "#f1d6e6"), ("Financiamento", "#a57592")]

    for nome, cor in series:
        fig.add_trace(go.Bar(
            name=nome, x=anos, y=yearly[nome], marker_color=cor,
            hovertemplate=(f"<b>{nome}</b><br>%{{x}}<br>Valor: %{{y:.2f}} mi<extra></extra>"),
        ))

    fig.update_layout(
        barmode="group", height=350, margin=dict(l=15, r=15, t=15, b=35),
        paper_bgcolor="white", plot_bgcolor="white", showlegend=False,
        font=dict(family="Arial", color="#111111", size=12),
        xaxis=dict(title=None, showgrid=True, gridcolor="#EDF1F5", zeroline=False),
        yaxis=dict(
            title=None, range=[-20, 40], tickmode="array", tickvals=[-20, 0, 20, 40],
            ticktext=["-20 mi", "0", "20 mi", "40 mi"], showgrid=True, gridcolor="#E8EDF2",
            zeroline=True, zerolinecolor="#64748B", zerolinewidth=1.5,
        ),
        bargap=0.25, bargroupgap=0.08,
    )

    legenda = html.Div(
        [
            html.Div(
                [
                    html.Span(className="legend-square", style={"backgroundColor": cor}),
                    html.Span(nome),
                ],
                className="legend-item-inline",
            )
            for nome, cor in series
        ],
        className="legend-inline-container",
    )

    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Span(
                                DashIconify(
                                    icon="streamline:graph-arrow-increase",
                                    width=24, 
                                    color="#a57592"
                        ), 
                        className="panel-header-icon"
                    ),
                            html.Span("Fluxo de Caixa", className="panel-header-title"),
                        ],
                        className="panel-header",
                    ),
                    legenda,
                ],
                className="cashflow-header-wrapper",
            ),
            dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"width": "100%"}),
        ],
        className="investor-panel cashflow-panel",
    )

# ==========================================
# FUNÇÃO DOS NOVOS CARDS (IGUAL À IMAGEM)
# ==========================================
def _investor_card_custom(title, value, variation_text, variation_status, theme, sparkline_points, icon_name):
    # Lógica de cores mantida (Azul para positivo, Laranja/Vermelho para negativo)
    if variation_status == "positive":
        bg_color = "#f3fbff"       
        icon_bg = "#E0F2FE"        
        icon_color = "#0284C7"     
        var_color = "#16A34A"      
        arrow = "↑"
    else:
        bg_color = "#f1d6e6"       
        icon_bg = "#a57592"        
        icon_color = "#501839"     
        var_color = "#DC2626"      
        arrow = "↓"

    sparkline_svg = f"""
    <svg viewBox="0 0 70 20" width="70" height="24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display: block; opacity: 0.9;">
        <path d="{sparkline_points}" />
    </svg>
    """

    return html.Div(
        [
            # Topo: Ícone Dinâmico e Título
            html.Div(
                [
                    html.Div(
                        DashIconify(icon=icon_name, width=20, color=icon_color),
                        className="kpi-icon",
                        style={"backgroundColor": icon_bg, "display": "flex", "alignItems": "center", "justifyContent": "center"}
                    ),
                    html.Span(title, className="kpi-title")
                ],
                className="kpi-header"
            ),

            # Meio: Valor e Sparkline
            html.Div(
                [
                    html.Span(value, className="kpi-value"),
                    html.Div(
                        dcc.Markdown(sparkline_svg, dangerously_allow_html=True, style={"margin": "0"}),
                        className="kpi-sparkline-wrapper",
                        style={"display": "flex", "alignItems": "center"}
                    )
                ],
                className="kpi-body"
            ),

            # Base: Variação
            html.Div(
                [
                    html.Span(f"{arrow} {variation_text}", style={"color": var_color, "fontWeight": "bold"}),
                    html.Span(" vs. período anterior", className="kpi-variation-text")
                ],
                className="kpi-footer"
            )
        ],
        className="kpi-card-hover",
        style={"backgroundColor": bg_color}
    )

def render_investor_view(
    index_fig, subtitle, latest, delta, investor_insights, scatter, value_fig,
    balance_fig, terminal_children, distribution, metrics=None, latest_year=1,
    prev=None, risk=None, selected_metric="margem_ebitda", metric_labels=None,
    historical_data=None,
):
    metric_labels = metric_labels or {}
    desc_trend = get_trend_description(
    latest,
    prev,
    latest_year,
    )

    desc_value = get_value_cash_description(
        latest,
        prev,
        latest_year,
    )

    desc_risk = get_risk_description(
        latest,
        risk,
        latest_year,
        perspective="investidores",
    )

    desc_dist = get_distribution_description(
        latest,
        selected_metric,
        metric_labels,
        latest_year,
        perspective="investidores",
    )
    
    if historical_data is None:
        historical_data = latest
    if metrics is None:
        metrics = _investor_metrics(latest) or {}

    def calculate_delta(current_value, previous_value):
        if (
            current_value is None
            or previous_value is None
            or pd.isna(current_value)
            or pd.isna(previous_value)
        ):
            return None

        return current_value - previous_value
    
    # --- MÉTRICAS DO PERÍODO ANTERIOR ---
    if prev is not None and not prev.empty:
        previous_metrics = _investor_metrics(prev) or {}
    else:
        previous_metrics = {}
    
    # --- VALORES ATUAIS ---
    lucro_atual = metrics.get("lucro_liquido", 0)
    receita_atual = metrics.get("receita_liquida", 0)
    margem_atual = metrics.get("margem_liquida", 0)
    divida_atual = metrics.get("divida_ebitda", 0)

    # --- VALORES DO PERÍODO ANTERIOR ---
    lucro_anterior = previous_metrics.get("lucro_liquido")
    receita_anterior = previous_metrics.get("receita_liquida")
    margem_anterior = previous_metrics.get("margem_liquida")
    divida_anterior = previous_metrics.get("divida_ebitda")

    # --- VARIAÇÕES ---
    delta_lucro = calculate_delta(lucro_atual, lucro_anterior)
    delta_receita = calculate_delta(receita_atual, receita_anterior)
    delta_margem = calculate_delta(margem_atual, margem_anterior)
    delta_divida = calculate_delta(divida_atual, divida_anterior)

    # --- VALORES FORMATADOS ---
    lucro = money(lucro_atual)
    receita = money(receita_atual)
    margem = f"{margem_atual:.1f}%".replace(".", ",")
    divida = f"{divida_atual:.1f}x".replace(".", ",")

    # --- CARDS COM O DESIGN PADRÃO ---
    investor_tiles = [
        card(
            "Lucro Líquido",
            lucro,
            delta_lucro,
            subtitle="Resultado após despesas e impostos",
            icon="andrsrxn:wallet",
        ),
        card(
            "Receita Líquida",
            receita,
            delta_receita,
            subtitle="Receita após deduções e impostos",
            icon="cuida:sort-ascending-duotone",
        ),
        card(
            "Margem Líquida",
            margem,
            delta_margem,
            subtitle="Rentabilidade líquida sobre a receita",
            icon="codicon:graph",
        ),
        card(
            "Dívida Líquida / EBITDA",
            divida,
            delta_divida,
            subtitle="Alavancagem financeira da operação",
            icon="codex:money",
        ),
    ]
    
    side_indicators = []
    for key, label, formatter, show_variation in (
        ("margem_ebitda", "Margem EBITDA", percent, True),
        ("roe", "ROE", percent, True),
        ("eva", "EVA", money, False),
    ):
        value = _metric_value(latest, key, formatter)
        if value is not None:
            variation = delta(key) if show_variation else None
            side_indicators.append(_mini_indicator(label, value, variation))

    # 1. Topo: Indicadores de Desempenho e Composição do Ativo (Lado a Lado)
    top_row = html.Div(
        [_performance_panel(latest, prev), _asset_composition_panel(latest)],
        className="investor-top-grid",
    )

    # 2. Base: Evolução e Fluxo de Caixa (Um abaixo do outro)
    bottom_row = html.Div(
        [_evolution_result_panel(historical_data), _cash_flow_panel(historical_data)],
        className="investor-bottom-grid",
    )

    # 3. Container principal que junta as duas linhas
    main_row = html.Div(
        [top_row, bottom_row],
        className="investor-main-layout",
        style={"width": "100%", "display": "flex", "flexDirection": "column", "gap": "24px"}
    )

    return html.Div(
        [
            # CABEÇALHO
            html.Div(
                className="statement-header-card",
                children=[
                    html.H1(
                        "Visão do Investidor",
                        className="statement-title",
                    ),
                    html.P(
                        "Rentabilidade, geração de caixa e criação de valor "
                        "para o capital investido.",
                        className="statement-subtitle",
                    ),
                ],
                style={"marginBottom": "16px"},
            ),

            # RESUMO PARA O INVESTIDOR
            html.Section(
                [
                    html.H2("Resumo para o investidor"),

                    html.P(
                        "Visão consolidada dos principais indicadores de "
                        "rentabilidade, resultado, margem e alavancagem "
                        "financeira no período selecionado.",
                        className="section-subtitle",
                    ),

                    html.Div(
                        investor_tiles,
                        className="metrics-grid",
                    ),
                ],
                className="section-investor",
            ),

            # VISÃO DETALHADA
            html.Section(
                [
                    html.H2("Visão detalhada"),

                    html.P(
                        "Acompanhamento da rentabilidade, evolução dos "
                        "resultados, geração de caixa e composição patrimonial.",
                        className="section-subtitle",
                    ),

                    # Mantém somente os gráficos que já existem
                    main_row,

                    # Texto próprio da visão do investidor
                    html.P(
                        [
                            html.Strong("Análise para o investidor: "),
                            (
                                "Os indicadores detalhados permitem avaliar "
                                "a capacidade de geração de resultado, o retorno "
                                "sobre o capital investido, a evolução da receita "
                                "e a sustentabilidade do fluxo de caixa ao longo "
                                "dos períodos analisados."
                            ),
                        ],
                        className="chart-description",
                    ),
                ],
                className="section",
            ),
        ],
        className="statement-container",
        style={"paddingBottom": "40px"},
    )