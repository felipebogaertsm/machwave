import abc

import machwave.models.nozzle_losses.base as losses_base
import machwave.models.nozzle_losses.evaluation_context as evaluation_context
import machwave.models.propellants as propellants


class LossComponent(abc.ABC):
    """A single nozzle thrust coefficient loss."""

    name: str
    applicable_mixture_types: frozenset[propellants.MixtureType]
    target: losses_base.ThrustCoefficientTermTarget

    @abc.abstractmethod
    def get_loss_fraction(
        self, context: evaluation_context.NozzleLossEvaluationContext
    ) -> float:
        """Return the loss as a fraction in [0, 1] for the given context."""

    def applies_to(self, mixture_type: propellants.MixtureType) -> bool:
        """Whether the component is valid for the given mixture type."""
        return mixture_type in self.applicable_mixture_types
