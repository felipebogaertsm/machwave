import abc

import machwave.models.nozzle_losses.base as losses_base
import machwave.models.propellants as propellants


class LossComponent(abc.ABC):
    """A single nozzle thrust-coefficient loss; wraps one loss formula."""

    name: str
    applicable_mixture_types: frozenset[propellants.MixtureType]
    default_target: losses_base.ThrustCoefficientTermTarget

    def __init__(
        self,
        *,
        target: losses_base.ThrustCoefficientTermTarget | None = None,
    ) -> None:
        """
        Initialize a loss component.

        Args:
            target: Thrust-coefficient term to derate. Defaults to the
                component's `default_target`.
        """
        self.target = target if target is not None else self.default_target

    @abc.abstractmethod
    def get_loss_fraction(self, context: losses_base.LossEvaluationContext) -> float:
        """Return the loss as a fraction in [0, 1] for the given step."""

    def applies_to(self, mixture_type: propellants.MixtureType) -> bool:
        """Whether the component is valid for the given mixture type."""
        return mixture_type in self.applicable_mixture_types
