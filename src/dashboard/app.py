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
from dash import Dash, Input, Output, State, callback_context, dcc, html, no_update

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
from perspectives.dashboard_layout import (
    build_balanco_table,
    build_dfc_table,
    build_dre_table,
    create_main_layout,
)

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
@server.route("/balanco")
@server.route("/balanco/")
@server.route("/dashboard")
@server.route("/dashboard/")
def serve_spa(*args, **kwargs):
    """Support direct URL access and browser refreshes on SPA routes."""
    return app.index(*args, **kwargs)


app.layout = create_main_layout(
    YEARS, SCENARIOS, PERSPECTIVES, PERSPECTIVE_METRICS, METRIC_LABELS, DATA
)


# ==============================================================================
# SELECTION PARSING & RESOLUTION HELPERS
# ==============================================================================
def parse_selection_string(text):
    """Parse a range/list selection string like:
      '12' -> [12]
      '12-15' -> [12, 13, 14, 15]
      '15-18;19' -> [15, 16, 17, 18, 19]
      '1, 2, 5-8' -> [1, 2, 5, 6, 7, 8]
    """
    if text is None:
        return []
    cleaned = str(text).replace(",", ";").replace("–", "-").replace("—", "-")
    tokens = [t.strip() for t in cleaned.split(";") if t.strip()]
    selected = set()
    for token in tokens:
        range_match = re.match(r"^(\d+)\s*-\s*(\d+)$", token)
        if range_match:
            start = int(range_match.group(1))
            end = int(range_match.group(2))
            if start <= end:
                selected.update(range(start, end + 1))
            else:
                selected.update(range(end, start + 1))
            continue
        num_match = re.match(r"^\d+$", token)
        if num_match:
            selected.add(int(num_match.group()))
            continue
    return sorted(selected)


def get_selected_years(years_val, all_years):
    if isinstance(years_val, str):
        nums = parse_selection_string(years_val)
    elif isinstance(years_val, (list, tuple)):
        if (
            len(years_val) == 2
            and all(isinstance(x, (int, float)) for x in years_val)
            and years_val[0] in all_years
            and years_val[1] in all_years
        ):
            first, last = int(years_val[0]), int(years_val[1])
            nums = list(range(min(first, last), max(first, last) + 1))
        else:
            nums = [int(x) for x in years_val if str(x).isdigit()]
    else:
        return list(all_years)

    valid_set = set(all_years)
    result = set()
    for n in nums:
        if n in valid_set:
            result.add(n)
        elif (n - 2026) in valid_set:
            result.add(n - 2026)
    res_list = sorted(result)
    return res_list if res_list else list(all_years)


def get_selected_scenarios(scenarios_val, all_scenarios):
    if isinstance(scenarios_val, str):
        nums = parse_selection_string(scenarios_val)
    elif isinstance(scenarios_val, (list, tuple)):
        if any(isinstance(x, str) and not x.isdigit() for x in scenarios_val):
            return [s for s in scenarios_val if s in all_scenarios]
        if len(scenarios_val) == 2 and all(isinstance(x, (int, float)) for x in scenarios_val):
            first, last = int(scenarios_val[0]), int(scenarios_val[1])
            nums = list(range(min(first, last), max(first, last) + 1))
        else:
            nums = [int(x) for x in scenarios_val if str(x).isdigit()]
    else:
        return list(all_scenarios)

    if not nums:
        return list(all_scenarios)

    num_to_scen = {}
    for s in all_scenarios:
        m = re.search(r"\d+", str(s))
        if m:
            num_to_scen[int(m.group())] = s

    for idx, s in enumerate(all_scenarios, start=1):
        if idx not in num_to_scen:
            num_to_scen[idx] = s

    result = [num_to_scen[n] for n in nums if n in num_to_scen]
    return result if result else list(all_scenarios)


# ==============================================================================
# CORE DYNAMIC RENDERING ENGINE
# ==============================================================================
def render_content(
    years, scenarios, selected_metric="margem_ebitda", perspective="gestao"
):

    # --------------------------------------------------------------------------
    # 1. PARAMETER SANITIZATION & FILTERING
    # --------------------------------------------------------------------------
    selected_years = get_selected_years(years, YEARS)
    chosen_scenarios = get_selected_scenarios(scenarios, SCENARIOS)
    perspective = perspective if perspective in PERSPECTIVES else "gestao"
    allowed_metrics = PERSPECTIVE_METRICS[perspective]
    selected_metric = (
        selected_metric if selected_metric in allowed_metrics else allowed_metrics[0]
    )

    # Filter dataframe by selected years and scenarios
    filtered = DATA[
        DATA.ano_num.isin(selected_years)
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
    prev_year = max([y for y in selected_years if y < latest_year], default=latest_year - 1)
    prev = operating[operating.ano_num.eq(prev_year)]

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
    if perspective == "tecnica":
        return render_technical_view(
            index_fig,
            subtitle,
            latest,
            tiles2,
            technical_insights,
            risk_fig,
            distribution,
            latest_year=latest_year,
            prev=prev,
            risk=risk,
            selected_metric=selected_metric,
            metric_labels=METRIC_LABELS,
        )

    if perspective == "investidores":
        return render_investor_view(  # <--- Adicionado o "return" aqui
            index_fig=index_fig,
            subtitle=subtitle,
            latest=latest,
            delta=delta,
            investor_insights=investor_insights,
            scatter=scatter,
            value_fig=value_fig,
            balance_fig=balance_fig,
            terminal_children=terminal_children,
            distribution=distribution,
            historical_data=operating,
            prev=prev,
            latest_year=latest_year,
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


# ==============================================================================
# BIDIRECTIONAL SLIDER & TEXT INPUT SYNCHRONIZATION
# ==============================================================================
@app.callback(
    Output("years", "value"),
    Input("years-input", "value"),
    State("years", "value"),
    prevent_initial_call=True,
)
def sync_years_input_to_slider(text_val, current_slider):
    """Update years slider when user types in the input box."""
    if not text_val:
        return no_update
    selected = get_selected_years(text_val, YEARS)
    if not selected:
        return no_update
    target = [min(selected), max(selected)]
    if current_slider == target:
        return no_update
    return target


@app.callback(
    Output("years-input", "value"),
    Input("years", "value"),
    Input("url", "pathname"),
    State("years-input", "value"),
)
def sync_years_slider_to_input(slider_val, pathname, current_text):
    """Update years input text when user moves the slider or navigates pages."""
    clean_path = (pathname or "/").rstrip("/") or "/"
    first, last = slider_val if slider_val else (min(YEARS), max(YEARS))
    if clean_path == "/dre":
        target = str(first)
    else:
        target = str(first) if first == last else f"{first}-{last}"

    if current_text == target:
        return no_update
    return target


@app.callback(
    Output("scenarios", "value"),
    Input("scenarios-input", "value"),
    State("scenarios", "value"),
    prevent_initial_call=True,
)
def sync_scenarios_input_to_slider(text_val, current_slider):
    """Update scenarios slider when user types in the input box."""
    if not text_val:
        return no_update
    nums = parse_selection_string(text_val)
    valid_nums = [n for n in nums if 1 <= n <= len(SCENARIOS)]
    if not valid_nums:
        return no_update
    target = [min(valid_nums), max(valid_nums)]
    if current_slider == target:
        return no_update
    return target


@app.callback(
    Output("scenarios-input", "value"),
    Input("scenarios", "value"),
    Input("url", "pathname"),
    State("scenarios-input", "value"),
)
def sync_scenarios_slider_to_input(slider_val, pathname, current_text):
    """Update scenarios input text when user moves the slider or navigates pages."""
    clean_path = (pathname or "/").rstrip("/") or "/"
    first, last = slider_val if slider_val else (1, len(SCENARIOS))
    if clean_path in ("/dfc", "/balanco"):
        target = str(first)
    else:
        target = str(first) if first == last else f"{first}-{last}"

    if current_text == target:
        return no_update
    return target


@app.callback(
    Output("dashboard-content", "children"),
    Input("years-input", "value"),
    Input("scenarios-input", "value"),
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


app.clientside_callback(
    """
    function(value) {
        var isSimplified = Array.isArray(value) && value.length > 0;
        if (typeof document !== 'undefined' && document.body) {
            document.body.classList.toggle('simplified-view-active', isSimplified);
        }
        return isSimplified;
    }
    """,
    Output("simplified-view-active-store", "data"),
    Input("toggle-simplified-view", "value"),
    prevent_initial_call=False,
)


@app.callback(
    Output("dfc-table-content", "children"),
    Input("years-input", "value"),
    Input("scenarios-input", "value"),
    Input("single-scenario-dropdown", "value"),
    Input("url", "pathname"),
)
def render_dfc(years, scenarios, single_scenario_val, pathname):
    clean_path = (pathname or "/").rstrip("/") or "/"
    selected_years = get_selected_years(years, YEARS)
    if clean_path == "/dfc" and single_scenario_val is not None:
        single_scenario = single_scenario_val
    else:
        chosen_scenarios = get_selected_scenarios(scenarios, SCENARIOS)
        single_scenario = chosen_scenarios[0] if chosen_scenarios else SCENARIOS[0]
    return build_dfc_table(
        DATA,
        selected_years,
        single_scenario,
    )


@app.callback(
    Output("balanco-table-content", "children"),
    Input("years-input", "value"),
    Input("scenarios-input", "value"),
    Input("single-scenario-dropdown", "value"),
    Input("url", "pathname"),
)
def render_balanco(years, scenarios, single_scenario_val, pathname):
    clean_path = (pathname or "/").rstrip("/") or "/"
    selected_years = get_selected_years(years, YEARS)
    if clean_path == "/balanco" and single_scenario_val is not None:
        single_scenario = single_scenario_val
    else:
        chosen_scenarios = get_selected_scenarios(scenarios, SCENARIOS)
        single_scenario = chosen_scenarios[0] if chosen_scenarios else SCENARIOS[0]
    return build_balanco_table(
        DATA,
        selected_years,
        single_scenario,
    )


@app.callback(
    Output("dashboard-page", "style"),
    Output("dre-page", "style"),
    Output("dfc-page", "style"),
    Output("balanco-page", "style"),
    Output("sidebar-panel-perspective", "style"),
    Output("sidebar-panel-indicador", "style"),
    Output("years-row-label", "children"),
    Output("scenarios-row-label", "children"),
    Output("years-range-container", "style"),
    Output("single-year-container", "style"),
    Output("scenarios-range-container", "style"),
    Output("single-scenario-container", "style"),
    Output("tab-dashboard", "className"),
    Output("tab-dre", "className"),
    Output("tab-dfc", "className"),
    Output("tab-balanco", "className"),
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
            {"display": "none"},
            {"display": "none"},
            {"display": "none"},
            "Ano da concessão (1 ano)",
            "Cenários simulados",
            {"display": "none"},
            {},
            {},
            {"display": "none"},
            base_tab,
            active_tab,
            base_tab,
            base_tab,
        )

    elif clean_path == "/dfc":
        return (
            {"display": "none"},
            {"display": "none"},
            {"display": "block"},
            {"display": "none"},
            {"display": "none"},
            {"display": "none"},
            "Anos da concessão",
            "Cenário simulado (1 cenário)",
            {},
            {"display": "none"},
            {"display": "none"},
            {},
            base_tab,
            base_tab,
            active_tab,
            base_tab,
        )

    elif clean_path == "/balanco":
        return (
            {"display": "none"},
            {"display": "none"},
            {"display": "none"},
            {"display": "block"},
            {"display": "none"},
            {"display": "none"},
            "Anos da concessão",
            "Cenário simulado (1 cenário)",
            {},
            {"display": "none"},
            {"display": "none"},
            {},
            base_tab,
            base_tab,
            base_tab,
            active_tab,
        )
    else:
        return (
            {},
            {"display": "none"},
            {"display": "none"},
            {"display": "none"},
            {},
            {},
            "Anos da concessão",
            "Cenários simulados",
            {},
            {"display": "none"},
            {},
            {"display": "none"},
            active_tab,
            base_tab,
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
@app.callback(
    Output("tabela-dre-dinamica", "children"),
    Input("years-input", "value"),
    Input("scenarios-input", "value"),
    Input("single-year-dropdown", "value"),
    Input("url", "pathname"),
)
def atualizar_tabela_dre(years, scenarios, single_year_val, pathname):
    clean_path = (pathname or "/").rstrip("/") or "/"
    if clean_path == "/dre" and single_year_val is not None:
        target_year = int(single_year_val)
    else:
        selected_years = get_selected_years(years, YEARS)
        target_year = selected_years[0] if selected_years else min(YEARS)
    chosen_scenarios = get_selected_scenarios(scenarios, SCENARIOS)

    df_filtrado = DATA[
        (DATA.ano_num == target_year)
        & DATA["Cenário"].isin(chosen_scenarios)
    ].copy()

    if df_filtrado.empty:
        return build_dre_table([])

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

    return build_dre_table(dre_vertical)


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
    fig.update_traces(marker_color="#63aee7")

    return fig


@app.callback(
    Output("grafico-top10-cenarios", "figure"),
    Input("single-year-dropdown", "value"),
    Input("years-input", "value"),
    Input("grafico-filtro-metrica", "value"),
)
def atualizar_grafico_top10(single_year_val, years_input_val, metrica_escolhida):
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

    # Define o ano selecionado na barra lateral (priorizando o dropdown de ano da DRE)
    if single_year_val is not None:
        ano_efetivo = int(single_year_val)
    else:
        selected_years = get_selected_years(years_input_val, YEARS)
        ano_efetivo = selected_years[0] if selected_years else 1

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
        line_color="#63aee7",
        line_width=3,
        marker=dict(size=10, color="#7ab6e4", symbol="circle"),
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
