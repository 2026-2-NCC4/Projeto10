import re
from dash import html, dcc, dash_table
import pandas as pd
from ui_elements import row, panel
from dash_iconify import DashIconify

DRE_ROWS = (
    ("(+) Receita Bruta",                               "DRE Receita"),
    ("(-) Tributos",                                    "DRE Tributos"),
    ("(-) Custos",                                      "DRE Custos"),
    ("(-) Depreciação e Amortização",                   "DRE Depreciacao e Amortizacao"),
    ("(=) Resultado Operacional",                       "DRE Resultado Operacional"),
    ("(+) Receitas Financeiras",                        "DRE Receitas Financeiras"),
    ("(-) Despesas Financeiras",                        "DRE Despesas Financeiras"),
    ("(=) Resultado Financeiro",                        "DRE Resultado Financeiro"),
    ("( ) Outros Resultados Operacionais",              "DRE Outros Resultados Operacionais"),
    ("(=) Resultado Antes do Imposto de Renda",         "DRE Resultado Antes do Imposto de Renda"),
    ("(-) Imposto de Renda e Contribuição Social",      "DRE Imposto de Renda e Contribuicao Social"),
    ("(=) Resultado Líquido",                           "DRE Resultado Liquido"),
    ("(=) Resultado Líquido após Equivalência",         "DRE Resultado Liquido apos Equivalencia"),
    ("( ) EBITDA",                                      "DRE EBITDA"),
)

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

BALANCO_ROWS = (
    ("ATIVO", "BAL Total do Ativo", "total"),
    ("1. ATIVO CIRCULANTE", None, "section"),
    ("Caixa e Equivalentes de Caixa", "BAL Disponivel", "item"),
    (
        "Contas a Receber (Partes Relacionadas)",
        "BAL Contas a Receber Partes Relacionadas",
        "item",
    ),
    ("Contas a Receber (Clientes)", "BAL Contas a Receber Clientes", "item"),
    ("Contas a Receber SWAP", "BAL Contas a Receber SWAP", "item"),
    ("Estoques", "BAL Estoques Diversos", "item"),
    ("Outros Créditos / Ativos Circulantes", "BAL Outros Creditos", "item"),
    ("TOTAL ATIVO CIRCULANTE", "BAL Ativo Circulante", "total"),
    ("2. ATIVO NÃO CIRCULANTE", None, "section"),
    ("Outorga da Concessão", "BAL Outorga da Concessao", "item"),
    ("Realizável a Longo Prazo", "BAL Realizavel a Longo Prazo", "item"),
    ("At Fiscal Diferido", "BAL At Fiscal Diferido", "item"),
    ("Créditos Tributários", "BAL Creditos Tributarios", "item"),
    ("Outros Créditos LP", "BAL Outros Creditos LP", "item"),
    ("Permanente", "BAL Permanente", "item"),
    ("Investimentos - Imobilizados", "BAL Investimentos Imobilizado", "item"),
    ("Investimentos - Intangível", "BAL Investimentos Intangivel", "item"),
    ("Diferido", "BAL Diferido", "item"),
    ("Depreciação Acumulada (Conta redutora)", "BAL Depreciacao Acumulada", "item"),
    (
        "Amortização - Intangível (Conta redutora)",
        "BAL Amortizacao Intangivel",
        "item",
    ),
    (
        "Amortização - Acumulada (Conta redutora)",
        "BAL Amortizacao Acumulada",
        "item",
    ),
    ("TOTAL ATIVO NÃO CIRCULANTE", "__TOTAL_ATIVO_NAO_CIRCULANTE__", "total"),
    ("PASSIVO E PATRIMÔNIO LÍQUIDO", "BAL Total do Passivo", "total"),
    ("1. PASSIVO CIRCULANTE", None, "section"),
    ("Fornecedores", "BAL Fornecedores", "item"),
    ("Empréstimos", "BAL Emprestimos", "item"),
    (
        "Obrigações Trabalhistas e Sociais",
        "BAL Encargos Sociais e Trabalhistas",
        "item",
    ),
    ("Tributos a pagar", "BAL Tributos a pagar", "item"),
    ("Contas a pagar", "BAL Tributos a pagar", "item"),
    ("Impostos a Recolher", "BAL Impostos", "item"),
    (
        "Obrigações com o Poder Concedente",
        "BAL Obrigacoes com o Poder Concedente",
        "item",
    ),
    ("Outros Débitos", "BAL Outros Debitos", "item"),
    ("Provisão Manutenção", "BAL Provisao Manutencao", "item"),
    ("Encargos Sociais e Trabalhistas", "BAL Tributos a pagar", "item"),
    ("TOTAL PASSIVO CIRCULANTE", "BAL Passivo Circulante", "total"),
    ("2. PASSIVO NÃO CIRCULANTE", None, "section"),
    ("Outros Débitos de longo prazo", "BAL Outros deb", "item"),
    (
        "Empréstimos e financiamentos bancários de longo prazo",
        "BAL Emprest",
        "item",
    ),
    ("Provisões para Contingências", "BAL Prov para Contingencias", "item"),
    ("TOTAL PASSIVO NÃO CIRCULANTE", "__TOTAL_PASSIVO_NAO_CIRCULANTE__", "total"),
    ("3. PATRIMÔNIO LÍQUIDO", None, "section"),
    ("Capital Social", "BAL Capital Social", "item"),
    ("Dividendos Antecipados", "BAL Dividendos Antecipados", "item"),
    ("Reservas de Capital", "BAL Reservas de Capital", "item"),
    ("Reservas Legais", "BAL Reservas Legais", "item"),
    ("Reserva de Retenção de Lucros", "BAL Reserva de Retencao de Lucros", "item"),
    ("Resultado Acumulado", "BAL Resultado Acumulado", "item"),
    ("Resultado do Período", "BAL Resultado do Periodo", "item"),
    ("TOTAL PATRIMÔNIO LÍQUIDO", "BAL Patrimonio Liquido", "total"),
)

def build_export_button(button_id):
    return html.Button(
        [
            DashIconify(
                icon="akar-icons:download",
                width=20,
                color="white"
            ),
            html.Span("Exportar Excel"),
        ],
        id=button_id,
        n_clicks=0,
        className="export-excel-btn",
    )

def _brl(value):
    if pd.isna(value):
        return "—"

    value = float(value)

    formatted = (
        f"{abs(value):,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

    if value < 0:
        return f"R$ ({formatted})"

    return f"R$ {formatted}"


def _balanco_cell_value(balance_sheet, year, account):
    if year not in balance_sheet.index:
        return 0.0
    if account == "__TOTAL_ATIVO_NAO_CIRCULANTE__":
        total_ativo = (
            balance_sheet.at[year, "BAL Total do Ativo"]
            if "BAL Total do Ativo" in balance_sheet.columns
            else 0.0
        )
        ativo_circ = (
            balance_sheet.at[year, "BAL Ativo Circulante"]
            if "BAL Ativo Circulante" in balance_sheet.columns
            else 0.0
        )
        return (0.0 if pd.isna(total_ativo) else total_ativo) - (
            0.0 if pd.isna(ativo_circ) else ativo_circ
        )
    if account == "__TOTAL_PASSIVO_NAO_CIRCULANTE__":
        parts = (
            balance_sheet.at[year, "BAL Outros deb"]
            if "BAL Outros deb" in balance_sheet.columns
            else 0.0,
            balance_sheet.at[year, "BAL Emprest"]
            if "BAL Emprest" in balance_sheet.columns
            else 0.0,
            balance_sheet.at[year, "BAL Prov para Contingencias"]
            if "BAL Prov para Contingencias" in balance_sheet.columns
            else 0.0,
        )
        return sum(0.0 if pd.isna(v) else v for v in parts)
    return (
        balance_sheet.at[year, account]
        if account in balance_sheet.columns
        else 0.0
    )


def build_dfc_table(data, years, scenario):
    if isinstance(scenario, (list, tuple, set)):
        target_scenario = next(iter(scenario)) if len(scenario) > 0 else (data["Cenário"].dropna().iloc[0] if "Cenário" in data.columns else "Cenário 1")
    else:
        target_scenario = scenario
    cash_flow = data.loc[data["Cenário"].eq(target_scenario)].set_index("Ano")
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
                            html.Td(
                                _brl(
                                    cash_flow.at[year, account]
                                    if (
                                        year in cash_flow.index
                                        and account in cash_flow.columns
                                    )
                                    else 0.0
                                )
                            )
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


def build_balanco_table(data, years, scenario):
    if isinstance(scenario, (list, tuple, set)):
        target_scenario = next(iter(scenario)) if len(scenario) > 0 else (data["Cenário"].dropna().iloc[0] if "Cenário" in data.columns else "Cenário 1")
    else:
        target_scenario = scenario
    balance_sheet = data.loc[data["Cenário"].eq(target_scenario)].set_index("Ano")
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
                        + (
                            [html.Td("") for _ in columns]
                            if kind == "section"
                            else [
                                html.Td(
                                    _brl(
                                        _balanco_cell_value(
                                            balance_sheet, year, account
                                        )
                                    )
                                )
                                for year in columns
                            ]
                        ),
                        className=(
                            "dfc-total"
                            if kind in {"total", "section"}
                            else ""
                        ),
                    )
                    for label, account, kind in BALANCO_ROWS
                ]
            ),
        ],
        className="dfc-table",
    )


# ==============================================================================
# FINANCIAL STATEMENTS (DRE / DFC / BALANÇO) UNIFIED DESIGN SYSTEM
# ==============================================================================
STATEMENT_CONTAINER_STYLE = {
    "backgroundColor": "transparent",
    "display": "flex",
    "flexDirection": "column",
    "gap": "24px",
}

STATEMENT_HEADER_CARD_STYLE = {
    "backgroundColor": "var(--white)",
    "padding": "20px",
    "borderRadius": "var(--radius-lg)",
    "border": "1px solid #e2e8f0",
    "textAlign": "center",
    "boxShadow": "var(--shadow-sm)",
    "position": "relative",
    "overflow": "hidden",
}

STATEMENT_TITLE_STYLE = {
    "color": "var(--ink)",
    "margin": "0 0 8px 0",
    "fontWeight": "600",
    "fontFamily": "inherit",
    "fontSize": "1.75rem",
    "letterSpacing": "-0.025em",
    "lineHeight": "1.15",
}

STATEMENT_SUBTITLE_STYLE = {
    "opacity": "1",
    "margin": "0 auto",
    "fontSize": "0.95rem",
    "fontFamily": "inherit",
    "textWrap": "balance",
    "maxWidth": "760px",
    "lineHeight": "1.45",
}

STATEMENT_CONTENT_STYLE = {
    "display": "flex",
    "flexDirection": "column",
    "gap": "24px",
    "width": "100%",
}

STATEMENT_CARD_STYLE = {
    "backgroundColor": "rgba(255, 255, 255, 0.9)",
    "backdropFilter": "blur(20px) saturate(180%)",
    "WebkitBackdropFilter": "blur(20px) saturate(180%)",
    "borderRadius": "var(--radius-lg)",
    "border": "1px solid var(--line)",
    "padding": "24px",
    "boxShadow": "var(--shadow-sm)",
}

SECTION_TITLE_STYLE = {
    "color": "var(--ink)",
    "fontSize": "1.25rem",
    "marginBottom": "18px",
    "fontWeight": "600",
    "letterSpacing": "-0.02em",
    "fontFamily": "inherit",
}

FILTER_LABEL_STYLE = {
    "fontSize": "0.95rem",
    "color": "var(--ink)",
    "marginBottom": "6px",
    "display": "block",
}

STATEMENT_TABLE_CONFIG = {
    "columns": [
        {"name": "Descrição da Conta", "id": "conta"},
        {"name": "Valor Consolidado", "id": "valor"},
    ],
    "style_table": {"overflowX": "auto", "minWidth": "100%"},
    "style_cell": {
        "backgroundColor": "#ffffff",
        "color": "var(--ink)",
        "border": "none",
        "borderBottom": "1px solid #f1f5f9",
        "padding": "14px",
        "fontFamily": "sans-serif",
    },
    "style_cell_conditional": [
        {"if": {"column_id": "conta"}, "textAlign": "left"},
        {"if": {"column_id": "valor"}, "textAlign": "right", "width": "250px"},
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
            "if": {"filter_query": '{valor} contains "-"', "column_id": "valor"},
            "color": "var(--plum)",
            "fontWeight": "normal",
        },
        {
            "if": {"filter_query": '{conta} begins with "(=)"'},
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


def build_statement_card(
    title: str,
    children: list,
    title_color: str = None,
    export_button_id: str = None,
):
    """Cria um card com título e botão opcional de exportação."""

    title_style = dict(SECTION_TITLE_STYLE)

    if title_color:
        title_style["color"] = title_color

    # Título do card
    header = html.Div(
        [
            html.H3(title, style={**title_style, "marginBottom": "0"}),

            # Só cria o botão quando receber um ID
            *(
                [build_export_button(export_button_id)]
                if export_button_id
                else []
            ),
        ],
        style={
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
            "gap": "16px",
            "marginBottom": "18px",
        },
    )

    return html.Div(
        style=STATEMENT_CARD_STYLE,
        children=[
            header,
            *children,
        ],
    )

def build_dre_table(dre_data):
    """Constrói a tabela DRE em 2 colunas (rótulo + valor), no mesmo estilo da DFC."""
    return html.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th("Descrição da Conta", scope="col"),
                        html.Th("Valor Consolidado", scope="col"),
                    ]
                )
            ),
            html.Tbody(
                [
                    html.Tr(
                        [
                            html.Th(dre_row.get("conta", ""), scope="row"),
                            html.Td(
                                dre_row.get("valor", ""),
                                style={"textAlign": "right"},
                            ),
                        ],
                        className=(
                            "dfc-total"
                            if dre_row.get("conta", "").startswith("(=)")
                            or dre_row.get("conta") == "( ) EBITDA"
                            else ""
                        ),
                    )
                    for dre_row in dre_data
                ]
            ),
        ],
        className="dfc-table",
    )

def build_statement_table(table_id: str):
    """Cria o container para a tabela DRE estilizada como a DFC."""
    return html.Div(id=table_id, className="dfc-table-wrap")


def build_statement_page(
    page_id: str,
    title: str,
    subtitle: str,
    table_title: str,
    table_id: str,
    melhores_anos_metrica_id: str = None,
    melhores_anos_graph_id: str = None,
    melhores_anos_options: list = None,
    top10_ano_id: str = None,
    top10_metrica_id: str = None,
    top10_graph_id: str = None,
    top10_options: list = None,
    years: list = None,
    scenarios: list = None,
    filtro_ano_id: str = None,
    filtro_cenario_id: str = None,
):
    """Constrói a árvore DOM de uma página de demonstrativo financeiro vertical (e.g. DRE).

    Layout: header card → tabela vertical (conta/valor)
    → gráfico top-10 cenários por ano (usando o seletor de ano da barra lateral).
    """
    header_card = html.Div(
        style=STATEMENT_HEADER_CARD_STYLE,
        children=[
            html.H2(title, style=STATEMENT_TITLE_STYLE),
            html.P(subtitle, style=STATEMENT_SUBTITLE_STYLE),
        ],
    )

    table_card = build_statement_card(
        table_title,
        [build_statement_table(table_id)],
        export_button_id="export-dre-btn",
    )

    filter_fields = []
    if top10_ano_id:
        filter_fields.append(
            build_statement_filter_field(
                "Ano",
                dcc.Dropdown(
                    id=top10_ano_id,
                    options=[{"label": f"Ano {a}", "value": a} for a in (years or [])],
                    value=1,
                    clearable=False,
                ),
                width="220px",
            )
        )
    if top10_metrica_id:
        filter_fields.append(
            build_statement_filter_field(
                "Métrica de Avaliação",
                dcc.Dropdown(
                    id=top10_metrica_id,
                    options=top10_options or [],
                    value=top10_options[0]["value"] if top10_options else None,
                    clearable=False,
                ),
                width="240px",
            )
        )

    chart2_filters = html.Div(
        style={"display": "flex", "gap": "16px", "marginBottom": "16px"},
        children=filter_fields,
    )

    chart2_card = build_statement_card(
        "Melhores Cenários",
        [chart2_filters, dcc.Graph(id=top10_graph_id)],
        title_color="var(--ink)",
    )

    return html.Div(
        id=page_id,
        className=page_id,
        style={"display": "none"},
        children=[
            dcc.Download(id="download-dre"),
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

    Exibe a tabela DFC parametrizada pelos seletores da barra lateral.
    """
    header_card = html.Div(
        style=STATEMENT_HEADER_CARD_STYLE,
        children=[
            html.H2(title, style=STATEMENT_TITLE_STYLE),
            html.P(subtitle, style=STATEMENT_SUBTITLE_STYLE),
        ],
    )

    table_card = build_statement_card(
        "Tabela DFC",
        [
            html.Div(
                build_dfc_table(data, years, scenarios),
                id="dfc-table-content",
                className="dfc-table-wrap",
            ),
        ],
        export_button_id="export-dfc-btn",
    )

    return html.Div(
        id=page_id,
        className=page_id,
        style={"display": "none"},
        children=[
            dcc.Download(id="download-dfc"),
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


def build_balanco_page(
    page_id: str, title: str, subtitle: str, years: list, scenarios: list, data
):
    """Constrói a árvore DOM da página Balanço Patrimonial.

    Exibe a tabela do Balanço parametrizada pelos seletores da barra lateral.
    """
    header_card = html.Div(
        style=STATEMENT_HEADER_CARD_STYLE,
        children=[
            html.H2(title, style=STATEMENT_TITLE_STYLE),
            html.P(subtitle, style=STATEMENT_SUBTITLE_STYLE),
        ],
    )

    table_card = build_statement_card(
        "Tabela Balanço Patrimonial",
        [
            html.Div(
                build_balanco_table(data, years, scenarios),
                id="balanco-table-content",
                className="dfc-table-wrap",
            ),
        ],
        export_button_id="export-balanco-btn",
)

    return html.Div(
        id=page_id,
        className=page_id,
        style={"display": "none"},
        children=[
            dcc.Download(id="download-balanco"),
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
                    dcc.Link(
                        "Balanço",
                        href="/balanco",
                        id="tab-balanco",
                        className="nav-tab nav-link",
                        title="Balanço Patrimonial",
                    ),
                ],
            ),
            html.Button(
                [
                    html.Span(className="toggle-sidebar-bar"),
                    html.Span(className="toggle-sidebar-bar"),
                    html.Span(className="toggle-sidebar-bar"),
                ],
                id="toggle-sidebar-btn",
                className="toggle-sidebar-btn",
                title="Abrir / Fechar barra lateral",
                n_clicks=0,
            ),
        ],
    )

    dashboard_div = html.Div(
        id="dashboard-page",
        className="dashboard",
        children=[
            # Área principal onde os gráficos e secções dinâmicas são injetados
            html.Main(
                className="main",
                children=[
                    html.Div(
                        id="dashboard-content",
                        className="content",
                        style={
                            "width": "100%",
                            "boxSizing": "border-box",
                        },
                    )
                ],
            ),
        ],
    )

    # Barra lateral de filtros e metadados compartilhada entre todas as páginas
    sidebar = html.Aside(
        className="sidebar",
        children=[
            # Logótipo e título
            html.Div(
                [html.Div("Nour", className="brand")],
                className="brand-lockup",
            ),
            # Painel 1: Perspetivas (exibido apenas no Dashboard)
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
                id="sidebar-panel-perspective",
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
                        dcc.Input(
                            id="years-input",
                            type="text",
                            value=f"{min_y}-{max_y}",
                            debounce=True,
                            className="readout-input",
                            placeholder=f"{min_y}-{max_y}",
                        ),
                        label_id="years-row-label",
                        control_id="years-slider-container",
                        range_id="years-range-container",
                        dropdown_control=dcc.Dropdown(
                            id="single-year-dropdown",
                            options=[{"label": f"Ano {y}", "value": y} for y in years],
                            value=min_y,
                            clearable=False,
                            className="dash-dropdown",
                        ),
                        dropdown_id="single-year-container",
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
                        dcc.Input(
                            id="scenarios-input",
                            type="text",
                            value=f"1-{n_scenarios}",
                            debounce=True,
                            className="readout-input",
                            placeholder=f"1-{n_scenarios}",
                        ),
                        label_id="scenarios-row-label",
                        control_id="scenarios-slider-container",
                        range_id="scenarios-range-container",
                        dropdown_control=dcc.Dropdown(
                            id="single-scenario-dropdown",
                            options=[
                                {
                                    "label": (
                                        f"Cenário {m.group()}"
                                        if (m := re.search(r"\d+", str(s)))
                                        else f"Cenário {idx}"
                                    ),
                                    "value": s,
                                }
                                for idx, s in enumerate(scenarios, start=1)
                            ],
                            value=scenarios[0] if scenarios else 1,
                            clearable=False,
                            className="dash-dropdown",
                        ),
                        dropdown_id="single-scenario-container",
                    ),
                ],
                id="sidebar-panel-recorte",
            ),
            # Painel 3: Seletor de indicador para distribuição (exibido apenas no Dashboard)
            panel(
                "Indicadores",
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
                id="sidebar-panel-indicador",
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
    )

    dre_div = build_statement_page(
        page_id="dre-page",
        title="Demonstração do Resultado do Exercício (DRE)",
        subtitle="Estrutura contábil da formação do resultado econômico. Detalha receitas, deduções, custos operacionais, despesas e tributos para mensurar a lucratividade líquida e o EBITDA da concessão.",
        table_title="Tabela DRE",
        table_id="tabela-dre-dinamica",
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

    balanco_div = build_balanco_page(
        page_id="balanco-page",
        title="Balanço Patrimonial",
        subtitle="Posição patrimonial e financeira da concessão ao final de cada exercício. Apresenta a composição dos ativos (circulante, realizável a longo prazo e permanente), passivos exigíveis e patrimônio líquido.",
        years=years,
        scenarios=scenarios,
        data=data,
    )

    return html.Div(
        className="app-container",
        children=[
            dcc.Location(id="url", refresh=False),
            dcc.Store(id="simplified-view-active-store"),
            dcc.Store(id="sidebar-collapsed-store", data=False),
            navbar,
            html.Div(
                className="pages-container",
                children=[
                    dashboard_div,
                    dre_div,
                    dfc_div,
                    balanco_div,
                ],
            ),
            sidebar,
        ],
    )
