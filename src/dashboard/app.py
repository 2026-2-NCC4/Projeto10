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
from hero_radial import radial_figure
from config import FONT_STACK, COLORS, METRIC_LABELS, PERSPECTIVES, PERSPECTIVE_SUMMARIES, PERSPECTIVE_METRICS
from metrics_kpi.operational_overview import build_operational_overview_tiles
from metrics_kpi.technical_control import build_technical_controls_tiles
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

# DATA LOADER
DATA = load_data(DATA_PATH)

# ==============================================================================
# GLOBAL METAMODEL & UI CONFIGURATION LOOKUPS
# ==============================================================================
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

# Expose underlying Flask WSGI server (required for deployment via Gunicorn, Waitress, etc.)
server = app.server

# ==============================================================================
# DASHBOARD PAGE SHELL
# ==============================================================================
def page(figure, subtitle, sections):
    """Assemble the hero header banner and the vertical stack of content sections."""
    return [
        html.Section(
            [
                html.Div(
                    [html.H1("Painel financeiro"), html.P(subtitle)],
                    className="hero-copy",
                ),
                dcc.Graph(
                    figure=figure,
                    config={"displayModeBar": False},
                    responsive=True,
                    className="hero-chart",
                    # Style note: dcc.Graph sets inline height: 100%, which defaults to 0
                    # on auto-height parents. Explicit clamp guarantees responsive height.
                    style={"height": "clamp(500px, 64vh, 700px)", "width": "100%"},
                ),
            ],
            className="hero",
        ),
        html.Div(sections, className="stack"),
    ]


# ==============================================================================
# MASTER DASHBOARD LAYOUT DEFINITION (DOM TREE)
# ==============================================================================
app.layout = html.Div(
    className="dashboard",
    children=[
        # Main area: Hosts dynamic dashboard content rendered by the reactive callback
        html.Main(
            className="main",
            children=[html.Div(id="dashboard-content", className="content")],
        ),
        # Sidebar: Hosts branding, interactive filters, and metadata
        html.Aside(
            className="sidebar",
            children=[
                # BRAND LOCKUP
                html.Div(
                    [
                        html.Div("NOUR", className="brand"),
                        html.Div(
                            "CTI Global | Concessão 2027–2038",
                            className="brand-caption",
                        ),
                    ],
                    className="brand-lockup",
                ),
                # FILTER PANEL 1: PERSPECTIVE SELECTOR
                panel(
                    "Perspectiva",
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
                                for key, label in PERSPECTIVES.items()
                            ],
                        ),
                        html.P(
                            PERSPECTIVE_SUMMARIES["gestao"],
                            id="perspective-summary",
                            className="panel-note",
                        ),
                    ],
                ),
                # FILTER PANEL 2: DATA SLICING (YEARS & SCENARIOS)
                panel(
                    "Recorte",
                    [
                        # Year range slider (Concession Years 1 through 12)
                        row(
                            "Anos da concessão",
                            dcc.RangeSlider(
                                id="years",
                                min=min(YEARS),
                                max=max(YEARS),
                                step=1,
                                value=[min(YEARS), max(YEARS)],
                                marks=None,
                                tooltip={"placement": "bottom"},
                            ),
                            html.Output(
                                f"{min(YEARS)}–{max(YEARS)}",
                                id="years-readout",
                                className="readout",
                            ),
                        ),
                        # Monte Carlo scenario range slider
                        row(
                            "Cenários simulados",
                            dcc.RangeSlider(
                                id="scenarios",
                                min=1,
                                max=len(SCENARIOS),
                                step=1,
                                value=[1, len(SCENARIOS)],
                                marks=None,
                                tooltip={"placement": "bottom"},
                            ),
                            html.Output(
                                f"{len(SCENARIOS):,}".replace(",", "."),
                                id="scenarios-readout",
                                className="readout",
                            ),
                        ),
                    ],
                ),
                # FILTER PANEL 3: METRIC DISTRIBUTION SELECTOR
                panel(
                    "Indicador",
                    [
                        row(
                            "Distribuição",
                            dcc.Dropdown(
                                id="distribution-metric",
                                options=[
                                    {"label": label, "value": key}
                                    for key, label in METRIC_LABELS.items()
                                    if key in PERSPECTIVE_METRICS["gestao"]
                                ],
                                value="margem_ebitda",
                                clearable=False,
                            ),
                        )
                    ],
                ),
                # METADATA & DATASET PROVENANCE
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
                                    f"{len(SCENARIOS)} cenários · {len(YEARS)} anos"
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


# ==============================================================================
# CORE DYNAMIC RENDERING ENGINE
# ==============================================================================
def render_content(
    years, scenarios, selected_metric="margem_ebitda", perspective="gestao"
):
    """Render the dashboard content dynamically based on user-selected filters.

    Parameters:
        years (list): [min_year, max_year] selected on the concession years slider.
        scenarios (list): [min_idx, max_idx] selected on the scenario count slider.
        selected_metric (str): Key of the metric chosen for distribution analysis.
        perspective (str): Active stakeholder perspective ('gestao', 'tecnica', 'investidores').

    Returns:
        list: Component hierarchy forming the full page for the selected perspective.
    """
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
    by_year = operating.groupby(["ano_num", "ano_calendario"], as_index=False).agg(
        receita=("receita", "median"),
        ebitda=("ebitda", "median"),
        margem_ebitda=("margem_ebitda", "median"),
        roe=("roe", "median"),
        liquidez_corrente=("liquidez_corrente", "median"),
        capital_terceiros=("participacao_capital_terceiros", "median"),
        eva=("eva", "median"),
        geracao_caixa=("geracao_caixa", "median"),
    )

    # REVENUE & EBITDA TREND AREA CHART
    trend = px.area(
        by_year,
        x="ano_calendario",
        y="receita",
        title="Receita ao longo da concessão",
        color_discrete_sequence=[COLORS["teal"]],
    )
    trend.add_trace(
        go.Scatter(
            x=by_year.ano_calendario,
            y=by_year.ebitda,
            mode="lines+markers",
            name="EBITDA",
            line={"color": COLORS["amber"], "width": 3},
            marker={"size": 7},
        )
    )
    trend.update_yaxes(tickprefix="R$ ", tickformat="~s")

    # --------------------------------------------------------------------------
    # 4. RADIAL PETAL HERO CHART (RELATIVE 0-100 NORMALIZATION)
    # --------------------------------------------------------------------------
    # Normalizes current median against the 5th and 95th percentiles of historical data,
    # ensuring robust 0-100 relative scores without outlier distortion.
    radar_metrics = [
        ("Margem", "margem_ebitda"),
        ("ROE", "roe"),
        ("Liquidez", "liquidez_corrente"),
        ("EVA", "eva"),
        ("Caixa", "geracao_caixa"),
        ("Receita", "receita"),
    ]
    radar_values = []
    for label, key in radar_metrics:
        vals, med = operating[key].dropna(), latest[key].median()
        lo, hi = vals.quantile(0.05), vals.quantile(0.95)
        score = (
            50
            if pd.isna(med) or hi == lo
            else max(8, min(100, 12 + 88 * (med - lo) / (hi - lo)))
        )
        radar_values.append((label, score))
    index_fig = radial_figure(radar_values)

    # --------------------------------------------------------------------------
    # 5. MONTE CARLO RISK ANALYSIS MATRIX
    # --------------------------------------------------------------------------
    # Evaluates binary adverse conditions across all simulated scenarios per year:
    # - Net Loss (Resultado Líquido < 0)
    # - Negative Cash (Saldo Final de Caixa < 0)
    # - Critical Liquidity (Liquidez Corrente < 1.0x)
    # - Value Destruction (EVA < 0)
    risk = (
        operating.assign(
            prejuizo=operating.resultado_liquido.lt(0).astype(float),
            caixa_negativo=operating.saldo_final_caixa.lt(0).astype(float),
            liquidez_critica=operating.liquidez_corrente.lt(1).astype(float),
            eva_negativo=operating.eva.lt(0).astype(float),
        )
        .groupby("ano_calendario", as_index=False)[
            ["prejuizo", "caixa_negativo", "liquidez_critica", "eva_negativo"]
        ]
        .mean()
    )
    risk_labels = {
        "prejuizo": "Prejuízo no ano",
        "caixa_negativo": "Caixa negativo",
        "liquidez_critica": "Liquidez abaixo de 1,0x",
        "eva_negativo": "EVA negativo",
    }
    risk_long = risk.melt(
        "ano_calendario", var_name="Evento", value_name="Probabilidade"
    )
    risk_long["Evento"] = risk_long["Evento"].map(risk_labels)
    risk_fig = px.area(
        risk_long,
        x="ano_calendario",
        y="Probabilidade",
        color="Evento",
        title="Mapa de risco · probabilidade por ano",
        labels={"ano_calendario": "Ano calendário"},
        color_discrete_map={
            risk_labels["prejuizo"]: "#501839",
            risk_labels["caixa_negativo"]: "#55a9e8",
            risk_labels["liquidez_critica"]: "#7a4b69",
            risk_labels["eva_negativo"]: "#2e7fb9",
        },
    )
    risk_fig.update_yaxes(tickformat=".0%")

    # --------------------------------------------------------------------------
    # 6. DYNAMIC NARRATIVE INSIGHTS (THRESHOLD-DRIVEN)
    # --------------------------------------------------------------------------
    latest_risk = risk.loc[risk["ano_calendario"].eq(2026 + latest_year)].iloc[0]
    revenue_change = delta("receita")
    margin_change = delta("margem_ebitda")
    cash_risk = latest_risk["caixa_negativo"]
    liquidity_risk = latest_risk["liquidez_critica"]
    eva_risk = latest_risk["eva_negativo"]
    selected_values = latest[selected_metric].dropna()
    p10, p90 = selected_values.quantile([0.10, 0.90])

    # Management Perspective Insights
    management_insights = [
        insight(
            "Tração de receita",
            (
                f"A mediana da receita variou {money(revenue_change)} frente ao ano anterior."
                if revenue_change is not None
                else "Não há ano anterior no recorte para comparar a receita."
            ),
        ),
        insight(
            "Eficiência operacional",
            (
                f"A margem EBITDA mudou {f'{margin_change * 100:+.1f}'.replace('.', ',')} p.p. no período, "
                f"chegando a {percent(latest.margem_ebitda.median())}."
                if margin_change is not None
                else f"A margem EBITDA mediana é de {percent(latest.margem_ebitda.median())}."
            ),
        ),
        insight(
            "Prioridade de caixa",
            f"{cash_risk:.0%} dos cenários encerram o ano com caixa negativo; "
            "esse é o principal sinal para acompanhar no plano de ação.",
            "alert" if cash_risk >= 0.10 else "positive",
        ),
    ]

    # Technical / Controllership Insights
    technical_insights = [
        insight(
            "Cobertura de curto prazo",
            f"A liquidez corrente mediana é {ratio(latest.liquidez_corrente.median())}; "
            f"{liquidity_risk:.0%} dos cenários ficam abaixo de 1,0x.",
            "alert" if liquidity_risk >= 0.10 else "positive",
        ),
        insight(
            "Dependência de terceiros",
            f"O capital de terceiros representa, na mediana, "
            f"{percent(latest.participacao_capital_terceiros.median())} do patrimônio líquido.",
        ),
        insight(
            "Faixa de incerteza",
            f"No ano mais recente, os 80% centrais de {METRIC_LABELS[selected_metric].lower()} "
            f"vão de {percent(p10) if selected_metric in {'participacao_capital_terceiros', 'composicao_endividamento'} else ratio(p10)} "
            f"a {percent(p90) if selected_metric in {'participacao_capital_terceiros', 'composicao_endividamento'} else ratio(p90)}.",
        ),
    ]

    # Investor / Shareholder Insights
    investor_insights = [
        insight(
            "Criação de valor",
            f"O EVA mediano é {money(latest.eva.median())}; "
            f"{eva_risk:.0%} dos cenários apresentam EVA negativo no ano.",
            "alert" if eva_risk >= 0.10 else "positive",
        ),
        insight(
            "Retorno sobre o capital",
            f"O ROE mediano é {percent(latest.roe.median())}. "
            "Leia este indicador junto à estrutura de capital e à dispersão entre cenários.",
        ),
        insight(
            "Assimetria de cenários",
            f"Para {METRIC_LABELS[selected_metric].lower()}, os percentis 10 e 90 no ano são "
            f"{percent(p10) if selected_metric in {'margem_ebitda', 'roa', 'roe'} else money(p10)} e "
            f"{percent(p90) if selected_metric in {'margem_ebitda', 'roa', 'roe'} else money(p90)}.",
        ),
    ]

    # --------------------------------------------------------------------------
    # 7. INVESTOR CHARTS (SCATTER, VALUE CREATION, BALANCE STRUCTURE)
    # --------------------------------------------------------------------------
    # Scatter plot: EBITDA Margin vs. EVA across all simulated scenarios
    scatter = px.scatter(
        latest,
        x="margem_ebitda",
        y="eva",
        color="Cenário",
        size="receita",
        size_max=20,
        opacity=0.72,
        title=f"Cenários · margem EBITDA e EVA · Ano {latest_year}",
        labels={"margem_ebitda": "Margem EBITDA", "eva": "EVA (R$)"},
        color_discrete_sequence=[COLORS["plum"], COLORS["sky"]],
    )
    scatter.update_xaxes(tickformat=".0%")

    # Line chart: EVA vs. Operating Cash Generation over the concession timeline
    value_fig = px.line(
        by_year,
        x="ano_calendario",
        y=["eva", "geracao_caixa"],
        markers=True,
        title="EVA e geração de caixa",
        labels={
            "ano_calendario": "Ano calendário",
            "value": "Valor",
            "eva": "EVA",
            "geracao_caixa": "Geração de caixa",
        },
        color_discrete_sequence=[COLORS["plum"], COLORS["sky"]],
    )
    value_fig.for_each_trace(
        lambda trace: trace.update(
            name={"eva": "EVA", "geracao_caixa": "Geração de caixa"}[trace.name]
        )
    )
    value_fig.update_yaxes(tickprefix="R$ ", tickformat="~s")

    # Bar chart: Balance structure comparison (Total Debt vs Cash vs Net Equity)
    balance = pd.DataFrame(
        {
            "Componente": ["Dívida total", "Caixa disponível", "Patrimônio líquido"],
            "Valor": [
                latest.divida_total.median(),
                latest.caixa.median(),
                latest.patrimonio_liquido.median(),
            ],
        }
    )
    balance_fig = px.bar(
        balance,
        x="Componente",
        y="Valor",
        title=f"Estrutura financeira · Ano {latest_year}",
        color="Componente",
        color_discrete_map={
            "Dívida total": "#501839",
            "Caixa disponível": "#55a9e8",
            "Patrimônio líquido": "#7a4b69",
        },
    )
    balance_fig.update_layout(showlegend=False)

    # --------------------------------------------------------------------------
    # 8. TERMINAL CONCESSION LIQUIDATION SECTION (YEAR 12)
    # --------------------------------------------------------------------------
    terminal = filtered[filtered.encerramento]
    terminal_children = []
    if not terminal.empty:
        terminal_tiles = [
            card(label, money(terminal[key].median()))
            for label, key in [
                ("Caixa inicial", "saldo_inicial_caixa"),
                ("Geração de caixa", "geracao_caixa"),
                ("Investimentos", "investimentos"),
                ("Distribuição ao acionista", "distribuicao_acionista"),
                ("Caixa final", "saldo_final_caixa"),
            ]
        ]
        terminal_children = [
            section(
                "Liquidação contratual",
                "Ano 12 · encerramento planejado separado da operação recorrente.",
                [
                    html.Div(terminal_tiles, className="metrics-grid"),
                    html.P(
                        "Saldos liquidados não entram nas tendências operacionais. A base não detalha a destinação contratual de cada ativo.",
                        className="notice",
                    ),
                ],
            )
        ]

    # --------------------------------------------------------------------------
    # 9. SCENARIO DISTRIBUTION BOXPLOT
    # --------------------------------------------------------------------------
    distribution = px.box(
        operating,
        x="ano_calendario",
        y=selected_metric,
        points=False,
        title=f"Distribuição dos cenários · {METRIC_LABELS[selected_metric]}",
        labels={
            "ano_calendario": "Ano calendário",
            selected_metric: METRIC_LABELS[selected_metric],
        },
        color_discrete_sequence=[COLORS["plum"]],
    )
    if selected_metric in {"margem_ebitda", "roa", "roe", "composicao_endividamento"}:
        distribution.update_yaxes(tickformat=".0%")

    # Subtitle with non-breaking spaces before separators
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
    # View A: Technical / Controllership
    if perspective == "tecnica":
        return page(
            index_fig,
            subtitle,
            [
                section(
                    "Saúde financeira e controles",
                    "Cobertura de curto prazo, estrutura de capital e retorno sobre o ativo.",
                    [html.Div(tiles2, className="metrics-grid")],
                ),
                section(
                    "Leituras para controle",
                    "Interpretações calculadas a partir da mediana e da distribuição dos cenários selecionados.",
                    [html.Div(technical_insights, className="insights-grid")],
                ),
                section(
                    "Risco financeiro",
                    "Probabilidade empírica de eventos de liquidez, resultado e criação de valor.",
                    [chart(risk_fig)],
                ),
                section(
                    "Distribuição de cenários",
                    "Dispersão do indicador financeiro selecionado por ano.",
                    [chart(distribution)],
                ),
            ],
        )

    # View B: Investors / Shareholders
    if perspective == "investidores":
        investor_tiles = [
            card("EBITDA", money(latest.ebitda.median()), delta("ebitda")),
            card(
                "Resultado líquido",
                money(latest.resultado_liquido.median()),
                delta("resultado_liquido"),
            ),
            card(
                "Geração de caixa",
                money(latest.geracao_caixa.median()),
                delta("geracao_caixa"),
            ),
            card("ROE", percent(latest.roe.median()), delta("roe")),
            card("EVA", money(latest.eva.median()), delta("eva")),
        ]
        return page(
            index_fig,
            subtitle,
            [
                section(
                    "Retorno ao investidor",
                    "Resultado, caixa e criação de valor no último ano do recorte.",
                    [html.Div(investor_tiles, className="metrics-grid")],
                ),
                section(
                    "Leituras para decisão de investimento",
                    "O retorno é apresentado com sua incerteza; os textos acompanham o recorte de anos e cenários aplicado.",
                    [html.Div(investor_insights, className="insights-grid")],
                ),
                section(
                    "Valor e potencial de retorno",
                    "Relação entre rentabilidade, criação de valor, caixa e estrutura de capital.",
                    [
                        html.Div(
                            [chart(scatter), chart(value_fig), chart(balance_fig)],
                            className="chart-grid",
                        )
                    ],
                ),
                *terminal_children,
                section(
                    "Distribuição de cenários",
                    "Amplitude dos retornos e indicadores observados nos cenários selecionados.",
                    [chart(distribution)],
                ),
            ],
        )

    # View C: Management / Executive (Default fallback)
    return page(
        index_fig,
        subtitle,
        [
            section(
                "Resumo operacional",
                "Receita, resultado e caixa no último ano do recorte.",
                [html.Div(tiles1, className="metrics-grid")],
            ),
            section(
                "Leituras para gestão",
                "Sinais que conectam desempenho, margem e risco de execução no recorte selecionado.",
                [html.Div(management_insights, className="insights-grid")],
            ),
            section(
                "Acompanhamento da operação",
                "Evolução de receita, EBITDA e riscos que exigem ação de gestão.",
                [
                    html.Div(
                        [chart(trend), chart(value_fig), chart(risk_fig)],
                        className="chart-grid",
                    )
                ],
            ),
            *terminal_children,
            section(
                "Distribuição de cenários",
                "Dispersão do indicador operacional selecionado por ano.",
                [chart(distribution)],
            ),
        ],
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
    """Master callback: Re-render the main dashboard whenever any filter is adjusted.

    Includes top-level exception handling so errors produce a visible notice in the UI
    rather than crashing the client or leaving an unresponsive blank screen.
    """
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
