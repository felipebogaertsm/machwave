import pytest

import machwave.core.geometric as geometric


def test_get_circle_area():
    # Test case: Circle with diameter 4
    diameter = 4
    expected_area = 12.56637
    assert pytest.approx(geometric.get_circle_area(diameter), rel=1e-4) == expected_area


def test_get_cylinder_surface_area():
    # Test case: Cylinder with length 5 and diameter 2
    length = 5
    diameter = 2
    expected_area = 31.4159265359
    assert (
        pytest.approx(geometric.get_cylinder_surface_area(length, diameter), rel=1e-4)
        == expected_area
    )
