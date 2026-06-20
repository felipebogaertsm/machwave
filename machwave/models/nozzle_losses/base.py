from __future__ import annotations

import dataclasses
import enum
import typing

import machwave.models.propellants as propellants

if typing.TYPE_CHECKING:
    import machwave.models.nozzle_losses.components.base as components_base
    import machwave.simulation.states as simulation_states

_MINIMUM_IDEAL_THRUST_COEFFICIENT = 1e-9


class ThrustCoefficientTermTarget(enum.StrEnum):
    """
    Which term of the thrust coefficient a nozzle loss derates.

    There can only be two thrust coefficient terms, momentum and pressure, so this class
    is not extensible.
    """

    MOMENTUM = "momentum"
    PRESSURE = "pressure"
    BOTH = "both"

    @property
    def affects_momentum(self) -> bool:
        """Whether this target derates the momentum term."""
        return self in (self.MOMENTUM, self.BOTH)

    @property
    def affects_pressure(self) -> bool:
        """Whether this target derates the pressure term."""
        return self in (self.PRESSURE, self.BOTH)


@dataclasses.dataclass(frozen=True)
class NozzleLossEvaluationResult:
    """Outcome of applying a loss model to each thrust coefficient term."""

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
        Initialize a nozzle loss model, frozen after initialization.

        Args:
            components: Loss components to be evaluated and applied.
            mixture_type: Engine mixture type the model is built for.

        Raises:
            ValueError: If a component lacks a `name` or `label`, two components share a
                name, or a component is not applicable to `mixture_type`.
        """
        for component in components:
            for attribute in ("name", "label"):
                value = getattr(component, attribute, None)
                if not isinstance(value, str) or not value:
                    raise ValueError(
                        f"{type(component).__name__} must define a non empty "
                        f"`{attribute}`."
                    )

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

        # Components are frozen, so names and labels are cached
        self.component_names = names
        self.component_labels = {
            component.name: component.label for component in components
        }

    def _accumulate_loss_factors(
        self, timestep_conditions: simulation_states.TimestepConditions
    ) -> tuple[dict[str, float], float, float]:
        """
        Sum the component loss fractions into the momentum and pressure factors.

        Each factor starts at one and is reduced by every fraction whose component
        targets that term.

        Returns:
            The per-component loss fractions and the aggregate momentum and pressure
            factors.
        """
        loss_fractions: dict[str, float] = {}
        momentum_factor = 1.0
        pressure_factor = 1.0

        for component in self.components:
            fraction = component.get_loss_fraction(timestep_conditions)
            loss_fractions[component.name] = fraction
            if component.target.affects_momentum:
                momentum_factor -= fraction
            if component.target.affects_pressure:
                pressure_factor -= fraction

        return loss_fractions, momentum_factor, pressure_factor

    def evaluate(
        self,
        momentum_term: float,
        pressure_term: float,
        timestep_conditions: simulation_states.TimestepConditions,
    ) -> NozzleLossEvaluationResult:
        """
        Apply every loss component to the decoupled thrust coefficient terms.

        Args:
            momentum_term: Momentum term of the ideal thrust coefficient.
            pressure_term: Pressure term of the ideal thrust coefficient.
            timestep_conditions: Engine conditions at this timestep for the components.

        Returns:
            The corrected terms, the nozzle efficiency and the loss fractions.

        Raises:
            ValueError: If the losses derate either term below zero.
        """
        loss_fractions, momentum_factor, pressure_factor = (
            self._accumulate_loss_factors(timestep_conditions)
        )

        if momentum_factor < 0.0 or pressure_factor < 0.0:
            raise ValueError(
                "Nozzle losses derate the thrust coefficient below zero: "
                f"momentum factor {momentum_factor}, pressure factor "
                f"{pressure_factor}."
            )

        corrected_momentum_term = momentum_term * momentum_factor
        corrected_pressure_term = pressure_term * pressure_factor
        ideal_thrust_coefficient = momentum_term + pressure_term
        if ideal_thrust_coefficient > _MINIMUM_IDEAL_THRUST_COEFFICIENT:
            nozzle_efficiency = float(
                (corrected_momentum_term + corrected_pressure_term)
                / ideal_thrust_coefficient
            )
        else:
            # If the pressure term is deeply negative and cancels out the momentum term,
            # the ideal thrust coefficient is near zero so efficiency shoots to
            # infinity. In this case, the nozzle efficiency is defined only by the
            # momentum factor.
            nozzle_efficiency = float(momentum_factor)

        return NozzleLossEvaluationResult(
            momentum_term=corrected_momentum_term,
            pressure_term=corrected_pressure_term,
            nozzle_efficiency=nozzle_efficiency,
            loss_fractions=loss_fractions,
        )
