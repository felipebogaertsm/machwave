"""Tests for the bounded cubic-spline interpolant in `machwave.core.interpolation`."""

import math

import pytest

import machwave.core.interpolation as interpolation


def test_bounded_cubic_spline_returns_knot_values_at_knots():
    """At each knot the spline must return the tabulated dependent value."""
    spline = interpolation.BoundedCubicSpline([0.0, 1.0, 2.0], [0.0, 1.0, 4.0])

    assert spline(0.0) == pytest.approx(0.0)
    assert spline(1.0) == pytest.approx(1.0)
    assert spline(2.0) == pytest.approx(4.0)


def test_bounded_cubic_spline_returns_finite_value_at_interior_point():
    """Interpolating between knots must yield a finite floating-point value."""
    spline = interpolation.BoundedCubicSpline([0.0, 1.0, 2.0], [0.0, 1.0, 4.0])

    value = spline(0.5)

    assert isinstance(value, float)
    assert math.isfinite(value)


def test_bounded_cubic_spline_exposes_domain_bounds():
    """The `domain` property must report `(x_min, x_max)` of the input knots."""
    spline = interpolation.BoundedCubicSpline([0.0, 1.0, 2.0], [0.0, 1.0, 4.0])

    assert spline.domain == (0.0, 2.0)


def test_bounded_cubic_spline_rejects_non_strictly_increasing_x_with_duplicate():
    """A repeated x knot must be rejected because the spline is undefined."""
    with pytest.raises(ValueError, match="strictly increasing"):
        interpolation.BoundedCubicSpline([0.0, 1.0, 1.0], [0.0, 1.0, 2.0])


def test_bounded_cubic_spline_rejects_decreasing_x():
    """A decreasing x sequence must be rejected."""
    with pytest.raises(ValueError, match="strictly increasing"):
        interpolation.BoundedCubicSpline([2.0, 1.0, 0.0], [0.0, 1.0, 2.0])


def test_bounded_cubic_spline_rejects_mismatched_lengths():
    """`x_points` and `y_points` must have the same length."""
    with pytest.raises(ValueError, match="equal length"):
        interpolation.BoundedCubicSpline([0.0, 1.0, 2.0], [0.0, 1.0])


def test_bounded_cubic_spline_rejects_fewer_than_two_knots():
    """A single knot is insufficient to define an interpolant."""
    with pytest.raises(ValueError, match="at least two knots"):
        interpolation.BoundedCubicSpline([0.0], [0.0])


def test_bounded_cubic_spline_rejects_two_dimensional_inputs():
    """Inputs must be one-dimensional sequences."""
    with pytest.raises(ValueError, match="one-dimensional"):
        interpolation.BoundedCubicSpline(
            [[0.0, 1.0], [2.0, 3.0]], [[0.0, 1.0], [2.0, 3.0]]
        )


def test_bounded_cubic_spline_accepts_inputs_at_domain_boundaries():
    """Calling exactly at `x_min` and `x_max` must not raise."""
    spline = interpolation.BoundedCubicSpline([0.0, 1.0, 2.0], [0.0, 1.0, 4.0])

    assert spline(0.0) == pytest.approx(0.0)
    assert spline(2.0) == pytest.approx(4.0)


def test_bounded_cubic_spline_rejects_input_below_domain_minimum():
    """Inputs below `x_min` must raise rather than extrapolate."""
    spline = interpolation.BoundedCubicSpline([0.0, 1.0, 2.0], [0.0, 1.0, 4.0])

    with pytest.raises(ValueError, match="outside"):
        spline(-1e-9)


def test_bounded_cubic_spline_rejects_input_above_domain_maximum():
    """Inputs above `x_max` must raise rather than extrapolate."""
    spline = interpolation.BoundedCubicSpline([0.0, 1.0, 2.0], [0.0, 1.0, 4.0])

    with pytest.raises(ValueError, match="outside"):
        spline(2.0 + 1e-9)
