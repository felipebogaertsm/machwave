# core.interpolation

Generic interpolation utilities for tabulated curves used across machwave.

## `BoundedCubicSpline`

Many parts of machwave consume property curves as small tables — pump head versus volumetric flow, burn rate versus pressure, nozzle area versus axial station. `BoundedCubicSpline` wraps such a table in a cubic spline that:

1. **Interpolates between knots with a cubic spline.** Smooth derivatives matter when the curve is composed with downstream solvers (RK4 step, root-finder on injector–chamber balance, etc.).
2. **Refuses to extrapolate.** [`scipy.interpolate.CubicSpline`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.CubicSpline.html) is constructed with `extrapolate=False`, and the class additionally raises `ValueError` for any input outside `[x_points[0], x_points[-1]]`. A simulation that drifts off the calibrated domain fails loudly rather than producing fabricated values.

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
