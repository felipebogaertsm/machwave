import machwave.models.nozzle_losses.base as losses_base
import machwave.models.nozzle_losses.evaluation_context as evaluation_context
import machwave.models.nozzle_losses.components.base as components_base
import machwave.models.propellants as propellants


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
        self, context: evaluation_context.NozzleLossEvaluationContext
    ) -> float:
        return self.fraction
