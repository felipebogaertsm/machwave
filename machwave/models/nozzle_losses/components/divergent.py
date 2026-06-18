import numpy as np

import machwave.common.decorators as decorators
import machwave.models.nozzle_losses.base as losses_base
import machwave.models.nozzle_losses.evaluation_context as evaluation_context
import machwave.models.nozzle_losses.components.base as components_base
import machwave.models.propellants as propellants

TYPICAL_RANGE = {"lower": 0.0075, "upper": 0.05}  # fraction


@decorators.check_bounds(lower=0.0, upper=1.0)
@decorators.warn_if_outside_range(**TYPICAL_RANGE)
def get_divergent_loss_fraction(divergent_angle: float) -> float:
    """
    Return the divergent nozzle loss fraction given the half angle.

    Only applicable for a conical convergent-divergent nozzle.

    Args:
        divergent_angle: Half angle of the divergent nozzle [deg].

    Returns:
        Divergent loss fraction in [0, 1].
    """
    return 0.5 * (1 - np.cos(np.deg2rad(divergent_angle)))


class DivergentLoss(components_base.LossComponent):
    """Nozzle divergence loss; derates the momentum term only."""

    name = "divergent_loss"
    applicable_mixture_types = frozenset(
        {propellants.MixtureType.SOLID, propellants.MixtureType.BILIQUID}
    )
    target = losses_base.ThrustCoefficientTermTarget.MOMENTUM

    def get_loss_fraction(
        self, context: evaluation_context.NozzleLossEvaluationContext
    ) -> float:
        return get_divergent_loss_fraction(
            divergent_angle=context.nozzle.divergent_angle
        )
