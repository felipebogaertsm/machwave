from __future__ import annotations

import dataclasses
import enum
import typing

import machwave.core.compressible_flow.nozzle as nozzle_core
import machwave.models.propellants as propellants

if typing.TYPE_CHECKING:
    import machwave.models.nozzle_losses.components.base as components_base
    import machwave.models.nozzle_losses.evaluation_context as evaluation_context


class ThrustCoefficientTermTarget(enum.StrEnum):
    """Which term of the thrust coefficient a nozzle loss derates."""

    MOMENTUM = "momentum"
    PRESSURE = "pressure"
    BOTH = "both"


@dataclasses.dataclass(frozen=True)
class NozzleLossEvaluationResult:
    """Outcome of applying a loss model to the decoupled thrust coefficient."""

    momentum_term: float
    pressure_term: float
    nozzle_efficiency: float
    loss_fractions: dict[str, float]


class NozzleLossModel:
    """Models a nozzle loss composition."""

    def __init__(
        self,
        components: list[components_base.LossComponent],
        *,
        mixture_type: propellants.MixtureType,
    ) -> None:
        """
        Initialize a nozzle loss model.

        Args:
            components: Loss components.
            mixture_type: Engine mixture type the model is built for.

        Raises:
            ValueError: If two components share a name, or a component is not
                applicable to `mixture_type`.
        """
        names = [component.name for component in components]
        if len(names) != len(set(names)):
            raise ValueError(f"Duplicate loss component names: {names}.")
        for component in components:
            if not component.applies_to(mixture_type):
                raise ValueError(
                    f"{type(component).__name__} is not applicable to "
                    f"{mixture_type} engines."
                )
        self.components = components
        self.mixture_type = mixture_type

    @property
    def component_names(self) -> list[str]:
        """Component names, in evaluation order."""
        return [component.name for component in self.components]

    def evaluate(
        self,
        momentum_term: float,
        pressure_term: float,
        context: evaluation_context.NozzleLossEvaluationContext,
    ) -> NozzleLossEvaluationResult:
        """
        Apply every component to the decoupled thrust-coefficient terms.

        Args:
            momentum_term: Momentum term of the ideal thrust coefficient.
            pressure_term: Pressure term of the ideal thrust coefficient.
            context: Instantaneous parameters for the components.

        Returns:
            The corrected terms, the diagnostic nozzle efficiency, and each component's
            loss fraction.

        Raises:
            ValueError: If the losses derate either term below zero.
        """
        loss_fractions = {
            component.name: component.get_loss_fraction(context)
            for component in self.components
        }
        momentum_factor = 1.0
        pressure_factor = 1.0

        for component in self.components:
            fraction = loss_fractions[component.name]
            if component.target in (
                ThrustCoefficientTermTarget.MOMENTUM,
                ThrustCoefficientTermTarget.BOTH,
            ):
                momentum_factor -= fraction
            if component.target in (
                ThrustCoefficientTermTarget.PRESSURE,
                ThrustCoefficientTermTarget.BOTH,
            ):
                pressure_factor -= fraction

        if momentum_factor < 0.0 or pressure_factor < 0.0:
            raise ValueError(
                "Nozzle losses derate the thrust coefficient below zero: "
                f"momentum factor {momentum_factor}, pressure factor "
                f"{pressure_factor}."
            )

        corrected_momentum_term = nozzle_core.apply_thrust_coefficient_correction(
            momentum_term, momentum_factor
        )
        corrected_pressure_term = nozzle_core.apply_thrust_coefficient_correction(
            pressure_term, pressure_factor
        )
        nozzle_efficiency = 1.0 - sum(loss_fractions.values())

        return NozzleLossEvaluationResult(
            momentum_term=corrected_momentum_term,
            pressure_term=corrected_pressure_term,
            nozzle_efficiency=nozzle_efficiency,
            loss_fractions=loss_fractions,
        )
