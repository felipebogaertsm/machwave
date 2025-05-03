import numpy as np
import pytest

from machwave.services.structural.pressure_vessels import (
    _get_cylindrical_vessel_hoop_stress,
    _get_cylindrical_vessel_radial_stress,
    _get_cylindrical_vessel_logitudinal_stress,
    get_cylindrical_vessel_burst_pressure,
)


def test_unit_pressure_stresses() -> None:
    """Test the stresses for a unit pressure in a cylindrical vessel."""
    a = 1.0  # Inner radius
    b = np.sqrt(2)  # Outer radius
    p = 1.0  # Unit pressure

    hoop = _get_cylindrical_vessel_hoop_stress(p, a, b)
    radial = _get_cylindrical_vessel_radial_stress(p, a, b)
    longitudinal = _get_cylindrical_vessel_logitudinal_stress(p, a, b)

    assert pytest.approx(3.0) == hoop
    assert pytest.approx(-1.0) == radial
    assert pytest.approx(2.0) == longitudinal


def test_burst_pressure_reference_case() -> None:
    """Test the burst pressure for a reference case."""
    a = 1.0
    b = np.sqrt(2)
    sigma_y = 13.0

    burst = get_cylindrical_vessel_burst_pressure(a, b, sigma_y)
    expected = sigma_y / np.sqrt(13.0)
    assert pytest.approx(expected) == burst


def test_burst_pressure_scales_linearly_with_yield() -> None:
    """Test that burst pressure scales linearly with yield strength."""
    a = 1.0
    b = 2.0
    yield1 = 100.0
    yield2 = 200.0
    bp1 = get_cylindrical_vessel_burst_pressure(a, b, yield1)
    bp2 = get_cylindrical_vessel_burst_pressure(a, b, yield2)

    # Doubling yield strength should double burst pressure
    assert pytest.approx(2 * bp1) == bp2


def test_cylindrical_vessel_burst_pressure_zero_radius() -> None:
    """Test the burst pressure for a case with zero inner radius."""
    a = 0.0
    b = 1.0
    sigma_y = 13.0

    with pytest.raises(ZeroDivisionError):
        get_cylindrical_vessel_burst_pressure(a, b, sigma_y)


def test_cylindrical_vessel_burst_pressure_reference_case() -> None:
    """Test the burst pressure for a reference case."""
    a = 101.6e-3
    b = 95.25e-3
    sigma_y = 40e6

    burst = get_cylindrical_vessel_burst_pressure(a, b, sigma_y)
    expected = 2659383.0
    assert pytest.approx(expected) == burst
