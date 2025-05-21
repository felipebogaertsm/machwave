import pytest

from machwave.core import correction_factors


@pytest.mark.parametrize(
    "divergent_angle, expected_correction_factor",
    [
        (0.0, 0.0),
        (2.0, 0.0003),
        (4.0, 0.0012),
        (6.0, 0.0028),
        (8.0, 0.0049),
        (10.0, 0.0076),
        (12.0, 0.0110),
        (15.0, 0.0170),
        (20.0, 0.0302),
        (24.0, 0.0433),
    ],
)
def test_get_nozzle_divergent_correction_factor(
    divergent_angle, expected_correction_factor
):
    """
    Parameters obtained from Sutton.
    """
    eta_div = correction_factors.get_nozzle_divergent_correction_factor(
        divergent_angle=divergent_angle
    )
    assert eta_div == pytest.approx(expected_correction_factor, abs=1e-4)


@pytest.mark.parametrize(
    "i_sp_th_frozen, i_sp_th_shifting, chamber_pressure_psi, expected_correction_factor",
    [
        (152.4, 154.1, 150.0, 0.0037),  # KNDX @ 150 psi, no pressure damping
        (152.4, 154.1, 200.0, 0.0037),  # KNDX @ 200 psi, pressure = threshold
        (152.4, 154.1, 210.0, 0.0035),  # KNDX @ 210 psi
        (152.4, 154.1, 1000.0, 0.0007),  # KNDX @ 1000 psi
        (250.0, 300.0, 320.0, 0.0347),  # large Isp @ 320 psi
        (250.0, 250.0, 200.0, 0.0),  # same frozen/shifting Isp
        (250.0, 250.0, 1000.0, 0.0),  # same frozen/shifting Isp
        (300.0, 300.0, 200.0, 0.0),  # same frozen/shifting Isp
        (300.0, 300.0, 1000.0, 0.0),  # same frozen/shifting Isp
    ],
)
def test_get_kinetics_correction_factor(
    i_sp_th_frozen, i_sp_th_shifting, chamber_pressure_psi, expected_correction_factor
):
    eta_kin = correction_factors.get_kinetics_correction_factor(
        i_sp_th_frozen=i_sp_th_frozen,
        i_sp_th_shifting=i_sp_th_shifting,
        chamber_pressure_psi=chamber_pressure_psi,
    )
    assert eta_kin == pytest.approx(expected_correction_factor, abs=1e-4)
