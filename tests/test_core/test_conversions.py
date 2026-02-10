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


@pytest.mark.parametrize(
    "a_imperial, n, expected_a_metric",
    [
        (0.019, 0.625, 10.82),  # KN-Sorbitol 15-117 psia
        (0.0, 0.5, 0.0),
        (1.648, -0.314, 8.77),  # KN-Sorbitol 117-218 psia
    ],
)
def test_convert_burn_rate_coefficient_to_metric(a_imperial, n, expected_a_metric):
    assert conversions.convert_burn_rate_coefficient_to_metric(
        a_imperial, n
    ) == pytest.approx(expected_a_metric, rel=1e-2)


@pytest.mark.parametrize(
    "rankine, expected_kelvin",
    [
        (0.0, 0.0),
        (491.67, 273.15),  # Water freezing point
        (671.67, 373.15),  # Water boiling point
        (1000.0, 555.56),
    ],
)
def test_convert_rankine_to_kelvin(rankine, expected_kelvin):
    assert conversions.convert_rankine_to_kelvin(rankine) == pytest.approx(
        expected_kelvin, rel=1e-2
    )


@pytest.mark.parametrize(
    "lbft3, expected_kgm3",
    [
        (0.0, 0.0),
        (62.428, 1000.0),  # Water density
        (1.0, 16.01846337),
        (100.0, 1601.846337),
    ],
)
def test_convert_lbft3_to_kgm3(lbft3, expected_kgm3):
    assert conversions.convert_lbft3_to_kgm3(lbft3) == pytest.approx(
        expected_kgm3, rel=1e-2
    )


@pytest.mark.parametrize(
    "j_per_mol, expected_cal_per_mol",
    [
        (0.0, 0.0),
        (4.184, 1.0),
        (41840.0, 10000.0),
        (-8368.0, -2000.0),
    ],
)
def test_convert_joules_per_mol_to_cal_per_mol(j_per_mol, expected_cal_per_mol):
    assert conversions.convert_joules_per_mol_to_cal_per_mol(
        j_per_mol
    ) == pytest.approx(expected_cal_per_mol, rel=1e-2)


@pytest.mark.parametrize(
    "kgm3, expected_gcc",
    [
        (0.0, 0.0),
        (1000.0, 1.0),  # Water density
        (2700.0, 2.7),  # Aluminum density
        (7850.0, 7.85),  # Steel density
    ],
)
def test_convert_kgm3_to_gcc(kgm3, expected_gcc):
    assert conversions.convert_kgm3_to_gcc(kgm3) == pytest.approx(
        expected_gcc, rel=1e-2
    )
