# core.interpolation

Generic interpolation utilities for tabulated curves used across machwave.

## `BoundedCubicSpline`

Wraps a table of knots in a cubic spline built on [`scipy.interpolate.CubicSpline`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.CubicSpline.html) with `extrapolate=False`, raising `ValueError` for any input outside `[x_points[0], x_points[-1]]`.

The constructor rejects malformed tables eagerly: the two sequences must be one-dimensional, the same length, contain at least two knots, and `x_points` must be strictly increasing. The inclusive domain bounds are exposed via the `domain` property.

### Example

```python
from machwave.core.interpolation import BoundedCubicSpline

efficiency_curve = BoundedCubicSpline(
    x_points=[0.5, 1.0, 1.5, 2.0],
    y_points=[0.55, 0.65, 0.62, 0.50],
)

efficiency_curve.domain   # → (0.5, 2.0)
efficiency_curve(1.2)     # → smooth spline value
efficiency_curve(3.0)     # raises ValueError — outside [0.5, 2.0]
```

---

::: machwave.core.interpolation
