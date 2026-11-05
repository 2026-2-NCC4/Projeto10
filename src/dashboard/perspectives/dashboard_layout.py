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


# ==============================================================================
# FINANCIAL STATEMENTS (DRE / DFC) UNIFIED DESIGN SYSTEM
# ==============================================================================
STATEMENT_CONTAINER_STYLE = {
    "backgroundColor": "#f8fafc",
    "minHeight": "100vh",
    "padding": "30px",
    "display": "flex",
    "flexDirection": "column",
    "gap": "24px",
}

STATEMENT_HEADER_CARD_STYLE = {
    "backgroundColor": "#ffffff",
    "padding": "24px",
    "borderRadius": "8px",
    "border": "1px solid #e2e8f0",
    "boxShadow": "0 1px 3px rgba(0,0,0,0.05)",
    "textAlign": "center",
}

STATEMENT_TITLE_STYLE = {
    "color": "#111111",
    "margin": "0 0 10px 0",
    "fontWeight": "bold",
    "fontFamily": "sans-serif",
    "fontSize": "22px",
}

STATEMENT_SUBTITLE_STYLE = {
    "color": "#4e4e4e",
    "margin": "0 auto",
    "fontSize": "14px",
    "fontFamily": "sans-serif",
    "textWrap": "balance",
    "maxWidth": "720px",
}

STATEMENT_CONTENT_STYLE = {
    "display": "flex",
    "flexDirection": "column",
    "gap": "24px",
    "width": "100%",
}

STATEMENT_CARD_STYLE = {
    "backgroundColor": "#ffffff",
    "borderRadius": "8px",
    "border": "1px solid #e2e8f0",
    "padding": "20px",
    "boxShadow": "0 1px 3px rgba(0,0,0,0.05)",
}

SECTION_TITLE_STYLE = {
    "color": "#0f172a",
    "fontSize": "16px",
    "marginBottom": "16px",
    "fontWeight": "bold",
}

FILTER_LABEL_STYLE = {
    "fontSize": "12px",
    "fontWeight": "600",
    "color": "var(--dark-blue)",
    "marginBottom": "4px",
    "display": "block",
}

STATEMENT_TABLE_CONFIG = {
    "columns": [
        {"name": "", "id": "sinal"},
        {"name": "Descrição da Conta", "id": "conta"},
        {"name": "Valor Consolidado", "id": "valor"},
    ],
    "style_table": {"overflowX": "auto", "minWidth": "100%"},
    "style_cell": {
        "backgroundColor": "#ffffff",
        "color": "var(--ink)",
        "border": "none",
        "borderBottom": "1px solid #f1f5f9",
        "padding": "14px 16px",
        "fontFamily": "sans-serif",
    },
    "style_cell_conditional": [
        {
            "if": {"column_id": "sinal"},
            "width": "50px",
            "textAlign": "center",
            "fontWeight": "bold",
            "fontSize": "16px",
            "color": "#94a3b8",
        },
        {"if": {"column_id": "conta"}, "textAlign": "left"},
        {
            "if": {"column_id": "valor"},
            "textAlign": "right",
            "width": "250px",
        },
    ],
    "style_header": {
        "backgroundColor": "var(--fill-hover)",
        "color": "var(--ink)",
        "fontWeight": "bold",
        "border": "none",
        "textAlign": "left",
    },
    "style_data_conditional": [
        {
            "if": {
                "filter_query": '{valor} contains "-"',
                "column_id": "valor",
            },
            "color": "var(--plum)",
            "fontWeight": "normal",
        },
        {
            "if": {"filter_query": '{sinal} = "="'},
            "backgroundColor": "var(--fill)",
            "color": "var(--ink)",
        },
    ],
}


def build_statement_filter_field(
    label: str, control, width: str = "220px", margin_bottom: str = None
):
    """Cria um campo de filtro padronizado com rótulo e componente."""
    style = {"width": width}
    if margin_bottom:
        style["marginBottom"] = margin_bottom
    return html.Div(
        style=style,
        children=[
            html.Label(label, style=FILTER_LABEL_STYLE),
            control,
        ],
    )


def build_statement_card(title: str, children: list, title_color: str = None):
    """Cria um card padronizado para seções com título e conteúdo."""
    title_style = dict(SECTION_TITLE_STYLE)
    if title_color:
        title_style["color"] = title_color
    return html.Div(
        style=STATEMENT_CARD_STYLE,
        children=[
            html.H3(title, style=title_style),
            *children,
        ],
    )


def build_statement_table(table_id: str):
    """Cria a DataTable padronizada de demonstrativo financeiro."""
    return dash_table.DataTable(
        id=table_id,
        data=[],
        **STATEMENT_TABLE_CONFIG,
    )


def build_statement_page(
    page_id: str,
    title: str,
    subtitle: str,
    table_title: str,
    table_id: str,
    filtro_ano_id: str,
    filtro_cenario_id: str,
    melhores_anos_metrica_id: str,
    melhores_anos_graph_id: str,
    melhores_anos_options: list,
    top10_ano_id: str,
    top10_metrica_id: str,
    top10_graph_id: str,
    top10_options: list,
    years: list,
    scenarios: list,
):
    """Constrói a árvore DOM de uma página de demonstrativo financeiro vertical (e.g. DRE).

    Layout: header card → tabela vertical (sinal/conta/valor) com filtros de ano/cenário
    → gráfico de melhores anos+cenários → gráfico top-10 cenários por ano.
    """
    header_card = html.Div(
        style=STATEMENT_HEADER_CARD_STYLE,
        children=[
            html.H2(title, style=STATEMENT_TITLE_STYLE),
            html.P(subtitle, style=STATEMENT_SUBTITLE_STYLE),
        ],
    )

    table_filters = html.Div(
        style={"marginBottom": "20px", "display": "flex", "gap": "16px"},
        children=[
            build_statement_filter_field(
                "Ano",
                dcc.Dropdown(
                    id=filtro_ano_id,
                    options=[{"label": f"Ano {a}", "value": a} for a in years],
                    value=1,
                    clearable=False,
                    placeholder="Selecione o ano...",
                ),
                width="220px",
            ),
            build_statement_filter_field(
                "Cenário",
                dcc.Dropdown(
                    id=filtro_cenario_id,
                    options=[{"label": str(c), "value": c} for c in scenarios],
                    placeholder="Selecione o cenário...",
                    multi=True,
                ),
                width="220px",
            ),
        ],
    )

    table_card = build_statement_card(
        table_title,
        [table_filters, build_statement_table(table_id)],
    )

    chart2_filters = html.Div(
        style={"display": "flex", "gap": "16px", "marginBottom": "16px"},
        children=[
            build_statement_filter_field(
                "Ano",
                dcc.Dropdown(
                    id=top10_ano_id,
                    options=[{"label": f"Ano {a}", "value": a} for a in years],
                    value=1,
                    clearable=False,
                ),
                width="220px",
            ),
            build_statement_filter_field(
                "Métrica de Avaliação",
                dcc.Dropdown(
                    id=top10_metrica_id,
                    options=top10_options,
                    value=top10_options[0]["value"] if top10_options else None,
                    clearable=False,
                ),
                width="240px",
            ),
        ],
    )

    chart2_card = build_statement_card(
        "Melhores Cenários",
        [chart2_filters, dcc.Graph(id=top10_graph_id)],
        title_color="var(--dark-blue)",
    )

    return html.Div(
        id=page_id,
        className=page_id,
        style={"display": "none"},
        children=[
            html.Div(
                style=STATEMENT_CONTAINER_STYLE,
                children=[
                    header_card,
                    html.Div(
                        style=STATEMENT_CONTENT_STYLE,
                        children=[
                            table_card,
                            chart2_card,
                        ],
                    ),
                ],
            )
        ],
    )


def build_dfc_page(
    page_id: str, title: str, subtitle: str, years: list, scenarios: list, data
):
    """Constrói a árvore DOM da página DFC.

    A DFC é um conceito diferente da DRE: exibe uma tabela pivot horizontal com
    todos os anos nas colunas e um cenário selecionado de cada vez. Não contém
    gráficos abaixo — apenas os filtros de cenário e anos e a tabela pivot.

    Reutiliza os tokens visuais do design system (header card, card de conteúdo,
    estilos de filtro) para consistência visual com a DRE.
    """
    header_card = html.Div(
        style=STATEMENT_HEADER_CARD_STYLE,
        children=[
            html.H2(title, style=STATEMENT_TITLE_STYLE),
            html.P(subtitle, style=STATEMENT_SUBTITLE_STYLE),
        ],
    )

    filters_row = html.Div(
        style={
            "marginBottom": "20px",
            "display": "flex",
            "gap": "16px",
            "flexWrap": "wrap",
        },
        children=[
            build_statement_filter_field(
                "Ano(s)",
                dcc.Dropdown(
                    id="dfc-years",
                    options=[{"label": f"Ano {year}", "value": year} for year in years],
                    value=list(years),
                    multi=True,
                    clearable=False,
                    searchable=True,
                ),
                width="218px",
            ),
            build_statement_filter_field(
                "Cenário",
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
                width="218px",
            ),
        ],
    )

    table_card = build_statement_card(
        "Tabela DFC",
        [
            filters_row,
            html.Div(
                build_dfc_table(data, years, scenarios[0]),
                id="dfc-table-content",
                className="dfc-table-wrap",
            ),
        ],
    )

    return html.Div(
        id=page_id,
        className=page_id,
        style={"display": "none"},
        children=[
            html.Div(
                style=STATEMENT_CONTAINER_STYLE,
                children=[
                    header_card,
                    html.Div(
                        style=STATEMENT_CONTENT_STYLE,
                        children=[table_card],
                    ),
                ],
            )
        ],
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
                        [html.Div("Nour", className="brand")],
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

    dre_div = build_statement_page(
        page_id="dre-page",
        title="Demonstração do Resultado do Exercício (DRE)",
        subtitle="Estrutura contábil da formação do resultado econômico. Detalha receitas, deduções, custos operacionais, despesas e tributos para mensurar a lucratividade líquida e o EBITDA da concessão.",
        table_title="Tabela DRE",
        table_id="tabela-dre-dinamica",
        filtro_ano_id="dre-filtro-ano",
        filtro_cenario_id="dre-filtro-cenario",
        melhores_anos_metrica_id="grafico-melhores-anos-metrica",
        melhores_anos_graph_id="grafico-melhores-anos-cenarios",
        melhores_anos_options=[
            {"label": "Resultado Líquido", "value": "DRE Resultado Liquido"},
            {"label": "EBITDA", "value": "DRE EBITDA"},
        ],
        top10_ano_id="grafico-filtro-ano",
        top10_metrica_id="grafico-filtro-metrica",
        top10_graph_id="grafico-top10-cenarios",
        top10_options=[
            {"label": "Resultado Líquido", "value": "DRE Resultado Liquido"},
            {"label": "EBITDA", "value": "DRE EBITDA"},
        ],
        years=years,
        scenarios=scenarios,
    )

    dfc_div = build_dfc_page(
        page_id="dfc-page",
        title="Demonstração dos Fluxos de Caixa (DFC)",
        subtitle="Mapeamento direto das entradas e saídas financeiras da concessão. Demonstra a geração de caixa operacional, dispêndios de Capex, serviço da dívida e saldo disponível para acionistas.",
        years=years,
        scenarios=scenarios,
        data=data,
    )

    return html.Div(
        className="app-container",
        children=[
            dcc.Location(id="url", refresh=False),
            dcc.Store(id="simplified-view-active-store"),
            navbar,
            dashboard_div,
            dre_div,
            dfc_div,
        ],
    )
