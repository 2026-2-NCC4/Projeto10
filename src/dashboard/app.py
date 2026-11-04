"""Nour Financial Dashboard — Interactive Analytics for CTI Global Concession.

Implemented with Python, Dash (Plotly), and Pandas.
Concession Period: 2027–2038 (12 Years, with simulated Monte Carlo scenarios).

================================================================================
QUICKSTART & EXECUTION
================================================================================
To run this dashboard locally from the repository root:
    $ python src/dashboard/app.py
    (or $ python dashboard/app.py if inside the src/ directory)

Then open your browser at:
    http://127.0.0.1:8050/

================================================================================
ARCHITECTURAL OVERVIEW
================================================================================
1. DATA INGESTION & PIPELINE (load_data):
   - Reads processed CSV financial statements (DRE, Balanço Patrimonial, Fluxo de Caixa).
   - Pivots ledger accounts into columnar tabular data.
   - Normalizes Portuguese accounting account names (stripping accents and whitespace).
   - Computes key financial KPIs (Margens, ROA, ROE, Liquidez, Endividamento, EVA).
   - Handles Year 12 as a terminal liquidation year (contractual handback).

2. METAMODEL & UI LOOKUPS:
   - Perspective definitions ('gestao', 'tecnica', 'investidores').
   - Metric labels and metric-to-perspective mappings.

3. DESIGN SYSTEM & REUSABLE UI BUILDERS:
   - Color palette tokens and typography settings.
   - Formatters: money (R$ bi/mi), percent (%), ratio (x).
   - Component wrappers: cards, insights, collapsible panels, and styled charts.
   - Custom radial petal chart geometry (via petals.py) for relative KPI scoring.

4. APPLICATION LAYOUT:
   - Sidebar: Branding, Perspective tabs, Year range slider, Scenario slider, Metric selector, Metadata.
   - Main content: Hero radial score chart + dynamic analytical sections.

5. DYNAMIC RENDERING (render_content):
   - Slices data by selected years and Monte Carlo scenarios.
   - Computes medians, year-over-year variations, and risk probabilities.
   - Assembles perspective-specific dashboards (Gestão, Técnica, Investidores).

6. REACTIVE CALLBACKS (@app.callback):
   - Synchronizes UI controls (e.g. updating available metrics when perspective changes).
   - Updates interactive readout badges.
   - Re-renders the entire main dashboard canvas upon filter modifications.

================================================================================
HOW TO MANAGE & EXTEND THIS DASHBOARD
================================================================================
- HOW TO ADD A NEW FINANCIAL METRIC:
  1. In `load_data()`: Extract the underlying accounting account or compute the formula
     on the `wide` DataFrame (e.g., `wide["ebit"] = col("DRE EBIT")`).
  2. In `METRIC_LABELS`: Add its machine name and human-readable label
     (e.g., `"ebit": "EBIT"`).
  3. In `PERSPECTIVE_METRICS`: Add the metric key to the perspectives that should display it
     (e.g., `'gestao': ['margem_ebitda', 'ebit', ...]`).
  4. In `render_content()`: Add a metric card or chart trace if you wish to feature it.

- HOW TO ADD A NEW STAKEHOLDER PERSPECTIVE:
  1. In `PERSPECTIVES`: Add the key and display name (e.g., `"esg": "Sustentabilidade"`).
  2. In `PERSPECTIVE_SUMMARIES`: Add a descriptive subtitle for the sidebar.
  3. In `PERSPECTIVE_METRICS`: Define which metrics will be selectable for this perspective.
  4. In `render_content()`: Add an `if perspective == "esg": return page(...)` branch
     with the custom sections, cards, and charts relevant to that audience.

- HOW TO TWEAK ALERT THRESHOLDS:
  - In `render_content()`, search for `insight(` calls.
  - For example, `cash_risk >= 0.10` triggers an "alert" tone. Change `0.10` (10%) to your
    desired tolerance threshold.

- HOW TO CHANGE COLOR THEMES:
  - Edit the `COLORS` dictionary below. Update CSS variables in `style.css` to match.
"""

# ==============================================================================
# IMPORTS & SYSTEM DEPENDENCIES
import re
import sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# ==============================================================================
import sys, os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import unicodedata

# Data manipulation and analytics
import pandas as pd

# Data visualization libraries
import plotly.express as px
import plotly.graph_objects as go

# Web framework and interactive components
from dash import Dash, Input, Output, dcc, html

# Local helper for custom polar petal geometry (Bezier curve coordinates)
from petals import petal

# Data Loader files
from data_loader import load_data
from ui_elements import row, panel, money, percent, ratio, card, insight, section, chart
from dashboard.metrics_kpi.hero_radial import radial_figure
from config import (
    FONT_STACK,
    COLORS,
    METRIC_LABELS,
    PERSPECTIVES,
    PERSPECTIVE_SUMMARIES,
    PERSPECTIVE_METRICS,
)
from metrics_kpi.operational_overview import build_operational_overview_tiles
from metrics_kpi.technical_control import build_technical_controls_tiles
from metrics_kpi.yearly_aggregates import compute_yearly_medians
from metrics_kpi.charts import (
    create_trend_chart,
    create_distribution_chart,
    create_risk_chart,
    create_investor_scatter_chart,
    create_value_cash_chart,
    create_balance_chart,
)
from metrics_kpi.radar_normalization import compute_radar_scores
from metrics_kpi.hero_radial import radial_figure
from metrics_kpi.risk_analysis import compute_risk_probabilities
from metrics_kpi.dynamic_insights import compute_dynamic_insights
from metrics_kpi.balance_metrics import compute_balance_structure
from metrics_kpi.terminal_liquidation import build_terminal_liquidation_section

# Perspectives views
from perspectives.technical import render_technical_view
from perspectives.investors import render_investor_view
from perspectives.management import render_management_view
from perspectives.dashboard_layout import build_dfc_table, create_main_layout

# ==============================================================================
# PATH RESOLUTION & ENVIRONMENT SETUP
# ==============================================================================
# Identify the repository root directory relative to this script.
# If this file is at <repo>/src/dashboard/app.py, parents[1] points to <repo>/src.
ROOT = Path(__file__).resolve().parents[1]

# Locate the processed financial dataset. Searches both common folder structures:
# 1. <repo>/data/processed/... (standard project layout)
# 2. <repo>/src/data/processed/... (nested src layout)
DATA_PATH = next(
    (
        path
        for path in (
            ROOT / "data" / "processed" / "Dados_Formatados_CTI.csv",
            ROOT / "src" / "data" / "processed" / "Dados_Formatados_CTI.csv",
        )
        if path.exists()
    ),
    ROOT / "src" / "data" / "processed" / "Dados_Formatados_CTI.csv",
)

# Load data once at startup (singleton pattern in memory)
DATA = load_data(DATA_PATH)
# Unique concession years (1 to 12) and simulated Monte Carlo scenarios
YEARS = sorted(DATA.ano_num.unique())
SCENARIOS = sorted(DATA["Cenário"].dropna().unique())

# ==============================================================================
# DASH APPLICATION INITIALIZATION
# ==============================================================================
app = Dash(
    __name__,
    title="Nour | Painel financeiro",
    assets_folder=str(Path(__file__).parent),  # Loads style.css from dashboard folder
    suppress_callback_exceptions=True,  # Permits dynamic component IDs across tabs
)

server = app.server


@server.route("/dre")
@server.route("/dre/")
@server.route("/dfc")
@server.route("/dfc/")
@server.route("/dashboard")
@server.route("/dashboard/")
def serve_spa(*args, **kwargs):
    """Support direct URL access and browser refreshes on SPA routes."""
    return app.index(*args, **kwargs)


app.layout = create_main_layout(
    YEARS, SCENARIOS, PERSPECTIVES, PERSPECTIVE_METRICS, METRIC_LABELS, DATA
)


# ==============================================================================
# CORE DYNAMIC RENDERING ENGINE
# ==============================================================================
def render_content(
    years, scenarios, selected_metric="margem_ebitda", perspective="gestao"
):
    # --------------------------------------------------------------------------
    # 1. PARAMETER SANITIZATION & FILTERING
    # --------------------------------------------------------------------------
    year_from, year_to = years or [min(YEARS), max(YEARS)]
    scenario_from, scenario_to = scenarios or [1, len(SCENARIOS)]
    perspective = perspective if perspective in PERSPECTIVES else "gestao"
    allowed_metrics = PERSPECTIVE_METRICS[perspective]
    selected_metric = (
        selected_metric if selected_metric in allowed_metrics else allowed_metrics[0]
    )
    # Slice the chosen subset of scenarios
    chosen_scenarios = SCENARIOS[scenario_from - 1 : scenario_to]

    # Filter dataframe by selected years and scenarios
    filtered = DATA[
        DATA.ano_num.between(year_from, year_to)
        & DATA["Cenário"].isin(chosen_scenarios)
    ].copy()

    # Empty state fallback if user selected an invalid/empty slice
    if filtered.empty:
        return [
            html.Div("Escolha ao menos um ano e um cenário.", className="empty-state")
        ]

    # Separate operating years from the terminal liquidation year (Year 12)
    operating = filtered[~filtered.encerramento]
    if operating.empty:
        operating = filtered

    # Identify latest operating year in the filtered slice and compare with previous year
    latest_year = int(operating.ano_num.max())
    latest = operating[operating.ano_num.eq(latest_year)]
    prev = operating[operating.ano_num.eq(latest_year - 1)]

    # Helper: compute year-over-year median difference for a metric
    def delta(metric):
        return (
            latest[metric].median() - prev[metric].median() if not prev.empty else None
        )

    # --------------------------------------------------------------------------
    # 2. ASSEMBLE KPI TILES (CARDS)
    # --------------------------------------------------------------------------
    # Operational overview tiles (Revenue, EBITDA, Net Result, Cash Gen, Debt)
    tiles1 = build_operational_overview_tiles(latest, prev)
    tiles2 = build_technical_controls_tiles(latest, prev)
    # --------------------------------------------------------------------------
    # 3. COMPUTE YEARLY MEDIANS FOR TIME-SERIES VISUALIZATIONS
    # --------------------------------------------------------------------------
    by_year = compute_yearly_medians(operating)
    # REVENUE & EBITDA TREND AREA CHART
    trend = create_trend_chart(by_year, COLORS)
    # --------------------------------------------------------------------------
    # 4. RADIAL PETAL HERO CHART (RELATIVE 0-100 NORMALIZATION)
    # --------------------------------------------------------------------------
    scored_labels = compute_radar_scores(operating, latest)
    index_fig = radial_figure(scored_labels)
    # --------------------------------------------------------------------------
    # 5. MONTE CARLO RISK ANALYSIS MATRIX
    # -------------------------------------------------------------------------
    # 1. Processa os dados de risco
    risk_long, risk_labels, _ = compute_risk_probabilities(operating)
    # 2. Gera o gráfico de risco
    risk_fig = create_risk_chart(risk_long, risk_labels)
    # --------------------------------------------------------------------------
    # 6. DYNAMIC NARRATIVE INSIGHTS (THRESHOLD-DRIVEN)
    # --------------------------------------------------------------------------
    risk_long, risk_labels, risk = compute_risk_probabilities(operating)
    # Management Perspective Insights
    # Gera todos os blocos de insights dinâmicos baseados no contexto atual
    management_insights, technical_insights, investor_insights = (
        compute_dynamic_insights(
            latest, prev, risk, latest_year, selected_metric, METRIC_LABELS
        )
    )
    # --------------------------------------------------------------------------
    # 7. INVESTOR CHARTS (SCATTER, VALUE CREATION, BALANCE STRUCTURE)
    # --------------------------------------------------------------------------
    # Scatter plot: EBITDA Margin vs. EVA across all simulated scenarios
    # 1. Prepara dados do balanço
    balance = compute_balance_structure(latest)
    # 2. Gera os gráficos dos investidores
    scatter = create_investor_scatter_chart(latest, latest_year, COLORS)
    value_fig = create_value_cash_chart(by_year, COLORS)
    balance_fig = create_balance_chart(balance, latest_year)
    # --------------------------------------------------------------------------
    # 8. TERMINAL CONCESSION LIQUIDATION SECTION (YEAR 12)
    # --------------------------------------------------------------------------
    # Gera os componentes da liquidação terminal (caso existam dados de encerramento)
    terminal_children = build_terminal_liquidation_section(filtered)
    # --------------------------------------------------------------------------
    # 9. SCENARIO DISTRIBUTION BOXPLOT
    # --------------------------------------------------------------------------
    # Gera o gráfico de distribuição dos cenários
    distribution = create_distribution_chart(
        operating, selected_metric, METRIC_LABELS, COLORS
    )
    # Subtitle formatado com separadores
    subtitle = " · ".join(
        [
            PERSPECTIVES[perspective],
            f"Ano {latest_year} ({2026 + latest_year})",
            f"{len(chosen_scenarios):,} cenários".replace(",", "."),
            "Mediana do Recorte",
        ]
    )
    # --------------------------------------------------------------------------
    # 10. PERSPECTIVE VIEW ROUTING
    # --------------------------------------------------------------------------
    if perspective == "tecnica":
        return render_technical_view(
            index_fig, subtitle, latest, tiles2, technical_insights, risk_fig, distribution
        )

    if perspective == "investidores":
        return render_investor_view(
            index_fig,
            subtitle,
            latest,
            delta,
            investor_insights,
            scatter,
            value_fig,
            balance_fig,
            terminal_children,
            distribution,
        )

    # Default: Management / Executive
    return render_management_view(
        index_fig,
        subtitle,
        latest,
        tiles1,
        management_insights,
        trend,
        value_fig,
        risk_fig,
        terminal_children,
        distribution,
    )


# ==============================================================================
# REACTIVE CALLBACKS (INTERACTIVITY)
# ==============================================================================
@app.callback(
    Output("distribution-metric", "options"),
    Output("distribution-metric", "value"),
    Input("perspective", "value"),
)
def set_distribution_metrics(perspective):
    """Synchronize the metric dropdown options when the active perspective changes.

    Ensures that technical metrics (e.g. Liquidez Seca) appear only in 'Técnica',
    while management or investor metrics appear in their respective tabs.
    """
    perspective = perspective if perspective in PERSPECTIVE_METRICS else "gestao"
    metrics = PERSPECTIVE_METRICS[perspective]
    return (
        [{"label": METRIC_LABELS[key], "value": key} for key in metrics],
        metrics[0],
    )


@app.callback(
    Output("perspective-summary", "children"),
    Input("perspective", "value"),
)
def describe_perspective(perspective):
    """Update the explanatory subtitle below the perspective tabs in the sidebar."""
    return PERSPECTIVE_SUMMARIES.get(perspective, PERSPECTIVE_SUMMARIES["gestao"])


@app.callback(Output("years-readout", "children"), Input("years", "value"))
def show_year_range(years):
    """Update the text readout next to the concession years slider (e.g. '1–12')."""
    first, last = years
    return str(first) if first == last else f"{first}–{last}"


@app.callback(Output("scenarios-readout", "children"), Input("scenarios", "value"))
def show_scenario_count(scenarios):
    """Update the text readout next to the scenario slider with pt-BR thousand dots."""
    first, last = scenarios
    return f"{last - first + 1:,}".replace(",", ".")


@app.callback(
    Output("dashboard-content", "children"),
    Input("years", "value"),
    Input("scenarios", "value"),
    Input("distribution-metric", "value"),
    Input("perspective", "value"),
)
def render(years, scenarios, selected_metric, perspective):
    try:
        return render_content(years, scenarios, selected_metric, perspective)
    except Exception as error:
        app.logger.exception("Dashboard render failed")
        return [
            html.Div(
                f"Não foi possível montar os gráficos: {type(error).__name__}: {error}",
                className="empty-state",
            )
        ]


@app.callback(
    Output("dfc-table-content", "children"),
    Input("dfc-scenario", "value"),
    Input("dfc-years", "value"),
)
def render_dfc(scenario, years):
    selected_years = [year for year in YEARS if year in (years or YEARS)]
    return build_dfc_table(
        DATA,
        selected_years,
        scenario if scenario in SCENARIOS else SCENARIOS[0],
    )


@app.callback(
    Output("dashboard-page", "style"),
    Output("dre-page", "style"),
    Output("dfc-page", "style"),
    Output("tab-dashboard", "className"),
    Output("tab-dre", "className"),
    Output("tab-dfc", "className"),
    Input("url", "pathname"),
)
def display_page(pathname):

    base_tab = "nav-tab nav-link"
    active_tab = "nav-tab nav-link active"

    clean_path = (pathname or "/").rstrip("/") or "/"
    if clean_path == "/dre":
        return (
            {"display": "none"},
            {"display": "block"},
            {"display": "none"},
            base_tab,
            active_tab,
            base_tab,
        )

    elif clean_path == "/dfc":
        return (
            {"display": "none"},
            {"display": "none"},
            {"display": "block"},
            base_tab,
            base_tab,
            active_tab,
        )
    else:
        return (
            {},
            {"display": "none"},
            {"display": "none"},
            active_tab,
            base_tab,
            base_tab,
        )


# ==============================================================================
# SERVER-SIDE INITIAL HYDRATION & APPLICATION ENTRYPOINT
# ==============================================================================
# Pre-render the default view directly into the layout tree.
# This prevents an initial flash of unstyled/empty content before the first callback fires.
def _hydrate_dashboard_content(tree, content):
    if hasattr(tree, "id") and getattr(tree, "id") == "dashboard-content":
        tree.children = content
        return True
    children = getattr(tree, "children", None)
    if children:
        child_list = children if isinstance(children, list) else [children]
        for child in child_list:
            if _hydrate_dashboard_content(child, content):
                return True
    return False


_hydrate_dashboard_content(
    app.layout,
    render([min(YEARS), max(YEARS)], [1, len(SCENARIOS)], "margem_ebitda", "gestao"),
)


# ==============================================================================
# CALLBACKS DA DRE
# ==============================================================================
@app.callback(Output("dre-filtro-cenario", "options"), Input("dre-filtro-ano", "value"))
def atualizar_options_cenario_dre(ano_selecionado):
    col_cenario = "Cenário" if "Cenário" in DATA.columns else DATA.columns[1]

    cenarios_brutos = sorted(DATA[col_cenario].dropna().unique())

    options = []
    for c in cenarios_brutos:
        num_match = re.search(r"\d+", str(c))
        num = int(num_match.group()) if num_match else c

        options.append({"label": f"Cenário {num}", "value": c})

    return options


@app.callback(
    Output("tabela-dre-dinamica", "data"),
    Input("dre-filtro-ano", "value"),
    Input("dre-filtro-cenario", "value"),
)
def atualizar_tabela_dre(anos, cenarios):
    df_filtrado = DATA.copy()

    col_ano = (
        "ano_num"
        if "ano_num" in df_filtrado.columns
        else ("Ano" if "Ano" in df_filtrado.columns else df_filtrado.columns[0])
    )
    col_cenario = (
        "Cenário" if "Cenário" in df_filtrado.columns else df_filtrado.columns[1]
    )

    if anos is not None:
        lista_anos = anos if isinstance(anos, list) else [anos]
        df_filtrado = df_filtrado[df_filtrado[col_ano].isin(lista_anos)]

    if cenarios:
        lista_cenarios = cenarios if isinstance(cenarios, list) else [cenarios]
        df_filtrado = df_filtrado[df_filtrado[col_cenario].isin(lista_cenarios)]

    if df_filtrado.empty:
        return []

    linha = df_filtrado.median(numeric_only=True)

    def formata_moeda(valor):
        if pd.isna(valor):
            return "R$ 0,00"
        texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {texto}"

    dre_vertical = [
        {
            "sinal": "+",
            "conta": "Receita Bruta",
            "valor": formata_moeda(linha.get("DRE Receita", 0)),
        },
        {
            "sinal": "-",
            "conta": "Tributos",
            "valor": formata_moeda(linha.get("DRE Tributos", 0)),
        },
        {
            "sinal": "-",
            "conta": "Custos",
            "valor": formata_moeda(linha.get("DRE Custos", 0)),
        },
        {
            "sinal": "-",
            "conta": "Depreciação e Amortização",
            "valor": formata_moeda(linha.get("DRE Depreciacao e Amortizacao", 0)),
        },
        {
            "sinal": "=",
            "conta": "Resultado Operacional",
            "valor": formata_moeda(linha.get("DRE Resultado Operacional", 0)),
        },
        {
            "sinal": "+",
            "conta": "Receitas Financeiras",
            "valor": formata_moeda(linha.get("DRE Receitas Financeiras", 0)),
        },
        {
            "sinal": "-",
            "conta": "Despesas Financeiras",
            "valor": formata_moeda(linha.get("DRE Despesas Financeiras", 0)),
        },
        {
            "sinal": "=",
            "conta": "Resultado Financeiro",
            "valor": formata_moeda(linha.get("DRE Resultado Financeiro", 0)),
        },
        {
            "sinal": " ",
            "conta": "Outros Resultados Operacionais",
            "valor": formata_moeda(linha.get("DRE Outros Resultados Operacionais", 0)),
        },
        {
            "sinal": "=",
            "conta": "Resultado Antes do Imposto de Renda",
            "valor": formata_moeda(
                linha.get("DRE Resultado Antes do Imposto de Renda", 0)
            ),
        },
        {
            "sinal": "-",
            "conta": "Imposto de Renda e Contribuição Social",
            "valor": formata_moeda(
                linha.get("DRE Imposto de Renda e Contribuicao Social", 0)
            ),
        },
        {
            "sinal": "=",
            "conta": "Resultado Líquido",
            "valor": formata_moeda(linha.get("DRE Resultado Liquido", 0)),
        },
        {
            "sinal": "=",
            "conta": "Resultado Líquido após Equivalência",
            "valor": formata_moeda(
                linha.get("DRE Resultado Liquido apos Equivalencia", 0)
            ),
        },
        {
            "sinal": " ",
            "conta": "EBITDA",
            "valor": formata_moeda(linha.get("DRE EBITDA", 0)),
        },
    ]

    return dre_vertical


@app.callback(
    Output("grafico-melhores-anos-cenarios", "figure"),
    Input("grafico-melhores-anos-metrica", "value"),
)
def atualizar_grafico_melhores_anos(metrica_escolhida):
    col_ano = (
        "ano_num"
        if "ano_num" in DATA.columns
        else ("Ano" if "Ano" in DATA.columns else DATA.columns[0])
    )
    col_cenario = "Cenário" if "Cenário" in DATA.columns else DATA.columns[1]

    metrica_alvo = metrica_escolhida if metrica_escolhida else "DRE Resultado Liquido"
    nome_metrica = (
        "Resultado Líquido" if metrica_alvo == "DRE Resultado Liquido" else "DRE EBITDA"
    )

    df_trab = DATA.copy()

    if df_trab.empty or metrica_alvo not in df_trab.columns:
        return px.bar(title="Sem dados disponíveis")

    num_cenario = (
        pd.to_numeric(
            df_trab[col_cenario].astype(str).str.extract(r"(\d+)", expand=False),
            errors="coerce",
        )
        .fillna(0)
        .astype(int)
    )

    df_trab["Ano_Cenario_Label"] = (
        "Ano = "
        + df_trab[col_ano].astype(str)
        + " | Cenário "
        + num_cenario.astype(str)
    )

    top10_combinados = df_trab.sort_values(by=metrica_alvo, ascending=False).head(10)

    fig = px.bar(
        top10_combinados,
        x="Ano_Cenario_Label",
        y=metrica_alvo,
        text_auto=".2s",
        labels={
            "Ano_Cenario_Label": "Ano e Cenário",
            metrica_alvo: f"{nome_metrica} (R$)",
        },
    )

    fig.update_layout(
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font_family="sans-serif",
        xaxis_title="Ano | Cenário",
        yaxis_title=f"{nome_metrica} (R$)",
        margin=dict(t=40, b=20, l=20, r=20),
        barcornerradius=4,
    )
    fig.update_traces(marker_color="#0284c7")

    return fig


@app.callback(
    Output("grafico-top10-cenarios", "figure"),
    [Input("grafico-filtro-ano", "value"), Input("grafico-filtro-metrica", "value")],
)
def atualizar_grafico_top10(ano_selecionado, metrica_escolhida):
    col_ano = (
        "ano_num"
        if "ano_num" in DATA.columns
        else ("Ano" if "Ano" in DATA.columns else DATA.columns[0])
    )
    col_cenario = "Cenário" if "Cenário" in DATA.columns else DATA.columns[1]

    metrica_alvo = metrica_escolhida if metrica_escolhida else "DRE Resultado Liquido"
    nome_metrica_label = (
        "Resultado Líquido" if metrica_alvo == "DRE Resultado Liquido" else "EBITDA"
    )

    df_trab = DATA.copy()

    # 1. Define o Ano 1 como padrão se nenhum ano estiver selecionado no dropdown (None)
    ano_efetivo = ano_selecionado if ano_selecionado is not None else 1

    df_trab = df_trab[df_trab[col_ano] == ano_efetivo]

    if df_trab.empty or metrica_alvo not in df_trab.columns:
        return px.line(title="Sem dados disponíveis para esta seleção")

    # Extrai o número do cenário e cria o rótulo "Cenário X"
    num_cenario = (
        pd.to_numeric(
            df_trab[col_cenario].astype(str).str.extract(r"(\d+)", expand=False),
            errors="coerce",
        )
        .fillna(0)
        .astype(int)
    )
    df_trab["Cenario_Formatado"] = "Cenário " + num_cenario.astype(str)

    # Ordena pelos 10 melhores
    top10 = df_trab.sort_values(by=metrica_alvo, ascending=False).head(10)

    # Gráfico de Linha com Marcadores (bolinhas)
    fig = px.line(
        top10,
        x="Cenario_Formatado",
        y=metrica_alvo,
        markers=True,
        text=top10[metrica_alvo].apply(lambda v: f"{v:,.0f}".replace(",", ".")),
        labels={
            "Cenario_Formatado": "Cenário Simulado",
            metrica_alvo: f"{nome_metrica_label} (R$)",
        },
    )

    # Estilização visual mantendo as cores e marcadores circulares
    fig.update_traces(
        line_color="#0284c7",
        line_width=3,
        marker=dict(size=10, color="#0284c7", symbol="circle"),
        textposition="top center",
    )

    fig.update_layout(
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font_family="sans-serif",
        xaxis_title="Cenário",
        yaxis_title=f"{nome_metrica_label} (R$)",
        margin=dict(t=40, b=20, l=20, r=20),
    )

    return fig


if __name__ == "__main__":
    # To run in debug mode for development (auto-reload on save, detailed in-browser debugger):
    # Change to: app.run(debug=True, port=8050)
    app.run(debug=True)
