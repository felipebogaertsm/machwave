import pytest

from machwave.services.conversions import (
    convert_mass_flux_metric_to_imperial,
    convert_mpa_to_pa,
    convert_pa_to_mpa,
    convert_pa_to_psi,
)


def test_convert_pa_to_psi():
    assert convert_pa_to_psi(100000) == pytest.approx(14.5037735, rel=1e-2)
    assert convert_pa_to_psi(0) == pytest.approx(0.0, rel=1e-2)
    assert convert_pa_to_psi(-50000) == pytest.approx(-7.252642, rel=1e-2)


def test_convert_pa_to_mpa():
    assert convert_pa_to_mpa(1000000) == pytest.approx(1.0, rel=1e-2)
    assert convert_pa_to_mpa(0) == pytest.approx(0.0, rel=1e-2)
    assert convert_pa_to_mpa(-500000) == pytest.approx(-0.5, rel=1e-2)


def test_convert_mpa_to_pa():
    assert convert_mpa_to_pa(2.5) == pytest.approx(2500000.0, rel=1e-2)
    assert convert_mpa_to_pa(0) == pytest.approx(0.0, rel=1e-2)
    assert convert_mpa_to_pa(-1.2) == pytest.approx(-1200000.0, rel=1e-2)


def test_convert_mass_flux_metric_to_imperial():
    assert convert_mass_flux_metric_to_imperial(0.001) == pytest.approx(
        1.42233e-6, rel=1e-2
    )
    assert convert_mass_flux_metric_to_imperial(0) == pytest.approx(
        0.0, rel=1e-2
    )
    assert convert_mass_flux_metric_to_imperial(-0.002) == pytest.approx(
        -2.84466e-6, rel=1e-2
    )
