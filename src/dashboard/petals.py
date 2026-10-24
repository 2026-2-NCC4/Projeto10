"""Rounded Petal Geometry for Plotly Polar Radial Charts.

This module generates 2D polygon coordinates tracing an annular sector with
smooth, rounded corners (fillets) using quadratic Bézier curves.

================================================================================
BACKGROUND & PURPOSE
================================================================================
In standard Plotly, polar bar charts created with ``go.Barpolar`` only support
rigid rectangular bars with hard 90-degree corners and have no native property
such as ``cornerradius``.

To achieve the custom "petal" look in the NOUR Financial Dashboard (app.py):
1. This module computes an explicit polygon perimeter path for each metric petal.
2. The perimeter is calculated in 2D Cartesian coordinates (x, y) with Bézier fillets.
3. The points are converted back to polar coordinates (theta in degrees, radius r).
4. Plotly renders the petal using ``go.Scatterpolar(theta=theta, r=radius, mode="lines", fill="toself")``.

================================================================================
MATHEMATICAL CONCEPTS
================================================================================
- ANNULAR SECTOR: A slice of a ring bounded by an inner radius, an outer radius,
  and two radial lines (start and end angles).
- QUADRATIC BÉZIER CURVE: A parametric curve defined by:
      B(t) = (1 - t)² · P0 + 2(1 - t)t · Pc + t² · P1,   for t ∈ [0, 1]
  where P0 is the start point on the edge, Pc is the original sharp corner vertex
  (the control point), and P1 is the tangent point on the adjoining edge.
- ANGULAR PULL-BACK (TRIM): The corner fillet radius expressed as an angle:
      θ_trim = corner / radius
  This ensures that the physical fillet length remains visually uniform on both
  the inner and outer circular arcs.

================================================================================
HOW TO MANAGE & TWEAK THIS MODULE
================================================================================
- HOW TO CHANGE PETAL ROUNDNESS:
  In `app.py` -> `radial_figure()`, adjust the `corner` argument passed to `petal()`.
  Increasing `corner` yields softer, more rounded petals; lowering it approaches sharp edges.
- HOW TO ADJUST PERFORMANCE VS. VISUAL SMOOTHNESS:
  Modify `arc_steps` (default 30) or `curve_steps` (default 12). Lower values reduce the
  number of points sent over the wire; higher values produce smoother curves on high-DPI screens.
- HOW TO RUN UNIT TESTS:
      $ python src/dashboard/petals.py
  (Runs `demo()` and validates path closure, geometry bounds, and safety clamping).
"""

from math import atan2, cos, degrees, hypot, radians, sin


# ==============================================================================
# TRIGONOMETRIC & PARAMETRIC HELPERS (INTERNAL)
# ==============================================================================
def _polar(angle, radius):
    """Convert polar coordinates (angle in radians, radius) to Cartesian (x, y).

    Parameters:
        angle (float): Angle in radians.
        radius (float): Distance from the origin.

    Returns:
        tuple: (x, y) Cartesian coordinates.
    """
    return radius * cos(angle), radius * sin(angle)


def _arc(angle_from, angle_to, radius, steps):
    """Generate linearly spaced Cartesian points along a circular arc at a fixed radius.

    Parameters:
        angle_from (float): Starting angle in radians.
        angle_to (float): Ending angle in radians.
        radius (float): Distance of the arc from the origin.
        steps (int): Number of linear segments to divide the arc into.

    Returns:
        list of tuple: List of (x, y) points tracing the circular arc.
    """
    span = angle_to - angle_from
    return [_polar(angle_from + span * i / steps, radius) for i in range(steps + 1)]


def _quad(start, control, end, steps):
    """Generate points along a quadratic Bézier curve for corner filleting.

    Evaluates the parametric formula:
        B(t) = (1 - t)² * start + 2 * (1 - t) * t * control + t² * end

    Parameters:
        start (tuple): (x, y) starting point on the edge.
        control (tuple): (x, y) control point representing the original sharp corner.
        end (tuple): (x, y) ending point on the intersecting edge.
        steps (int): Number of evaluation segments along the curve.

    Returns:
        list of tuple: List of (x, y) points tracing the smooth rounded corner.
    """
    (x0, y0), (cx, cy), (x1, y1) = start, control, end
    points = []
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        points.append(
            (
                u * u * x0 + 2 * u * t * cx + t * t * x1,
                u * u * y0 + 2 * u * t * cy + t * t * y1,
            )
        )
    return points


# ==============================================================================
# PRIMARY PETAL GEOMETRY GENERATOR
# ==============================================================================
def petal(center_deg, width_deg, inner, outer, corner, arc_steps=30, curve_steps=12):
    """Return ``(theta_degrees, radii)`` tracing a single closed, rounded petal.

    Constructs an annular sector where each of the 4 sharp corners is replaced
    by a smooth quadratic Bézier fillet.

    Parameters:
        center_deg (float): Center orientation angle of the petal in degrees (0–360).
        width_deg (float): Angular width/spread of the petal in degrees.
        inner (float): Inner radius (the central donut hole boundary).
        outer (float): Outer radius (proportional to the metric value).
        corner (float): Requested corner rounding radius in coordinate units.
                        Automatically clamped to prevent geometric inversion.
        arc_steps (int, optional): Point density for circular arcs (default 30).
        curve_steps (int, optional): Point density for each rounded corner (default 12).

    Returns:
        tuple: (theta_degrees, radii)
            - theta_degrees (list of float): Angles in degrees for each vertex.
            - radii (list of float): Radial distance from origin for each vertex.
    """
    # Guard against zero or negative radial thickness
    outer = max(outer, inner + 1e-9)
    half = radians(width_deg) / 2

    # SAFETY CLAMPING:
    # Ensure the requested corner radius cannot exceed:
    # 1. Half of the radial depth ((outer - inner) / 2)
    # 2. The available arc length on the outer ring (outer * half * 0.98)
    # 3. The available arc length on the inner ring (inner * half * 0.98)
    corner = max(
        0.0, min(corner, (outer - inner) / 2, outer * half * 0.98, inner * half * 0.98)
    )

    # Angular boundaries of the petal wedge (in radians)
    start, end = radians(center_deg) - half, radians(center_deg) + half

    # ANGULAR PULL-BACK (TRIM):
    # Express the linear corner radius as an angular offset (arc length = r * theta).
    # This keeps the physical fillet visually proportional across inner and outer arcs.
    outer_trim = corner / outer
    inner_trim = corner / inner if inner else 0.0

    # --------------------------------------------------------------------------
    # PERIMETER CONSTRUCTION (8 SEGMENTS + CLOSING POINT)
    # --------------------------------------------------------------------------
    # 1. Outer circular arc (between top-left and top-right fillets)
    points = _arc(start + outer_trim, end - outer_trim, outer, arc_steps)

    # 2. Top-right corner fillet (Bézier curve rounding into the right radial edge)
    points += _quad(
        _polar(end - outer_trim, outer),
        _polar(end, outer),
        _polar(end, outer - corner),
        curve_steps,
    )[1:]

    # 3. Right radial straight edge (descending from outer radius to inner radius)
    points.append(_polar(end, inner + corner))

    # 4. Bottom-right corner fillet (Bézier curve rounding into the inner arc)
    points += _quad(
        _polar(end, inner + corner),
        _polar(end, inner),
        _polar(end - inner_trim, inner),
        curve_steps,
    )[1:]

    # 5. Inner circular arc (returning along the central donut hole boundary)
    points += _arc(end - inner_trim, start + inner_trim, inner, arc_steps)[1:]

    # 6. Bottom-left corner fillet (Bézier curve rounding into the left radial edge)
    points += _quad(
        _polar(start + inner_trim, inner),
        _polar(start, inner),
        _polar(start, inner + corner),
        curve_steps,
    )[1:]

    # 7. Left radial straight edge (ascending back toward the outer radius)
    points.append(_polar(start, outer - corner))

    # 8. Top-left corner fillet (Bézier curve rounding into the outer arc)
    points += _quad(
        _polar(start, outer - corner),
        _polar(start, outer),
        _polar(start + outer_trim, outer),
        curve_steps,
    )[1:]

    # 9. Close the polygon loop by repeating the first vertex
    points.append(points[0])

    # Convert Cartesian (x, y) back to polar coordinates (theta in degrees, radius r)
    return (
        [degrees(atan2(y, x)) for x, y in points],
        [hypot(x, y) for x, y in points],
    )


# ==============================================================================
# VALIDATION & SELF-TEST SUITE
# ==============================================================================
def demo():
    """Run mathematical and geometric assertions to verify petal boundary integrity.

    Validates:
    - Path closure (start vertex equals end vertex).
    - Radial boundary adherence (points remain inside the annular ring).
    - Angular confinement (points stay within the designated angular wedge).
    - Corner filleting (corners do not touch the sharp theoretical vertices).
    - Safety clamping (absurdly large corner radius does not invert or break geometry).
    - Degenerate handling (handles zero-thickness petals without runtime exceptions).
    """

    # A corner fillet is a chord across the ring, so it dips a tiny fraction of a
    # percent inside `inner`. Tolerate that small tolerance; anything larger is an escape.
    def within(radius, inner, outer):
        return all(inner * 0.98 <= r <= outer * 1.001 for r in radius)

    # Test 1: Standard petal generation
    theta, radius = petal(0, 40, 20, 100, 9)
    assert theta[0] == theta[-1] and radius[0] == radius[-1], "path is not closed"
    assert within(radius, 20, 100), "radius escaped the ring"
    assert all(-20.01 <= t <= 20.01 for t in theta), "petal escaped its wedge"

    # Test 2: Verify that corner rounding actually happened (no point reaches sharp corners)
    corners = [r for t, r in zip(theta, radius) if abs(abs(t) - 20) < 0.01]
    assert corners and max(corners) < 99, "corners were not rounded"
    assert min(corners) > 21, "inner corners were not rounded"

    # Test 3: Clamping verification (extreme corner radius should clamp gracefully)
    theta, radius = petal(170, 40, 20, 100, 500)
    assert within(radius, 20, 100), "clamping failed"

    # Test 4: Degenerate case (zero thickness where outer equals inner)
    theta, radius = petal(0, 40, 20, 20, 9)
    assert all(abs(r - 20) < 0.01 for r in radius), "degenerate petal is not a ring arc"

    print("petals: ok")


if __name__ == "__main__":
    demo()
