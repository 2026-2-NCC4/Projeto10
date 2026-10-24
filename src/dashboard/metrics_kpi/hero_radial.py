import plotly.graph_objects as go
from petals import petal
from config import FONT_STACK, COLORS

# ==============================================================================
# RADIAL PETAL VISUALIZATION (CUSTOM POLAR SCATTER CHART)
# ==============================================================================
# Sizing parameters for the central hole and spacing between individual metric petals
HOLE = 0.34
PETAL_GAP = (
    0.30  # Fraction of angular slice left empty so petals appear as distinct shapes
)


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
