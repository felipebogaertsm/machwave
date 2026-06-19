from __future__ import annotations

import typing

import machwave.models.nozzle_losses.base as losses_base
import machwave.models.nozzle_losses.components.base as components_base
import machwave.models.propellants as propellants

if typing.TYPE_CHECKING:
    import machwave.simulation.states as simulation_states


class ConstantFractionLoss(components_base.LossComponent):
    """A fixed loss fraction, independent of operating conditions."""

    applicable_mixture_types = frozenset(
        {propellants.MixtureType.SOLID, propellants.MixtureType.BILIQUID}
    )
    target = losses_base.ThrustCoefficientTermTarget.BOTH

    def __init__(self, fraction: float, *, name: str) -> None:
        """
        Initialize a constant loss.

        Args:
            fraction: Loss fraction in [0, 1].
            name: Diagnostic series name.

        Raises:
            ValueError: If `fraction` is outside [0, 1].
        """
        if not 0.0 <= fraction <= 1.0:
            raise ValueError(f"loss fraction must be in [0, 1], got {fraction}.")
        self.name = name
        self.fraction = fraction

    def get_loss_fraction(
        self, timestep_conditions: simulation_states.TimestepConditions
    ) -> float:
        return self.fraction
