from dash import html, dcc
import pandas as pd
from ui_elements import money, percent
import plotly.graph_objects as go
from dash_svg import Svg, Path
from dash_iconify import DashIconify


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

    gauge_max = 20
    gauge_value = margem if margem is not None and not pd.isna(margem) else 0
    gauge_fill = max(0, min(100, (gauge_value / gauge_max) * 100))
    gauge_angle = gauge_fill * 1.8

    gauge = html.Div(
        [
            html.Div(
                className="gauge-arc",
                style={
                    "background": (
                        f"conic-gradient(from 270deg at 50% 100%, "
                        f"#10B981 0deg {gauge_angle}deg, "
                        f"#E5E7EB {gauge_angle}deg 180deg, "
                        f"transparent 180deg 360deg)"
                    )
                },
                children=[html.Div(className="gauge-inner-cover")]
            ),
            html.Div(_format_percent(margem), className="gauge-value"),
            html.Div("Margem Líquida", className="gauge-label"),
            _variation_badge(margem_delta, "p.p."),
        ],
        className="gauge-container",
    )

    indicators = [
        _performance_item(
            DashIconify(icon="lucide:trending-up", width=24, color="#0284c7"), 
            "ROE", _format_percent(roe), roe_delta, "p.p.", "#0284c7"
        ),
        _performance_item(
            DashIconify(icon="lucide:coins", width=24, color="#0284c7"), 
            "ROIC", _format_percent(roic), roic_delta, "p.p.", "#0284c7"
        ),
        _performance_item(
            DashIconify(icon="lucide:badge-dollar-sign", width=24, color="#0284c7"), 
            "EBITDA", _format_money_millions(ebitda), ebitda_delta, "%", "#0284c7"
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
                            color="#0284c7"
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
    colunas = ["Ano", "investor_receita_liquida", "investor_lucro_liquido", "investor_margem_liquida"]
    faltantes = [c for c in colunas if c not in data.columns]

    if data is None or data.empty or faltantes:
        return html.Div("Dados insuficientes...", className="investor-panel")

    df = data[colunas].copy()
    df["ano_num"] = pd.to_numeric(df["Ano"].astype(str).str.extract(r"(\d+)")[0], errors="coerce")
    metricas = ["investor_receita_liquida", "investor_lucro_liquido", "investor_margem_liquida"]

    for coluna in metricas:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    df = df.dropna(subset=["ano_num"]).groupby("ano_num", as_index=False)[metricas].median().sort_values("ano_num")
    anos = [f"Ano {int(a)}" for a in df["ano_num"]]

    receita = df["investor_receita_liquida"] / 1_000_000
    lucro = df["investor_lucro_liquido"] / 1_000_000
    margem = df["investor_margem_liquida"]

    fig = go.Figure()
    configuracoes = [
        {"nome": "Receita", "valores": receita, "formato": "R$ %{y:,.1f} mi", "eixo": "R$ milhões"},
        {"nome": "Lucro Líquido", "valores": lucro, "formato": "R$ %{y:,.1f} mi", "eixo": "R$ milhões"},
        {"nome": "Margem", "valores": margem, "formato": "%{y:.1f}%", "eixo": "Percentual (%)"},
    ]

    for indice, config in enumerate(configuracoes):
        fig.add_trace(go.Bar(
            x=anos, y=config["valores"], name=config["nome"], marker_color="#2563A6",
            opacity=0.85, visible=(indice == 0),
            hovertemplate=("<b>%{x}</b><br>" + config["formato"] + "<extra></extra>"),
        ))
        fig.add_trace(go.Scatter(
            x=anos, y=config["valores"], name="Evolução", mode="lines+markers",
            line=dict(color="#173F7A", width=3), marker=dict(size=7, color="#173F7A"),
            visible=(indice == 0),
            hovertemplate=("<b>%{x}</b><br>" + config["formato"] + "<extra></extra>"),
        ))

    botoes = []
    for indice, config in enumerate(configuracoes):
        visibilidade = [False] * 6
        visibilidade[indice * 2] = True
        visibilidade[indice * 2 + 1] = True
        botoes.append(dict(
            label=config["nome"], method="update",
            args=[{"visible": visibilidade}, {"yaxis": {"title": config["eixo"], "rangemode": "tozero"}}],
        ))

    fig.update_layout(
        height=370, autosize=True, showlegend=False, paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
        font=dict(family="Inter, Segoe UI, Arial, sans-serif", color="#172033", size=12),
        margin=dict(l=55, r=25, t=65, b=45),
        xaxis=dict(title=None, showgrid=False, linecolor="#E5E7EB", tickfont=dict(color="#64748B")),
        yaxis=dict(title="R$ milhões", rangemode="tozero", showgrid=True, gridcolor="#E8EEF6", zeroline=False, tickfont=dict(color="#64748B")),
        updatemenus=[dict(
            type="buttons", direction="right", buttons=botoes, active=0,
            x=1, y=1.19, xanchor="right", yanchor="top",
            bgcolor="#F1F5F9", bordercolor="#E2E8F0", borderwidth=1,
            font=dict(color="#173F7A", size=11), pad=dict(l=4, r=4, t=4, b=4),
        )],
        hovermode="x unified",
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
                                    color="#0284c7"
                                ), 
                                className="panel-header-icon"
                            ),
                            html.H3("Evolução do Resultado", className="panel-header-title"),
                        ],
                        className="panel-header",
                    ),
                    html.Span("⛶", title="Expandir gráfico", className="panel-expand-icon"),
                ],
                className="panel-header-wrapper",
            ),
            dcc.Graph(
                id="investor-evolution-chart", figure=fig,
                config={"displayModeBar": False, "responsive": True},
                style={"width": "100%", "height": "390px"},
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
    series = [("Operacional", "#173F7A"), ("Investimento", "#2563A6"), ("Financiamento", "#60A5FA")]

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
                            color="#0284c7"
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
        bg_color = "#FFF9F5"       
        icon_bg = "#FFEDD5"        
        icon_color = "#EA580C"     
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
    if historical_data is None:
        historical_data = latest
    if metrics is None:
        metrics = _investor_metrics(latest) or {}

    # --- CRIAÇÃO DOS 4 CARDS ---
    lucro = money(metrics.get("lucro_liquido", 0))
    receita = money(metrics.get("receita_liquida", 0))
    margem = f"{metrics.get('margem_liquida', 0):.1f}%".replace(".", ",")
    divida = f"{metrics.get('divida_ebitda', 0):.1f}x".replace(".", ",")

    investor_tiles = [
         _investor_card_custom(
            title="Lucro Líquido", 
            value=lucro, 
            variation_text="+18,5%", 
            variation_status="positive", 
            theme="blue", 
            sparkline_points="M0,18 L15,12 L25,15 L40,5 L55,8 L70,0",
            icon_name="ph:trend-up"  # <--- Ícone de linha subindo
        ),
        _investor_card_custom(
            title="Receita Líquida", 
            value=receita, 
            variation_text="+12,3%", 
            variation_status="positive", 
            theme="blue", 
            sparkline_points="M0,20 L10,15 L20,18 L35,10 L50,12 L65,8 L70,8",
            icon_name="ph:currency-circle-dollar"  # <--- Ícone de moeda
        ),
        _investor_card_custom(
            title="Margem Líquida", 
            value=margem, 
            variation_text="+1,2 p.p.", 
            variation_status="positive", 
            theme="blue", 
            sparkline_points="M0,15 L15,15 L25,10 L40,18 L55,12 L70,5",
            icon_name="ph:percent"  # <--- Ícone de porcentagem
        ),
        _investor_card_custom(
            title="Dívida Líquida / EBITDA", 
            value=divida, 
            variation_text="-0,1x", 
            variation_status="negative", 
            theme="orange", 
            sparkline_points="M0,10 L15,15 L30,8 L45,18 L60,15 L70,18",
            icon_name="ph:scales"  # <--- Ícone de balança (endividamento)
        )
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
            # 1. CABEÇALHO EM CARD (Estilo Demonstrativo)
            html.Div(
                className="statement-header-card",
                children=[
                    html.H1(
                        "Visão do Investidor", 
                        className="statement-title" # Usa a classe do CSS
                    ),
                    html.P(
                        "Rentabilidade, geração de caixa e criação de valor para o capital investido.",
                        className="statement-subtitle" # Usa a classe do CSS
                    ),
                ],
                style={"marginBottom": "24px"} # Dá um espaço entre o card do título e os gráficos abaixo
            ),
            
            # 2. CARDS KPI (Lado a lado)
            html.Div(
                investor_tiles, 
                className="metrics-grid investor-kpi-grid",
                style={
                    "display": "grid", 
                    "gridTemplateColumns": "repeat(4, 1fr)", 
                    "gap": "20px", 
                    "marginBottom": "30px",
                    "width": "100%"
                }
            ),
            
            # 3. CONTEÚDO DOS GRÁFICOS
            main_row
        ],
        className="statement-container", # Aplica o fundo cinza #f8fafc e o padding geral
        style={"paddingBottom": "40px"} # Um respiro extra no final da página
    )