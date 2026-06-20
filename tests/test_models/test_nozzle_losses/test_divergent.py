import pytest

import machwave.models.nozzle_losses.components.divergent as divergent


@pytest.mark.parametrize(
    "divergent_angle, expected_loss_fraction",
    [
        (0.0, 0.0000),
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
def test_divergent_loss_fraction(divergent_angle, expected_loss_fraction):
    """
    Parameters obtained from Sutton (originally tabulated as percentages,
    here divided by 100 to match the fraction convention).
    """
    divergent_loss = divergent.DivergentLoss.compute_loss_fraction(
        divergent_angle=divergent_angle
    )
    assert divergent_loss == pytest.approx(expected_loss_fraction, abs=1e-4)
