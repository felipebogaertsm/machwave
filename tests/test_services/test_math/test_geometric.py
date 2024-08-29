import pytest

import numpy as np

from machwave.services.math.geometric import (
    get_circle_area,
    get_torus_area,
    get_cylinder_surface_area,
    get_cylinder_volume,
    get_length,
    get_trapezoidal_area,
)


def test_get_circle_area():
    # Test case: Circle with diameter 4
    diameter = 4
    expected_area = 12.56637
    assert pytest.approx(get_circle_area(diameter), rel=1e-4) == expected_area


def test_get_torus_area():
    # Test case: Torus with major radius 2 and minor radius 1
    major_radius = 2
    minor_radius = 1
    expected_area = 78.95684
    assert (
        pytest.approx(get_torus_area(major_radius, minor_radius), rel=1e-4)
        == expected_area
    )


def test_get_trapezoidal_area():
    # Test case: Trapezoid with base length 4, tip length 6, and height 3
    base_length = 4
    tip_length = 6
    height = 3
    expected_area = 15.0
    assert (
        get_trapezoidal_area(base_length, tip_length, height) == expected_area
    )


def test_get_cylinder_surface_area():
    # Test case: Cylinder with length 5 and diameter 2
    length = 5
    diameter = 2
    expected_area = 31.4159265359
    assert (
        pytest.approx(get_cylinder_surface_area(length, diameter), rel=1e-4)
        == expected_area
    )


def test_get_cylinder_volume():
    # Test case: Cylinder with length 5 and diameter 2
    length = 5
    diameter = 2
    expected_volume = 15.7079632679
    assert (
        pytest.approx(get_cylinder_volume(diameter, length), rel=1e-4)
        == expected_volume
    )
