from __future__ import annotations

import numpy as np

import machwave.models.nozzle_losses.base as losses_base
import machwave.models.nozzle_losses.components.base as components_base
import machwave.models.propellants as propellants


class DivergentLoss(components_base.LossComponent):
    """
    Nozzle divergence loss.

    Only applicable for a conical convergent-divergent nozzle. Derates the momentum
    term only.
    """

    name = "divergent_loss"
    label = "divergent nozzle loss"
    applicable_mixture_types = frozenset(
        {propellants.MixtureType.SOLID, propellants.MixtureType.BILIQUID}
    )
    target = losses_base.ThrustCoefficientTermTarget.MOMENTUM
    timestep_parameter_map = {"divergent_angle": "nozzle.divergent_angle"}
    typical_range = (0.0075, 0.05)

    @staticmethod
    def loss_fraction(divergent_angle: float) -> float:
        """
        Return the divergent nozzle loss fraction given the half angle.

        Args:
            divergent_angle: Half angle of the divergent nozzle [deg].

        Returns:
            Divergent loss fraction in [0, 1].
        """
        return 0.5 * (1 - np.cos(np.deg2rad(divergent_angle)))
