"""NOUR Financial Dashboard — Interactive Analytics for CTI Global Concession.

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
# ==============================================================================
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
from config import FONT_STACK, COLORS, METRIC_LABELS, PERSPECTIVES, PERSPECTIVE_SUMMARIES, PERSPECTIVE_METRICS
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

#Perspectives views
from perspectives.technical import render_technical_view
from perspectives.investors import render_investor_view
from perspectives.management import render_management_view
from perspectives.dashboard_layout import create_main_layout


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
    title="NOUR | Painel financeiro",
    assets_folder=str(Path(__file__).parent),  # Loads style.css from dashboard folder
    suppress_callback_exceptions=True,        # Permits dynamic component IDs across tabs
)

server = app.server

app.layout = create_main_layout(YEARS, SCENARIOS, PERSPECTIVES, PERSPECTIVE_METRICS, METRIC_LABELS)

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
    risk_long, risk_labels = compute_risk_probabilities(operating)
    # 2. Gera o gráfico de risco
    risk_fig = create_risk_chart(risk_long, risk_labels)
    # --------------------------------------------------------------------------
    # 6. DYNAMIC NARRATIVE INSIGHTS (THRESHOLD-DRIVEN)
    # --------------------------------------------------------------------------
    risk_long, risk_labels, risk = compute_risk_probabilities(operating)
    # Management Perspective Insights
    # Gera todos os blocos de insights dinâmicos baseados no contexto atual
    management_insights, technical_insights, investor_insights = compute_dynamic_insights(
        latest, prev, risk, latest_year, selected_metric, METRIC_LABELS
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
    distribution = create_distribution_chart(operating, selected_metric, METRIC_LABELS, COLORS)
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
        return render_technical_view(index_fig, subtitle, tiles2, technical_insights, risk_fig, distribution)

    if perspective == "investidores":
        return render_investor_view(
            index_fig, subtitle, latest, delta, investor_insights, 
            scatter, value_fig, balance_fig, terminal_children, distribution
        )

    # Default: Management / Executive
    return render_management_view(
        index_fig, subtitle, tiles1, management_insights, 
        trend, value_fig, risk_fig, terminal_children, distribution
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


# ==============================================================================
# SERVER-SIDE INITIAL HYDRATION & APPLICATION ENTRYPOINT
# ==============================================================================
# Pre-render the default view directly into the layout tree.
# This prevents an initial flash of unstyled/empty content before the first callback fires.
app.layout.children[0].children[0].children = render(
    [min(YEARS), max(YEARS)], [1, len(SCENARIOS)], "margem_ebitda", "gestao"
)

if __name__ == "__main__":
    # To run in debug mode for development (auto-reload on save, detailed in-browser debugger):
    # Change to: app.run(debug=True, port=8050)
    app.run(debug=False)
