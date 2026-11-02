# src/dashboard/perspectives/dashboard_layout.py
from dash import html, dcc, dash_table
from ui_elements import row, panel

DFC_ROWS = (
    ("Recebimentos de Receita", "FLU Receita"),
    ("(-) Tributos", "FLU Tributos"),
    ("(-) Custos", "FLU Custos"),
    ("(-) Investimentos", "FLU Investimentos"),
    ("Entradas Financeiras", "FLU Entradas"),
    ("(-) Despesas Financeiras", "FLU Despesas Financeiras"),
    ("Resultado Financeiro", "FLU Resultado Financeiro"),
    (
        "(-) Imposto de Renda e Contribuição Social",
        "FLU Imposto de Renda e Contribuicao Social",
    ),
    ("(-) Distribuição para Acionistas", "FLU Distribuicao para Acionista"),
    ("GERAÇÃO DE CAIXA", "FLU Geracao de Caixa"),
    ("Saldo Inicial de Caixa", "FLU Saldo Inicial"),
    ("Saldo Final de Caixa", "FLU Saldo Final"),
)


def _brl(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def build_dfc_table(data, years, scenario):
    cash_flow = data.loc[data["Cenário"].eq(scenario)].set_index("Ano")
    columns = [f"Ano {year}" for year in years]
    return html.Table(
        [
            html.Thead(
                html.Tr(
                    [html.Th("Conta", scope="col")]
                    + [html.Th(year, scope="col") for year in columns]
                )
            ),
            html.Tbody(
                [
                    html.Tr(
                        [html.Th(label, scope="row")]
                        + [
                            html.Td(_brl(cash_flow.at[year, account]))
                            for year in columns
                        ],
                        className=(
                            "dfc-total"
                            if account in {"FLU Geracao de Caixa", "FLU Saldo Final"}
                            else ""
                        ),
                    )
                    for label, account in DFC_ROWS
                ]
            ),
        ],
        className="dfc-table",
    )


def create_main_layout(
    years, scenarios, perspectives, perspective_metrics, metric_labels, data
):
    """Constrói a árvore DOM completa do layout principal do painel (Sidebar e Main)."""
    print("ENTROU NA FUNÇÃO CREATE_MAIN_LAYOUT!", flush=True)
    min_y, max_y = min(years), max(years)
    n_scenarios = len(scenarios)

    navbar = html.Header(
        id="top-navbar",
        className="navbar top-navbar",
        children=[
            html.Nav(
                className="nav-links",
                children=[
                    dcc.Link(
                        "Dashboard",
                        href="/",
                        id="tab-dashboard",
                        className="nav-tab nav-link active",
                        title="Dashboard",
                    ),
                    dcc.Link(
                        "DRE",
                        href="/dre",
                        id="tab-dre",
                        className="nav-tab nav-link",
                        title="DRE",
                    ),
                    dcc.Link(
                        "DFC",
                        href="/dfc",
                        id="tab-dfc",
                        className="nav-tab nav-link",
                        title="DFC",
                    ),
                ],
            )
        ],
    )

    dashboard_div = html.Div(
        id="dashboard-page",
        className="dashboard",
        children=[
            # Área principal onde os gráficos e secções dinâmicas são injetados
            html.Main(
                className="main",
                children=[html.Div(id="dashboard-content", className="content")],
            ),
            # Barra lateral de filtros e metadados
            html.Aside(
                className="sidebar",
                children=[
                    # Logótipo e título
                    html.Div(
                        [
                            html.Div("Nour", className="brand"),
                            html.Div(
                                "CTI Global | Concessão 2027–2038",
                                className="brand-caption",
                            ),
                        ],
                        className="brand-lockup",
                    ),
                    # Painel 1: Perspetivas
                    panel(
                        "Perspetiva",
                        [
                            dcc.Tabs(
                                id="perspective",
                                value="gestao",
                                className="segmented",
                                parent_className="segmented-parent",
                                content_className="segmented-content",
                                children=[
                                    dcc.Tab(
                                        label=label,
                                        value=key,
                                        className="segment",
                                        selected_className="segment--on",
                                    )
                                    for key, label in perspectives.items()
                                ],
                            ),
                            html.P(
                                list(perspectives.values())[0],
                                id="perspective-summary",
                                className="panel-note",
                            ),
                        ],
                    ),
                    # Painel 2: Recorte temporal e de cenários
                    panel(
                        "Recorte",
                        [
                            row(
                                "Anos da concessão",
                                dcc.RangeSlider(
                                    id="years",
                                    min=min_y,
                                    max=max_y,
                                    step=1,
                                    value=[min_y, max_y],
                                    marks=None,
                                    tooltip={"placement": "bottom"},
                                ),
                                html.Output(
                                    f"{min_y}–{max_y}",
                                    id="years-readout",
                                    className="readout",
                                ),
                            ),
                            row(
                                "Cenários simulados",
                                dcc.RangeSlider(
                                    id="scenarios",
                                    min=1,
                                    max=n_scenarios,
                                    step=1,
                                    value=[1, n_scenarios],
                                    marks=None,
                                    tooltip={"placement": "bottom"},
                                ),
                                html.Output(
                                    f"{n_scenarios:,}".replace(",", "."),
                                    id="scenarios-readout",
                                    className="readout",
                                ),
                            ),
                        ],
                    ),
                    # Painel 3: Seletor de indicador para distribuição
                    panel(
                        "Indicador",
                        [
                            row(
                                "Distribuição",
                                dcc.Dropdown(
                                    id="distribution-metric",
                                    options=[
                                        {"label": label, "value": key}
                                        for key, label in metric_labels.items()
                                        if key in perspective_metrics["gestao"]
                                    ],
                                    value="margem_ebitda",
                                    clearable=False,
                                ),
                            )
                        ],
                    ),
                    # Metadados e proveniência dos dados
                    html.Div(
                        [
                            html.Dl(
                                [
                                    html.Dt("Base"),
                                    html.Dd("Dados formatados CTI"),
                                    html.Dt("Atualização"),
                                    html.Dd("Leitura direta do arquivo local"),
                                    html.Dt("Cobertura"),
                                    html.Dd(
                                        f"{n_scenarios} cenários · {max_y - min_y + 1} anos"
                                    ),
                                ],
                                className="meta-list",
                            )
                        ],
                        className="meta-list brand-lockup",
                    ),
                ],
            ),
        ],
    )

    dre_div = html.Div(
        id="dre-page",
        className="dre-page",
        style={"display": "none"},
        children=[
            html.Div(
                style={
                    "backgroundColor": "#f8fafc",
                    "minHeight": "100vh",
                    "padding": "30px",
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "24px",
                },
                children=[
                    html.Div(
                        style={
                            "backgroundColor": "#ffffff",
                            "padding": "24px",
                            "borderRadius": "8px",
                            "border": "1px solid #e2e8f0",
                            "boxShadow": "0 1px 3px rgba(0,0,0,0.05)",
                            "textAlign": "center",
                        },
                        children=[
                            html.H2(
                                "Demonstração do Resultado do Exercício (DRE)",
                                style={
                                    "color": "#0f172a",
                                    "margin": "0 0 4px 0",
                                    "fontWeight": "bold",
                                    "fontFamily": "sans-serif",
                                    "fontSize": "22px",
                                },
                            ),
                            html.P(
                                "Acompanhe a performance financeira e os resultados operacionais.",
                                style={
                                    "color": "#64748b",
                                    "margin": "0",
                                    "fontSize": "14px",
                                    "fontFamily": "sans-serif",
                                },
                            ),
                        ],
                    ),

                    html.Div(
                        style={
                            "display": "flex",
                            "flexDirection": "column",
                            "gap": "24px",
                            "width": "100%",
                        },
                        children=[
                            
                            # ==========================================
                            # BLOCO 1: TABELA DRE COM SEU FILTRO PRÓPRIO
                            # ==========================================
                            html.Div(
                                style={
                                    "backgroundColor": "#ffffff",
                                    "borderRadius": "8px",
                                    "border": "1px solid #e2e8f0",
                                    "padding": "20px",
                                    "boxShadow": "0 1px 3px rgba(0,0,0,0.05)",
                                },
                                children=[
                                    html.H3("Tabela DRE", style={"color": "#0f172a", "fontSize": "16px", "marginBottom": "16px"}),
                                    
                                    # Filtro interno da DRE (Inicia por padrão no Ano 1)
                                    html.Div(
                                        style={"marginBottom": "20px", "display": "flex", "gap": "16px"},
                                        children=[
                                            html.Div(
                                                style={"width": "220px"},
                                                children=[
                                                    html.Label("Ano", style={"fontSize": "12px", "fontWeight": "600", "color": "var(--dark-blue)", "marginBottom": "4px", "display": "block"}),
                                                    dcc.Dropdown(
                                                        id="dre-filtro-ano",
                                                        options=[{"label": f"Ano {a}", "value": a} for a in years],
                                                        value=1,  
                                                        clearable=False
                                                    )
                                                ]
                                            ),
                                            html.Div(
                                                style={"width": "220px"},
                                                children=[
                                                    html.Label("Cenário", style={"fontSize": "12px", "fontWeight": "600", "color": "var(--dark-blue)", "marginBottom": "4px", "display": "block"}),
                                                    dcc.Dropdown(
                                                        id="dre-filtro-cenario",
                                                        options=[{"label": str(c), "value": c} for c in scenarios],
                                                        placeholder="Selecione o cenário...",
                                                        multi=True
                                                    )
                                                ]
                                            )
                                        ]
                                    ),

                                    # TABELA DRE
                                    dash_table.DataTable(
                                        id="tabela-dre-dinamica",
                                        columns=[
                                            {"name": "", "id": "sinal"},
                                            {"name": "Descrição da Conta", "id": "conta"},
                                            {"name": "Valor Consolidado", "id": "valor"},
                                        ],
                                        data=[],
                                        style_table={"overflowX": "auto", "minWidth": "100%"},
                                        style_cell={
                                            "backgroundColor": "#ffffff",
                                            "color": "var(--ink)",
                                            "border": "none",
                                            "borderBottom": "1px solid #f1f5f9",
                                            "padding": "14px 16px",
                                            "fontFamily": "sans-serif",
                                        },
                                        style_cell_conditional=[
                                            {"if": {"column_id": "sinal"}, "width": "50px", "textAlign": "center", "fontWeight": "bold", "fontSize": "16px", "color": "#94a3b8"},
                                            {"if": {"column_id": "conta"}, "textAlign": "left"},
                                            {"if": {"column_id": "valor"}, "textAlign": "right", "width": "250px", "fontFamily": "monospace"},
                                        ],
                                        style_header={
                                            "backgroundColor": "var(--fill-hover)",
                                            "color": "var(--ink)",
                                            "fontWeight": "bold",
                                            "border": "none",
                                            "textAlign": "left",
                                        },
                                        style_data_conditional=[
                                            {
                                                "if": {"filter_query": '{sinal} = "="'},
                                                "backgroundColor": "var(--light-blue)",
                                                "color": "#00395F",
                                            },
                                            {
                                                "if": {
                                                    "filter_query": '{valor} contains "-"',
                                                    "column_id": "valor",
                                                },
                                                "color": "#dc2626",
                                                "fontWeight": "normal",
                                            },
                                        ],
                                    )
                                ],
                            ),
                            # ==========================================
                            # GRÁFICO DE MELHORES ANOS E CENÁRIOS
                            # ==========================================
                            html.Div(
                                style={
                                    "backgroundColor": "#ffffff",
                                    "borderRadius": "8px",
                                    "border": "1px solid #e2e8f0",
                                    "padding": "20px",
                                    "boxShadow": "0 1px 3px rgba(0,0,0,0.05)",
                                },
                                children=[
                                    html.H3("Melhores Anos e Cenários", style={"color": "#0f172a", "fontSize": "16px", "marginBottom": "16px"}),

                                    # Filtro de Métrica exclusivo para este gráfico
                                    html.Div(
                                        style={"marginBottom": "16px", "width": "240px"},
                                        children=[
                                            html.Label(
                                                "Métrica de Análise",
                                                style={
                                                    "fontSize": "12px",
                                                    "fontWeight": "600",
                                                    "color": "var(--dark-blue)",
                                                    "marginBottom": "4px",
                                                    "display": "block",
                                                },
                                            ),
                                            dcc.Dropdown(
                                                id="grafico-melhores-anos-metrica",
                                                options=[
                                                    {"label": "Resultado Líquido", "value": "DRE Resultado Liquido"},
                                                    {"label": "EBITDA", "value": "DRE EBITDA"}
                                                ],
                                                value="DRE Resultado Liquido",  # Padrão inicial
                                                clearable=False
                                            ),
                                        ],
                                    ),

                                    # GRÁFICO DE BARRAS (Melhores Anos + Cenários)
                                    dcc.Graph(id="grafico-melhores-anos-cenarios"),
                                ],
                            ),

                            # ==========================================
                            # GRÁFICO TOP 10 COM SEU FILTRO PRÓPRIO
                            # ==========================================
                            html.Div(
                                style={
                                    "backgroundColor": "#ffffff",
                                    "borderRadius": "8px",
                                    "border": "1px solid #e2e8f0",
                                    "padding": "20px",
                                    "boxShadow": "0 1px 3px rgba(0,0,0,0.05)",
                                },
                                children=[
                                    html.H3("Melhores Cenários", style={"color": "var(--dark-blue)", "fontSize": "16px", "marginBottom": "16px"}),

                                    html.Div(
                                        style={"display": "flex", "gap": "16px", "marginBottom": "16px"},
                                        children=[

                                            html.Div(
                                                style={"width": "220px"},
                                                children=[
                                                    html.Label(
                                                        "Ano",
                                                        style={
                                                            "fontSize": "12px",
                                                            "fontWeight": "600",
                                                            "color": "var(--dark-blue)",
                                                            "marginBottom": "4px",
                                                            "display": "block",
                                                        },
                                                    ),
                                                    dcc.Dropdown(
                                                        id="grafico-filtro-ano",
                                                        options=[{"label": f"Ano {a}", "value": a} for a in years],
                                                        value=1,  
                                                        clearable=False
                                                    ),
                                                ],
                                            ),

                                            # 2. NOVO FILTRO: Métrica de Avaliação (Resultado Líquido vs EBITDA)
                                            html.Div(
                                                style={"width": "240px"},
                                                children=[
                                                    html.Label(
                                                        "Métrica de Avaliação",
                                                        style={
                                                            "fontSize": "12px",
                                                            "fontWeight": "600",
                                                            "color": "var(--dark-blue)",
                                                            "marginBottom": "4px",
                                                            "display": "block",
                                                        },
                                                    ),
                                                    dcc.Dropdown(
                                                        id="grafico-filtro-metrica",
                                                        options=[
                                                            {"label": "Resultado Líquido", "value": "DRE Resultado Liquido"},
                                                            {"label": "EBITDA", "value": "DRE EBITDA"}
                                                        ],
                                                        value="DRE Resultado Liquido",  
                                                        clearable=False
                                                    ),
                                                ],
                                            ),
                                        ]
                                    ),

                                    # GRÁFICO DE BARRAS
                                    dcc.Graph(id="grafico-top10-cenarios"),
                                ],
                            ),
                        ],
                    ),
                ],
            )
        ],
    )

    dfc_div = html.Div(
        id="dfc-page",
        className="dfc-page",
        style={"display": "none"},
        children=[
            html.Div(
                [
                    html.H1("Demonstrativo do Fluxo de Caixa (DFC)"),
                    html.Div(
                        [
                            html.Label("Cenário", htmlFor="dfc-scenario"),
                            dcc.Dropdown(
                                id="dfc-scenario",
                                options=[
                                    {"label": f"Cenário {index}", "value": scenario}
                                    for index, scenario in enumerate(scenarios, start=1)
                                ],
                                value=scenarios[0],
                                clearable=False,
                                searchable=True,
                            ),
                        ],
                        className="dfc-scenario",
                    ),
                    html.Div(
                        build_dfc_table(data, years, scenarios[0]),
                        id="dfc-table-content",
                        className="dfc-table-wrap",
                    ),
                ],
                className="dfc-content",
            ),
        ],
    )

    return html.Div(
        className="app-container",
        children=[
            dcc.Location(id="url", refresh=False),
            navbar,
            dashboard_div,
            dre_div,
            dfc_div,
        ],
    )