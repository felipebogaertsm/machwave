import pytest

from machwave.core import conversions


@pytest.mark.parametrize(
    "pa, expected_psi",
    [
        (100_000, 14.5037735),
        (0, 0.0),
        (-50_000, -7.252642),
    ],
)
def test_convert_pa_to_psi(pa, expected_psi):
    assert conversions.convert_pa_to_psi(pa) == pytest.approx(expected_psi, rel=1e-2)


@pytest.mark.parametrize(
    "pa, expected_mpa",
    [
        (1_000_000, 1.0),
        (0, 0.0),
        (-500_000, -0.5),
    ],
)
def test_convert_pa_to_mpa(pa, expected_mpa):
    assert conversions.convert_pa_to_mpa(pa) == pytest.approx(expected_mpa, rel=1e-2)


@pytest.mark.parametrize(
    "mpa, expected_pa",
    [
        (2.5, 2_500_000.0),
        (0, 0.0),
        (-1.2, -1_200_000.0),
    ],
)
def test_convert_mpa_to_pa(mpa, expected_pa):
    assert conversions.convert_mpa_to_pa(mpa) == pytest.approx(expected_pa, rel=1e-2)


@pytest.mark.parametrize(
    "kg_m2_s, expected_slug_ft2_s",
    [
        (0.001, 1.42233e-6),
        (0.0, 0.0),
        (-0.002, -2.84466e-6),
    ],
)
def test_convert_mass_flux_metric_to_imperial(kg_m2_s, expected_slug_ft2_s):
    assert conversions.convert_mass_flux_metric_to_imperial(kg_m2_s) == pytest.approx(
        expected_slug_ft2_s, rel=1e-2
    )


@pytest.mark.parametrize(
    "meters, expected_inches",
    [
        (0.0, 0.0),
        (1.0, 39.3701),
        (0.0254, 1.0),
        (-1.0, -39.3701),
    ],
)
def test_convert_meter_to_inch(meters, expected_inches):
    assert conversions.convert_meter_to_inch(meters) == pytest.approx(
        expected_inches, rel=1e-6
    )


@pytest.mark.parametrize(
    "meters, expected_micrometres",
    [
        (0.0, 0.0),
        (1e-6, 1.0),
        (1.0, 1_000_000.0),
        (-0.5, -500_000.0),
    ],
)
def test_convert_meter_to_micrometer(meters, expected_micrometres):
    assert conversions.convert_meter_to_micrometer(meters) == pytest.approx(
        expected_micrometres, rel=1e-12
    )
