from dash import html, dcc
from dash_iconify import DashIconify
import pandas as pd
from config import FONT_STACK, COLORS



# ==============================================================================
# REUSABLE UI COMPONENT BUILDERS
# ==============================================================================
def row(
    label,
    control,
    readout=None,
    label_id=None,
    control_id=None,
    dropdown_control=None,
    dropdown_id=None,
    range_id=None,
):
    """Build a standard two-column control row for the sidebar.

    Parameters:
        label (str): Title of the control (e.g. "Anos da concessão").
        control (dash component): Interactive input (e.g. Slider or Dropdown).
        readout (dash component, optional): Dynamic badge displaying the current value.
        label_id (str, optional): ID for the label span component.
        control_id (str, optional): ID for the control wrapper div.
        dropdown_control (dash component, optional): Optional alternate dropdown control.
        dropdown_id (str, optional): ID for the dropdown wrapper div.
        range_id (str, optional): ID for the range controls wrapper div.

    Returns:
        html.Div: Styled row element containing label on left, control on right.
    """
    control_props = {"className": "row-control"}
    if control_id is not None:
        control_props["id"] = control_id
    right = [html.Div(control, **control_props)]
    if readout is not None:
        right.append(readout)

    range_props = {"className": "row-right"}
    if range_id is not None:
        range_props["id"] = range_id

    children = [
        html.Span(
            label,
            **({"id": label_id} if label_id else {"className": "row-label"}),
        ),
        html.Div(right, **range_props),
    ]
    if dropdown_control is not None:
        dropdown_props = {
            "className": "row-dropdown-container",
            "style": {"display": "none"},
        }
        if dropdown_id is not None:
            dropdown_props["id"] = dropdown_id
        children.append(html.Div(dropdown_control, **dropdown_props))

    return html.Div(children, className="row")


def panel(
    title,
    children,
    open_by_default=True,
    id=None,
    style=None,
    className="panel",
    **kwargs,
):
    """Build a collapsible HTML5 <details> panel for sidebar grouping.

    Parameters:
        title (str): Header text displayed on the clickable summary.
        children (list): Inner Dash components inside the panel body.
        open_by_default (bool): Whether the accordion is initially expanded.
        id (str, optional): Unique component ID.
        style (dict, optional): Inline styling.
        className (str, optional): CSS class names.
    """
    props = {
        "open": open_by_default,
        "className": className,
        **kwargs,
    }
    if id is not None:
        props["id"] = id
    if style is not None:
        props["style"] = style
    return html.Details(
        [html.Summary(title), html.Div(children, className="panel-body")],
        **props,
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

def variation_badge(value, suffix="", formatter=None):
    if value is None or pd.isna(value):
        text = "Sem comparação"
        color_class = "badge-neutral"
    else:
        positive = value >= 0
        arrow = "↑" if positive else "↓"
        sign = "+" if positive else "-"

        if formatter == "money":
            formatted = money(abs(value))
            formatted = formatted.replace("R$ ", "")
            text = f"{arrow} {sign}R$ {formatted}"

        else:
            formatted = f"{abs(value):.1f}".replace(".", ",")
            text = f"{arrow} {sign}{formatted} {suffix}".strip()

        color_class = (
            "badge-positive"
            if positive
            else "badge-negative"
        )

    return html.Div(
        text,
        className=f"investor-badge {color_class}",
    )

def card(
    label,
    value,
    delta=None,
    subtitle=None,
    icon=None,
    accent_color=None,
):
    """
    Build a reusable KPI card with label, subtitle, icon, value,
    and optional variation.

    Parameters:
        label (str): Name of the indicator.
        value (str): Formatted primary metric value.
        delta (float, optional): Variation against the previous period.
        subtitle (str, optional): Supporting description below the label.
        icon (str, optional): Iconify icon name.
        accent_color (str, optional): Custom icon color.
    """

    icon_color = accent_color or COLORS.get("plum", "#501839")

    header_children = []

    if icon:
        header_children.append(
            html.Div(
                DashIconify(
                    icon=icon,
                    width=22,
                    height=22,
                    color=icon_color,
                ),
                className="metric-icon",
            )
        )

    text_children = [
        html.Div(label, className="metric-label"),
    ]

    if subtitle:
        text_children.append(
            html.Div(
                subtitle,
                className="metric-subtitle",
            )
        )

    header_children.append(
        html.Div(
            text_children,
            className="metric-heading",
        )
    )

    children = [
        html.Div(
            header_children,
            className="metric-header",
        ),
        html.Div(
            value,
            className="metric-value",
        ),
    ]

    if delta is not None and not pd.isna(delta):
        if abs(delta) < 1:
            children.append(
                variation_badge(
                    delta * 100,
                    suffix="p.p.",
                )
            )
        else:
            children.append(
                variation_badge(
                    delta,
                    formatter="money",
                )
            )
    return html.Div(
        children,
        className="metric-card",
        style={"--metric-accent": icon_color},
    )

def section(title, subtitle, children, footer_desc=None):
    """Build a semantic content section with header and responsive content container."""
    elements = [
        html.Div([html.H2(title), html.P(subtitle, className="section-subtitle")]),
        *children,
    ]

    if footer_desc:
        elements.append(html.P(footer_desc, className="section-description"))

    return html.Section(elements, className="section")


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
        title_font={"size": 15, "color": COLORS["ink"], "weight": "bold"},
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

def insight(title, text, tone="neutral"):
    """Build an analytical insight card with semantic tone styling."""
    return html.Div(
        [
            html.H3(title),
            html.P(text),
        ],
        className=f"insight-card insight-{tone}",
    )


# ----------------------------------------------------------------------
# PAGE LAYOUT HELPER
# ----------------------------------------------------------------------
def page(index_fig, subtitle, sections):
    """Assemble a full dashboard page.

    Parameters
    ----------
    index_fig : plotly.graph_objects.Figure
        The hero/radial figure to display at the top of the page.
    subtitle : str
        Title text displayed above the hero figure (e.g., "Gestão · Ano 11 (2037) · 1.200 cenários · Mediana do Recorte").
    sections : list[Component]
        List of section components that make up the page content.
    """
    # Hero container: title and simplified view toggle above the chart
    hero = html.Div(
        [
            html.Div(
                [
                    html.H2(subtitle, className="hero-title"),
                    html.Div(
                        dcc.Checklist(
                            id="toggle-simplified-view",
                            options=[
                                {
                                    "label": "Visão simplificada",
                                    "value": "simplified",
                                }
                            ],
                            value=[],
                            persistence=True,
                            persistence_type="session",
                            className="simplified-view-toggle",
                        ),
                        className="hero-toggle-container",
                        title="Ocultar subtítulos e descrições dos gráficos para uma visualização simplificada",
                    ),
                ],
                className="hero-header",
            ),
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
