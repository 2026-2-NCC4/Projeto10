# src/dashboard/dashboard_layout.py
from dash import html, dcc
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
        className="empty-page-container",
        style={"display": "none"},
        children=[
            html.H1("DRE", className="centered-page-text"),
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
