import pytest
import numpy as np

from rocketsolver.models.rocket.fuselage import (
    Fuselage,
    DragCoefficientTypeError,
)
from rocketsolver.services.math.geometric import get_circle_area


def test_frontal_area_calculation():
    length = 10.0
    outer_diameter = 2.0
    fuselage = Fuselage(length, outer_diameter, 0.0)

    expected_area = get_circle_area(outer_diameter)
    calculated_area = fuselage.frontal_area

    assert calculated_area == expected_area


def test_get_drag_coefficient_single_value():
    length = 10.0
    outer_diameter = 2.0
    drag_coefficient = 0.3
    fuselage = Fuselage(length, outer_diameter, drag_coefficient)

    calculated_coefficient = fuselage.get_drag_coefficient()

    assert calculated_coefficient == drag_coefficient


def test_get_drag_coefficient_interpolation():
    length = 10.0
    outer_diameter = 2.0
    drag_coefficient = np.array([[0.0, 0.3], [10.0, 0.2], [20.0, 0.1]])
    fuselage = Fuselage(length, outer_diameter, drag_coefficient)

    calculated_coefficient_5 = fuselage.get_drag_coefficient(5.0)
    calculated_coefficient_15 = fuselage.get_drag_coefficient(15.0)
    calculated_coefficient_25 = fuselage.get_drag_coefficient(25.0)

    assert calculated_coefficient_5 == pytest.approx(0.25)
    assert calculated_coefficient_15 == pytest.approx(0.15)
    assert calculated_coefficient_25 == pytest.approx(0.1)


def test_get_drag_coefficient_invalid_type():
    length = 10.0
    outer_diameter = 2.0
    drag_coefficient = "invalid"
    fuselage = Fuselage(length, outer_diameter, drag_coefficient)

    with pytest.raises(DragCoefficientTypeError):
        fuselage.get_drag_coefficient()
