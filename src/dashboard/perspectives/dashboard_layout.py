# src/dashboard/dashboard_layout.py
from dash import html, dcc
from ui_elements import row, panel

def create_main_layout(years, scenarios, perspectives, perspective_metrics, metric_labels):
    """Constrói a árvore DOM completa do layout principal do painel (Sidebar e Main)."""
    min_y, max_y = min(years), max(years)
    n_scenarios = len(scenarios)
    
    return html.Div(
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
                            html.Div("NOUR", className="brand"),
                            html.Div("CTI Global | Concessão 2027–2038", className="brand-caption"),
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
                                html.Output(f"{min_y}–{max_y}", id="years-readout", className="readout"),
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
                                html.Output(f"{n_scenarios:,}".replace(",", "."), id="scenarios-readout", className="readout"),
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
                                    html.Dd(f"{n_scenarios} cenários · {max_y - min_y + 1} anos"),
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