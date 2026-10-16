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

# ==============================================================================
# DESIGN SYSTEM TOKENS (TYPOGRAPHY & PALETTE)
# ==============================================================================
# System font stack prioritizing native OS rendering for clean modern typography
FONT_STACK = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'

# Semantic color palette used across charts, badges, and indicator cards:
# - ink: Primary text, axis lines, titles
# - teal / sky: Positive trends, revenue, available cash, liquid assets
# - plum / amber / red: Deep accents, EBITDA, equity, risk highlights, debt
COLORS = {
    "ink": "#111111",
    "teal": "#55a9e8",
    "blue": "#55a9e8",
    "amber": "#501839",
    "red": "#501839",
    "plum": "#501839",
    "sky": "#55a9e8",
}


# ==============================================================================
# DATA INGESTION & FINANCIAL KPI ENGINE
# ==============================================================================
def load_data(path: Path) -> pd.DataFrame:
    """Load, cleanse, pivot, and calculate financial indicators from raw CSV ledger.

    Parameters:
        path (Path): Path to the processed CTI CSV data file.

    Returns:
        pd.DataFrame: Wide-format dataframe containing all original accounts plus
                      derived financial ratios, indices, and calendar dimensions.

    Processing Steps:
        1. Reads Brazilian CSV formatting (semicolon delimiter, comma decimal).
        2. Pivots accounting accounts ('Conta') into individual columns per Year and Scenario.
        3. Normalizes Portuguese column names to allow accent-insensitive lookups.
        4. Calculates DRE (Income Statement), BAL (Balance Sheet), and FLU (Cash Flow) KPIs.
        5. Computes liquidity, debt structure, profitability, and EVA metrics.
        6. Sets ratios to NaN for Year 12 (terminal liquidation year).
    """
    # Read the CSV with Brazilian locale formatting:
    # - sep=";": Semicolon separates columns
    # - decimal=",": Comma is used as the decimal mark (e.g. 10,50)
    # - thousands=".": Dot is used as thousands separator (e.g. 1.000.000)
    # - encoding="latin-1": Handles Portuguese accented characters (é, ã, ç, etc.)
    raw = pd.read_csv(path, sep=";", encoding="latin-1", decimal=",", thousands=".")

    # Standardize column naming
    raw = raw.rename(columns={"Cenario": "Cenário"})

    # Strip excess whitespace inside account names for cleaner matching
    raw["Conta"] = raw["Conta"].str.replace(r"\s+", " ", regex=True).str.strip()

    # PIVOT OPERATION:
    # The original file is in long format (each row is a single account value).
    # We pivot so that each unique (Ano, Cenário) is a single row, and each
    # financial account ('Conta') becomes a distinct column.
    wide = (
        raw.dropna(subset=["Conta"])
        .pivot_table(
            index=["Ano", "Cenário"], columns="Conta", values="Valor", aggfunc="first"
        )
        .reset_index()
    )

    # FEATURE ENGINEERING: CONCESSION TIMELINE
    # Extract the numeric year (e.g. "Ano 1" -> 1, "Ano 12" -> 12)
    wide["ano_num"] = wide["Ano"].str.extract(r"(\d+)").astype(int)

    # Map concession year to actual calendar year:
    # Concession starts in 2027 (Ano 1 = 1 + 2026 = 2027, Ano 12 = 12 + 2026 = 2038)
    wide["ano_calendario"] = wide["ano_num"] + 2026

    # Flag Year 12 as the contractual termination/handback year
    wide["encerramento"] = wide["ano_num"].eq(12)

    # ACCENT-INSENSITIVE COLUMN RESOLVER
    # Portuguese accounting labels often vary between sources (e.g., "Patrimônio Líquido" vs
    # "Patrimonio Liquido" or with/without hyphens). This helper performs NFD Unicode
    # normalization to safely locate the matching column regardless of accents or spacing.
    def col(name):
        def normalize(value):
            value = str(value).replace(" - ", " ")
            return "".join(
                c
                for c in unicodedata.normalize("NFD", value)
                if unicodedata.category(c) != "Mn"
            )

        found = [c for c in wide.columns if normalize(c) == normalize(name)]
        if not found:
            raise KeyError(f"Conta não encontrada: {name}")
        return wide[found[0]]

    # --------------------------------------------------------------------------
    # 1. EXTRACT RAW BASE ACCOUNTS (BALANÇO & DRE)
    # --------------------------------------------------------------------------
    receita, ac, pc = (
        col("DRE Receita"),               # Gross Revenue
        col("BAL Ativo Circulante"),      # Current Assets (short-term)
        col("BAL Passivo Circulante"),    # Current Liabilities (short-term)
    )
    pl, ativo, caixa = (
        col("BAL Patrimônio Líquido"),    # Shareholders' Equity
        col("BAL Total do Ativo"),        # Total Assets
        col("BAL Disponível"),            # Cash and Cash Equivalents
    )
    estoque, rlp, permanente = (
        col("BAL Estoques Diversos"),            # Inventory
        col("BAL Realizável a Longo Prazo"),     # Long-Term Receivables / Non-current Assets
        col("BAL Permanente"),                   # Fixed / Permanent Assets (PPE)
    )

    # Total Debt Calculation: Current Liabilities + Other Debts + Loans + Contingency Provisions
    divida = pd.concat(
        [
            pc,
            col("BAL Outros deb"),
            col("BAL Emprést"),
            col("BAL Prov para Contingências"),
        ],
        axis=1,
    ).sum(axis=1)

    # --------------------------------------------------------------------------
    # 2. DRE METRICS (INCOME STATEMENT)
    # --------------------------------------------------------------------------
    wide["receita"] = receita
    wide["custos_variaveis"] = col("DRE Custos").abs()
    wide["ebitda"] = col("DRE EBITDA")
    wide["resultado_operacional"] = col("DRE Resultado Operacional")  # EBIT
    wide["resultado_liquido"] = col("DRE Resultado Líquido")          # Net Profit/Loss

    # Margins: operational efficiency relative to gross revenue
    wide["margem_ebitda"] = wide.ebitda.div(receita)
    wide["margem_liquida"] = wide.resultado_liquido.div(receita)

    # --------------------------------------------------------------------------
    # 3. PROFITABILITY & RETURN RATIOS
    # --------------------------------------------------------------------------
    # ROA (Return on Assets): Net Profit / Total Assets
    wide["roa"] = wide.resultado_liquido.div(ativo)

    # ROE (Return on Equity): Net Profit / Shareholders' Equity
    wide["roe"] = wide.resultado_liquido.div(pl.abs())

    # --------------------------------------------------------------------------
    # 4. LIQUIDITY INDICATORS (SHORT-TERM SOLVENCY)
    # --------------------------------------------------------------------------
    # Current Liquidity: Current Assets / Current Liabilities (> 1.0 indicates safety)
    wide["liquidez_corrente"] = ac.div(pc).abs()

    # Quick Liquidity: (Current Assets - Inventory) / Current Liabilities
    wide["liquidez_seca"] = (ac - estoque).div(pc).abs()

    # Immediate Liquidity: Cash / Current Liabilities (instant coverage)
    wide["liquidez_imediata"] = caixa.div(pc).abs()

    # General Liquidity: (Current Assets + Long-Term Receivables) / Total Debt
    wide["liquidez_geral"] = (ac + rlp).div(divida).abs()

    # --------------------------------------------------------------------------
    # 5. CAPITAL STRUCTURE & INDEBTEDNESS
    # --------------------------------------------------------------------------
    # Debt-to-Equity Ratio: Total Debt / Equity
    wide["participacao_capital_terceiros"] = divida.div(pl).abs()

    # Debt Composition: Share of total debt maturing in the short term (PC / Debt)
    wide["composicao_endividamento"] = pc.div(divida).abs()

    # Fixed Assets to Equity: (RLP + Permanent Assets) / Equity
    wide["imobilizacao_pl"] = (rlp + permanente).div(pl).abs()

    # Absolute Balances
    wide["divida_total"] = divida.abs()
    wide["ativo_total"], wide["patrimonio_liquido"], wide["caixa"] = ativo, pl, caixa

    # --------------------------------------------------------------------------
    # 6. CASH FLOW STATEMENT (FLU)
    # --------------------------------------------------------------------------
    wide["geracao_caixa"] = col("FLU Geração de Caixa")                  # Operating Cash Flow
    wide["investimentos"] = col("FLU Investimentos")                      # Capex / Investments
    wide["distribuicao_acionista"] = col("FLU Distribuição para Acionista") # Dividends / Equity returns
    wide["saldo_inicial_caixa"] = col("FLU Saldo Inicial")                # Beginning cash balance
    wide["saldo_final_caixa"] = col("FLU Saldo Final")                    # Ending cash balance

    # --------------------------------------------------------------------------
    # 7. ECONOMIC VALUE ADDED (EVA)
    # --------------------------------------------------------------------------
    # Formula: NOPAT - (Invested Capital * Cost of Capital)
    # - resultado_operacional * 0.66: Net Operating Profit After Tax (assuming 34% corporate tax)
    # - (ativo - pc): Invested Capital (Total Assets minus Non-interest Bearing Current Liabilities)
    # - 0.10: 10% Weighted Average Cost of Capital (WACC) hurdle rate
    wide["eva"] = wide.resultado_operacional * 0.66 - (ativo - pc) * 0.10

    # --------------------------------------------------------------------------
    # 8. TERMINAL YEAR ADJUSTMENTS
    # --------------------------------------------------------------------------
    # In Year 12 (concession handback/liquidation), traditional financial ratios
    # are distorted by contractual asset transfers. We mask them as NaN so they
    # do not skew ongoing operational trends.
    ratios = [
        "roa",
        "roe",
        "liquidez_corrente",
        "liquidez_seca",
        "liquidez_imediata",
        "liquidez_geral",
        "participacao_capital_terceiros",
        "composicao_endividamento",
        "imobilizacao_pl",
    ]
    wide.loc[wide.encerramento, ratios] = float("nan")
    return wide


# ==============================================================================
# GLOBAL METAMODEL & UI CONFIGURATION LOOKUPS
# ==============================================================================
# Load data once at startup (singleton pattern in memory)
DATA = load_data(DATA_PATH)

# Unique concession years (1 to 12) and simulated Monte Carlo scenarios
YEARS = sorted(DATA.ano_num.unique())
SCENARIOS = sorted(DATA["Cenário"].dropna().unique())

# Human-readable labels for metric keys (used in dropdowns, tooltips, and axis titles)
METRIC_LABELS = {
    "margem_ebitda": "Margem EBITDA",
    "roa": "ROA",
    "roe": "ROE",
    "liquidez_corrente": "Liquidez corrente",
    "liquidez_seca": "Liquidez seca",
    "liquidez_imediata": "Liquidez imediata",
    "liquidez_geral": "Liquidez geral",
    "participacao_capital_terceiros": "Participação de capital de terceiros",
    "composicao_endividamento": "Composição do endividamento",
    "imobilizacao_pl": "Imobilização do PL",
    "eva": "EVA",
}

# The three executive perspectives tailored for different stakeholder groups
PERSPECTIVES = {
    "tecnica": "Técnica",           # Controllership, Treasury, Risk & Compliance
    "gestao": "Gestão",             # Executive Committee, Operations, C-Level
    "investidores": "Investidores", # Shareholders, Board of Directors, Lenders
}

# Explanatory subtitles shown beneath the perspective selector in the sidebar
PERSPECTIVE_SUMMARIES = {
    "tecnica": "Liquidez, endividamento e os controles que sustentam a operação.",
    "gestao": "Receita, margem e os riscos que exigem decisão no próximo ciclo.",
    "investidores": "Retorno, criação de valor e a dispersão entre cenários.",
}

# Defines which metrics are available in the distribution dropdown for each perspective
PERSPECTIVE_METRICS = {
    "tecnica": [
        "liquidez_corrente",
        "liquidez_seca",
        "liquidez_imediata",
        "liquidez_geral",
        "participacao_capital_terceiros",
        "composicao_endividamento",
        "imobilizacao_pl",
    ],
    "gestao": ["margem_ebitda", "liquidez_corrente", "roa", "eva"],
    "investidores": ["margem_ebitda", "roa", "roe", "eva"],
}

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
# REUSABLE UI COMPONENT BUILDERS
# ==============================================================================
def row(label, control, readout=None):
    """Build a standard two-column control row for the sidebar.

    Parameters:
        label (str): Title of the control (e.g. "Anos da concessão").
        control (dash component): Interactive input (e.g. Slider or Dropdown).
        readout (dash component, optional): Dynamic badge displaying the current value.

    Returns:
        html.Div: Styled row element containing label on left, control on right.
    """
    right = [html.Div(control, className="row-control")]
    if readout is not None:
        right.append(readout)
    return html.Div(
        [
            html.Span(label, className="row-label"),
            html.Div(right, className="row-right"),
        ],
        className="row",
    )


def panel(title, children, open_by_default=True):
    """Build a collapsible HTML5 <details> panel for sidebar grouping.

    Parameters:
        title (str): Header text displayed on the clickable summary.
        children (list): Inner Dash components inside the panel body.
        open_by_default (bool): Whether the accordion is initially expanded.
    """
    return html.Details(
        [html.Summary(title), html.Div(children, className="panel-body")],
        open=open_by_default,
        className="panel",
    )


def money(value):
    """Format numeric values into Brazilian Real (R$) with magnitude suffix.

    Values >= 1 billion format as 'R$ X,XX bi'.
    Values < 1 billion format as 'R$ X,XX mi'.
    Handles commas/dots per pt-BR standards. Missing values return '—'.
    """
    if pd.isna(value):
        return "—"
    scale, suffix = (1e9, "bi") if abs(value) >= 1e9 else (1e6, "mi")
    return (
        f"R$ {value/scale:,.2f} {suffix}".replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def percent(value):
    """Format decimal floats (e.g. 0.154) as percentage strings ('15,4%')."""
    return "—" if pd.isna(value) else f"{value:.1%}".replace(".", ",")


def ratio(value):
    """Format coverage multiples (e.g. 1.76 -> '1,76x') using pt-BR comma decimal."""
    return "—" if pd.isna(value) else f"{value:.2f}x".replace(".", ",")


def card(label, value, delta=None):
    """Build a high-level KPI card with metric label, value, and optional variation.

    Parameters:
        label (str): Name of the indicator (e.g. "Receita").
        value (str): Formatted primary metric value (e.g. "R$ 450,20 mi").
        delta (float, optional): Variation against previous period. Automatically
                                 detects if delta is a rate (< 1, formatted in p.p.)
                                 or currency (>= 1, formatted via money()).
    """
    children = [
        html.Div(label, className="metric-label"),
        html.Div(value, className="metric-value"),
    ]
    if delta is not None and not pd.isna(delta):
        children.append(
            html.Div(
                (
                    # Ratios and percentages are < 1, so magnitude determines whether
                    # to show percentage points (p.p.) or currency (R$).
                    f"Variação: {f'{delta * 100:+.1f}'.replace('.', ',')} p.p."
                    if abs(delta) < 1
                    else f"Variação: {money(delta)}"
                ),
                className="metric-delta",
            )
        )
    return html.Div(children, className="metric-card")


def insight(title, text, tone="neutral"):
    """Build an analytical narrative insight card with semantic tone styling.

    Parameters:
        title (str): Bold summary heading of the observation.
        text (str): Explanatory analysis explaining business implications.
        tone (str): Styling class modifier ('neutral', 'alert', or 'positive').
    """
    return html.Div(
        [html.H3(title), html.P(text)], className=f"insight-card insight-{tone}"
    )


def section(title, subtitle, children):
    """Build a semantic content section with header and responsive content container."""
    return html.Section(
        [
            html.Div([html.H2(title), html.P(subtitle, className="section-subtitle")]),
            *children,
        ],
        className="section",
    )


def chart(figure, class_name="chart-card"):
    """Apply unified styling tokens to a Plotly figure and wrap in a responsive card.

    Standardizes fonts, transparent plot/paper backgrounds, gridlines, and margins.
    Hides the Plotly floating modebar for a clean embedded appearance.
    """
    figure.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": FONT_STACK, "color": COLORS["ink"], "size": 12},
        title_font={"size": 15, "color": COLORS["ink"]},
        margin={"l": 48, "r": 20, "t": 56, "b": 44},
        legend_title_text="",
        legend={"font": {"size": 12}},
        hoverlabel={"font": {"family": FONT_STACK, "size": 12}},
    )
    figure.update_xaxes(gridcolor="#eeeeee", linecolor="#cfcfcf", zeroline=False)
    figure.update_yaxes(gridcolor="#eeeeee", linecolor="#cfcfcf", zeroline=False)
    return html.Div(
        dcc.Graph(figure=figure, config={"displayModeBar": False}, responsive=True),
        className=class_name,
    )


# ==============================================================================
# RADIAL PETAL VISUALIZATION (CUSTOM POLAR SCATTER CHART)
# ==============================================================================
# Sizing parameters for the central hole and spacing between individual metric petals
HOLE = 0.34
PETAL_GAP = 0.30  # Fraction of angular slice left empty so petals appear as distinct shapes


def radial_figure(scored_labels):
    """Build the hero radial petal chart showing normalized relative KPI scores.

    Parameters:
        scored_labels (list of tuple): List of (label_str, score_float_0_to_100).

    Returns:
        go.Figure: Plotly polar figure where each indicator is traced as a smooth
                   rounded petal with Bezier corners (via petals.py).
    """
    figure = go.Figure()
    slice_deg = 360 / len(scored_labels)
    inner = 100 * HOLE / (1 - HOLE)

    for index, (label, score) in enumerate(scored_labels):
        # Calculate closed geometric boundary path for the rounded petal
        theta, radius = petal(
            center_deg=index * slice_deg,
            width_deg=slice_deg * (1 - PETAL_GAP),
            inner=inner,
            outer=inner + score * (100 - inner) / 100,
            corner=14,
        )
        figure.add_trace(
            go.Scatterpolar(
                theta=theta,
                r=radius,
                mode="lines",
                fill="toself",
                fillcolor=COLORS["plum"],
                line={"width": 0},
                hoveron="fills",
                text=f"{label}<br>Índice relativo {score:.0f}/100",
                hoverinfo="text",
            )
        )

    figure.update_layout(
        showlegend=False,
        margin={"l": 80, "r": 80, "t": 56, "b": 56},
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": FONT_STACK},
        hoverlabel={
            "bgcolor": COLORS["plum"],
            "bordercolor": COLORS["plum"],
            "font": {"color": "#ffffff", "size": 13, "family": FONT_STACK},
        },
        polar={
            "hole": HOLE,
            "bgcolor": "rgba(0,0,0,0)",
            "radialaxis": {
                # Range 0-118 provides visual headroom past 100 so outer labels clear petals
                "range": [0, 118],
                "showticklabels": False,
                "showline": False,
                "griddash": "dot",
                "gridcolor": "rgba(80,24,57,.40)",
                "gridwidth": 1,
                "tickvals": [25, 50, 75, 100],
            },
            "angularaxis": {
                "rotation": 90,
                "direction": "clockwise",
                "showline": False,
                "griddash": "dot",
                "gridcolor": "rgba(80,24,57,.40)",
                "gridwidth": 1,
                "linecolor": "rgba(80,24,57,.40)",
                "tickmode": "array",
                "tickvals": [i * slice_deg for i in range(len(scored_labels))],
                "ticktext": [
                    f"<span style='font-size:17px'>{score:.0f}</span><br>{label}"
                    for label, score in scored_labels
                ],
                "tickfont": {"color": COLORS["plum"], "size": 12},
            },
        },
    )
    return figure


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
    tiles1 = [
        card("Receita", money(latest.receita.median()), delta("receita")),
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
        card(
            "Dívida total", money(latest.divida_total.median()), delta("divida_total")
        ),
    ]

    # Technical controls & liquidity tiles (Margins, ROA, ROE, Current & General Liquidity)
    tiles2 = [
        card(
            "Margem EBITDA",
            percent(latest.margem_ebitda.median()),
            delta("margem_ebitda"),
        ),
        card("ROA", percent(latest.roa.median()), delta("roa")),
        card("ROE", percent(latest.roe.median()), delta("roe")),
        card("Liquidez corrente", ratio(latest.liquidez_corrente.median())),
        card("Liquidez geral", ratio(latest.liquidez_geral.median())),
    ]

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
