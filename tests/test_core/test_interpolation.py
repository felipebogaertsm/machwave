import numpy as np
import pytest

from machwave.core.solvers import interpolation


@pytest.mark.parametrize(
    "time, values, new_time, expected",
    [
        # Test with float input
        (
            np.array([0.0, 1.0, 2.0, 3.0]),
            np.array([0.0, 10.0, 20.0, 30.0]),
            1.5,
            15.0,
        ),
        # Test with exact match
        (
            np.array([0.0, 1.0, 2.0, 3.0]),
            np.array([0.0, 10.0, 20.0, 30.0]),
            2.0,
            20.0,
        ),
        # Test with extrapolation (lower bound)
        (
            np.array([1.0, 2.0, 3.0]),
            np.array([10.0, 20.0, 30.0]),
            0.5,
            10.0,  # np.interp returns boundary value for out-of-bounds
        ),
        # Test with extrapolation (upper bound)
        (
            np.array([1.0, 2.0, 3.0]),
            np.array([10.0, 20.0, 30.0]),
            4.0,
            30.0,  # np.interp returns boundary value for out-of-bounds
        ),
        # Test with negative values
        (
            np.array([0.0, 1.0, 2.0]),
            np.array([-10.0, 0.0, 10.0]),
            0.5,
            -5.0,
        ),
        # Test with non-linear spacing
        (
            np.array([0.0, 0.5, 2.0, 5.0]),
            np.array([0.0, 5.0, 10.0, 25.0]),
            1.25,
            7.5,
        ),
    ],
)
def test_interpolate_with_time_float(time, values, new_time, expected):
    """Test interpolation with float new_time input."""
    result = interpolation.interpolate_with_time(time, values, new_time)

    # Check that result is a float
    assert isinstance(result, float)

    # Check the value
    assert result == pytest.approx(expected, rel=1e-9)


@pytest.mark.parametrize(
    "time, values, new_time, expected",
    [
        # Test with array input - simple linear case
        (
            np.array([0.0, 1.0, 2.0, 3.0]),
            np.array([0.0, 10.0, 20.0, 30.0]),
            np.array([0.5, 1.5, 2.5]),
            np.array([5.0, 15.0, 25.0]),
        ),
        # Test with array input - exact matches
        (
            np.array([0.0, 1.0, 2.0, 3.0]),
            np.array([0.0, 10.0, 20.0, 30.0]),
            np.array([0.0, 1.0, 2.0, 3.0]),
            np.array([0.0, 10.0, 20.0, 30.0]),
        ),
        # Test with single element array
        (
            np.array([0.0, 1.0, 2.0]),
            np.array([0.0, 10.0, 20.0]),
            np.array([1.5]),
            np.array([15.0]),
        ),
        # Test with mixed interpolation and extrapolation
        (
            np.array([1.0, 2.0, 3.0]),
            np.array([10.0, 20.0, 30.0]),
            np.array([0.5, 1.5, 2.5, 3.5]),
            np.array([10.0, 15.0, 25.0, 30.0]),
        ),
        # Test with descending order new_time values
        (
            np.array([0.0, 1.0, 2.0, 3.0]),
            np.array([0.0, 10.0, 20.0, 30.0]),
            np.array([3.0, 2.0, 1.0, 0.0]),
            np.array([30.0, 20.0, 10.0, 0.0]),
        ),
        # Test with negative values
        (
            np.array([0.0, 1.0, 2.0]),
            np.array([-20.0, 0.0, 20.0]),
            np.array([0.25, 0.75, 1.5]),
            np.array([-15.0, -5.0, 10.0]),
        ),
    ],
)
def test_interpolate_with_time_array(time, values, new_time, expected):
    """Test interpolation with array new_time input."""
    result = interpolation.interpolate_with_time(time, values, new_time)

    # Check that result is an array
    assert isinstance(result, np.ndarray)

    # Check the values
    np.testing.assert_allclose(result, expected, rtol=1e-9)


def test_interpolate_with_time_empty_array():
    """Test interpolation with empty array."""
    time = np.array([0.0, 1.0, 2.0])
    values = np.array([0.0, 10.0, 20.0])
    new_time = np.array([])

    result = interpolation.interpolate_with_time(time, values, new_time)

    assert isinstance(result, np.ndarray)
    assert len(result) == 0


def test_interpolate_with_time_integer_input():
    """Test that integer inputs are handled correctly."""
    time = np.array([0.0, 1.0, 2.0, 3.0])
    values = np.array([0.0, 10.0, 20.0, 30.0])
    new_time = 2  # integer input

    result = interpolation.interpolate_with_time(time, values, new_time)

    # Should return float for scalar input
    assert isinstance(result, float)
    assert result == pytest.approx(20.0, rel=1e-9)


def test_interpolate_with_time_preserves_dtype():
    """Test that array output preserves appropriate numeric dtype."""
    time = np.array([0.0, 1.0, 2.0, 3.0])
    values = np.array([0.0, 10.0, 20.0, 30.0])
    new_time = np.array([0.5, 1.5, 2.5])

    result = interpolation.interpolate_with_time(time, values, new_time)

    assert isinstance(result, np.ndarray)
    assert np.issubdtype(result.dtype, np.floating)
