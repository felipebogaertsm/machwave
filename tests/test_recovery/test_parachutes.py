import pytest

import numpy as np

from machwave.models.recovery.parachutes import (
    Parachute,
    HemisphericalParachute,
    ToroidalParachute,
)


def test_parachute_abstract_class():
    with pytest.raises(TypeError):
        parachute = Parachute()


def test_hemispherical_parachute_initialization():
    diameter = 2.5
    parachute = HemisphericalParachute(diameter)
    assert parachute.diameter == diameter


def test_hemispherical_parachute_drag_coefficient():
    diameter = 2.5
    parachute = HemisphericalParachute(diameter)
    assert parachute.drag_coefficient == 0.71


def test_hemispherical_parachute_area():
    diameter = 2.5
    parachute = HemisphericalParachute(diameter)
    expected_area = (np.pi * diameter**2) / 4
    assert parachute.area == expected_area


def test_toroidal_parachute_initialization():
    major_radius = 3.5
    minor_radius = 1.2
    parachute = ToroidalParachute(major_radius, minor_radius)
    assert parachute.major_radius == major_radius
    assert parachute.minor_radius == minor_radius


def test_toroidal_parachute_drag_coefficient():
    major_radius = 3.5
    minor_radius = 1.2
    parachute = ToroidalParachute(major_radius, minor_radius)
    assert parachute.drag_coefficient == 0.85


def test_toroidal_parachute_area():
    major_radius = 3.5
    minor_radius = 1.2
    parachute = ToroidalParachute(major_radius, minor_radius)
    expected_area = 4 * np.pi**2 * major_radius * minor_radius
    assert parachute.area == expected_area
