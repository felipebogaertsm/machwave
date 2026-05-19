from collections.abc import Sequence

import numpy as np
from scipy.interpolate import CubicSpline


class BoundedCubicSpline:
    """Cubic spline interpolant that does not extrapolate outside its domain."""

    def __init__(
        self,
        x_points: Sequence[float],
        y_points: Sequence[float],
    ) -> None:
        """Construct the spline from a table of knots.

        Args:
            x_points: Strictly increasing knot locations along the independent
                axis. Must contain at least two entries.
            y_points: Dependent values at each knot. Must have the same length
                as `x_points`.

        Raises:
            ValueError: If the inputs are not one-dimensional sequences of
                equal length, if fewer than two knots are supplied, or if
                `x_points` is not strictly increasing.
        """
        x_array = np.asarray(x_points, dtype=float)
        y_array = np.asarray(y_points, dtype=float)

        if x_array.ndim != 1 or y_array.ndim != 1 or x_array.shape != y_array.shape:
            raise ValueError(
                "x_points and y_points must be one-dimensional sequences of equal length"
            )
        if x_array.size < 2:
            raise ValueError("BoundedCubicSpline needs at least two knots")
        if not np.all(np.diff(x_array) > 0):
            raise ValueError("x_points must be strictly increasing")

        self._spline = CubicSpline(x_array, y_array, extrapolate=False)
        self._domain_minimum = float(x_array[0])
        self._domain_maximum = float(x_array[-1])

    @property
    def domain(self) -> tuple[float, float]:
        """Return the inclusive `(minimum, maximum)` bounds of the spline."""
        return (self._domain_minimum, self._domain_maximum)

    def __call__(self, value: float) -> float:
        """Return the interpolated value at `value`.

        Args:
            value: Independent-axis input at which to evaluate the spline.

        Returns:
            Interpolated dependent value.

        Raises:
            ValueError: If `value` is outside the inclusive `domain`.
        """
        if value < self._domain_minimum or value > self._domain_maximum:
            raise ValueError(
                f"input {value} is outside "
                f"[{self._domain_minimum}, {self._domain_maximum}]"
            )
        return float(self._spline(value))
