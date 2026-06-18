import machwave.models.nozzle_losses.base as losses_base
import machwave.models.nozzle_losses.components.base as components_base
import machwave.models.propellants as propellants


class ConstantFractionLoss(components_base.LossComponent):
    """A fixed loss fraction, independent of operating conditions."""

    applicable_mixture_types = frozenset(
        {propellants.MixtureType.SOLID, propellants.MixtureType.BILIQUID}
    )
    default_target = losses_base.ThrustCoefficientTermTarget.BOTH

    def __init__(
        self,
        fraction: float,
        *,
        name: str,
        target: losses_base.ThrustCoefficientTermTarget | None = None,
    ) -> None:
        """
        Initialize a constant loss.

        Args:
            fraction: Loss fraction in [0, 1].
            name: Diagnostic series name.
            target: Thrust-coefficient term to derate.

        Raises:
            ValueError: If `fraction` is outside [0, 1].
        """
        super().__init__(target=target)
        if not 0.0 <= fraction <= 1.0:
            raise ValueError(f"loss fraction must be in [0, 1], got {fraction}.")
        self.name = name
        self.fraction = fraction

    def get_loss_fraction(
        self, context: losses_base.NozzleLossEvaluationContext
    ) -> float:
        return self.fraction
