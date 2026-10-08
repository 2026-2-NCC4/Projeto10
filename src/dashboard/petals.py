"""Rounded petal geometry for the radial chart.

Plotly's ``Barpolar`` draws polar bars with hard corners and has no
``cornerradius``, so each petal is built here as an explicit closed path and
handed to ``Scatterpolar(fill="toself")`` instead.

A petal is an annular sector (outer arc, radial edge, inner arc, radial edge)
with each of its four corners replaced by a quadratic Bezier whose control
point is the original sharp corner.
"""

from math import atan2, cos, degrees, hypot, radians, sin


def _polar(angle, radius):
    return radius * cos(angle), radius * sin(angle)


def _arc(angle_from, angle_to, radius, steps):
    span = angle_to - angle_from
    return [_polar(angle_from + span * i / steps, radius) for i in range(steps + 1)]


def _quad(start, control, end, steps):
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


def petal(center_deg, width_deg, inner, outer, corner, arc_steps=30, curve_steps=12):
    """Return ``(theta_degrees, radii)`` tracing one rounded petal, closed.

    ``corner`` is a requested radius in data units; it is clamped so the
    rounding can never eat past the petal's own edges.
    """
    outer = max(outer, inner + 1e-9)
    half = radians(width_deg) / 2
    corner = max(
        0.0, min(corner, (outer - inner) / 2, outer * half * 0.98, inner * half * 0.98)
    )
    start, end = radians(center_deg) - half, radians(center_deg) + half
    # Angular pull-back is the arc length `corner` expressed as an angle, so the
    # fillet looks the same size on the inner and the outer arc.
    outer_trim = corner / outer
    inner_trim = corner / inner if inner else 0.0

    points = _arc(start + outer_trim, end - outer_trim, outer, arc_steps)
    points += _quad(
        _polar(end - outer_trim, outer),
        _polar(end, outer),
        _polar(end, outer - corner),
        curve_steps,
    )[1:]
    points.append(_polar(end, inner + corner))
    points += _quad(
        _polar(end, inner + corner),
        _polar(end, inner),
        _polar(end - inner_trim, inner),
        curve_steps,
    )[1:]
    points += _arc(end - inner_trim, start + inner_trim, inner, arc_steps)[1:]
    points += _quad(
        _polar(start + inner_trim, inner),
        _polar(start, inner),
        _polar(start, inner + corner),
        curve_steps,
    )[1:]
    points.append(_polar(start, outer - corner))
    points += _quad(
        _polar(start, outer - corner),
        _polar(start, outer),
        _polar(start + outer_trim, outer),
        curve_steps,
    )[1:]
    points.append(points[0])
    return (
        [degrees(atan2(y, x)) for x, y in points],
        [hypot(x, y) for x, y in points],
    )


def demo():
    # A corner fillet is a chord across the ring, so it dips a fraction of a
    # percent inside `inner`. Tolerate that; anything larger is a real escape.
    def within(radius, inner, outer):
        return all(inner * 0.98 <= r <= outer * 1.001 for r in radius)

    theta, radius = petal(0, 40, 20, 100, 9)
    assert theta[0] == theta[-1] and radius[0] == radius[-1], "path is not closed"
    assert within(radius, 20, 100), "radius escaped the ring"
    assert all(-20.01 <= t <= 20.01 for t in theta), "petal escaped its wedge"
    # Rounding happened: nothing reaches the outer radius at the wedge edges.
    corners = [r for t, r in zip(theta, radius) if abs(abs(t) - 20) < 0.01]
    assert corners and max(corners) < 99, "corners were not rounded"
    assert min(corners) > 21, "inner corners were not rounded"

    # Clamping: an absurd corner radius still yields a path inside the ring.
    theta, radius = petal(170, 40, 20, 100, 500)
    assert within(radius, 20, 100), "clamping failed"

    # A petal reaching the hole is degenerate, not an exception.
    theta, radius = petal(0, 40, 20, 20, 9)
    assert all(abs(r - 20) < 0.01 for r in radius), "degenerate petal is not a ring arc"
    print("petals: ok")


if __name__ == "__main__":
    demo()
