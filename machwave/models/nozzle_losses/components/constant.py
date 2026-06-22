from __future__ import annotations

import typing

import machwave.models.nozzle_losses.base as losses_base
import machwave.models.nozzle_losses.components.base as components_base
import machwave.models.propellants as propellants

if typing.TYPE_CHECKING:
    import machwave.simulation.states as simulation_states


class ConstantFractionLoss(components_base.LossComponent):
    """A fixed loss fraction."""

    applicable_mixture_types = frozenset(
        {propellants.MixtureType.SOLID, propellants.MixtureType.BILIQUID}
    )
    target = losses_base.ThrustCoefficientTermTarget.BOTH

    def __init__(self, fraction: float, *, name: str, label: str | None = None) -> None:
        """
        Initialize a constant loss.

        Args:
            fraction: Loss fraction in [0, 1].
            name: Diagnostic series name.
            label: Human-readable report name; defaults to a spaced `name`.

        Raises:
            ValueError: If `fraction` is outside [0, 1].
        """
        if not 0.0 <= fraction <= 1.0:
            raise ValueError(f"loss fraction must be in [0, 1], got {fraction}.")

        self.name = name
        self.label = label if label is not None else name.replace("_", " ")
        self.fraction = fraction

    @staticmethod
    def compute_loss_fraction(fraction: float) -> float:
        return fraction

    def _parse_compute_loss_fraction_arguments(
        self, timestep_conditions: simulation_states.TimestepConditions
    ) -> dict[str, typing.Any]:
        """Supply the configured constant fraction to `compute_loss_fraction`."""
        return {"fraction": self.fraction}
