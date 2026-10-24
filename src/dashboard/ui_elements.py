from dash import html, dcc
import pandas as pd
from config import FONT_STACK, COLORS


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


# ----------------------------------------------------------------------
# PAGE LAYOUT HELPER
# ----------------------------------------------------------------------
def page(index_fig, subtitle, sections):
    """Assemble a full dashboard “page".

    Parameters
    ----------
    index_fig : plotly.graph_objects.Figure
        The hero/radial figure to display at the top of the page.
    subtitle : str
        Title text displayed above the hero figure (e.g., "Gestão · Ano 11 (2037) · 1.200 cenários · Mediana do Recorte").
    sections : list[Component]
        List of section components that make up the page content.
    """
    # Hero container: title above the chart, with shared styling
    hero = html.Div(
        [
            html.H2(subtitle, className="hero-title"),
            chart(index_fig, class_name="hero-graph"),
        ],
        className="hero-figure",
    )
    return html.Div(
        [
            hero,
            html.Div(sections, className="page-content"),
        ],
        className="page",
    )
    """Assemble a full dashboard “page".

    Parameters
    ----------
    index_fig : plotly.graph_objects.Figure
        The hero/radial figure to display at the top of the page.
    subtitle : str
        Subtitle text displayed under the hero figure.
    sections : list[Component]
        List of section components that make up the page content.
    """
    # Wrap the Plotly figure in a Graph component with the same styling as other charts
    hero = chart(index_fig, class_name="hero-figure")
    return html.Div(
        [
            hero,
            html.H2(subtitle, className="page-subtitle"),
            html.Div(sections, className="page-content"),
        ],
        className="page",
    )
    """
    Assemble a full dashboard “page”.

    Parameters
    ----------
    index_fig : dash component
        The hero/radial figure shown at the top of the page.
    subtitle : str
        A short description displayed under the hero figure.
    sections : list[dash component]
        The body of the page – typically a list of ``section`` components.

    Returns
    -------
    html.Div
        A container ready to be injected into ``dashboard-content``.
    """
    return html.Div(
        [
            # Hero / radial KPI figure
            html.Div(index_fig, className="hero-figure"),
            # Subtitle text
            html.H2(subtitle, className="page-subtitle"),
            # The actual content sections
            html.Div(sections, className="page-content"),
        ],
        className="page",
    )
