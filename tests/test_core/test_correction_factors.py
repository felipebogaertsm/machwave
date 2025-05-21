from machwave.core import correction_factors

import pytest


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
    eta_div = correction_factors.get_nozzle_divergent_correction_factor(
        divergent_angle=divergent_angle
    )
    assert eta_div == pytest.approx(expected_correction_factor, abs=1e-4)
