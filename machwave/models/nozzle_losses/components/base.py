from __future__ import annotations

import abc
import functools
import typing
import warnings

import machwave.models.nozzle_losses.base as losses_base
import machwave.models.propellants as propellants

if typing.TYPE_CHECKING:
    import machwave.simulation.states as simulation_states


class LossComponent(abc.ABC):
    """
    A single nozzle thrust coefficient loss.

    Every subclass defines a `loss_fraction` method that returns the fraction from
    scalar inputs (applying any unit conversions itself), and a
    `timestep_parameter_map` binding each of its parameters to a dotted attribute path
    on the timestep conditions. The inherited `get_loss_fraction` resolves the map,
    calls `loss_fraction`, validates the result lies in [0, 1], and warns when it
    falls outside `typical_range`. Condition-independent losses take no parameters and
    leave `timestep_parameter_map` empty.

    Attributes:
        name: Identifier for the loss series.
        label: Human-readable name used in reports.
        applicable_mixture_types: Mixture types the loss is valid for.
        target: Thrust coefficient term the loss derates.
        timestep_parameter_map: Maps each `loss_fraction` parameter to a dotted
            attribute path resolved against the timestep conditions.
        typical_range: Optional (lower, upper) fraction the loss is expected to fall
            within. A result outside it triggers a warning.
        loss_fraction: Computes the loss fraction; defined by every subclass.
    """

    name: str
    label: str
    applicable_mixture_types: frozenset[propellants.MixtureType]
    target: losses_base.ThrustCoefficientTermTarget
    timestep_parameter_map: typing.ClassVar[dict[str, str]] = {}
    typical_range: typing.ClassVar[tuple[float, float] | None] = None
    loss_fraction: typing.ClassVar[typing.Callable[..., float]]

    def __init_subclass__(cls, **kwargs: typing.Any) -> None:
        super().__init_subclass__(**kwargs)
        for required in ("applicable_mixture_types", "target"):
            if not hasattr(cls, required):
                raise TypeError(f"{cls.__name__} must define `{required}`.")
        if not callable(getattr(cls, "loss_fraction", None)):
            raise TypeError(f"{cls.__name__} must define a `loss_fraction` method.")

    def _parse_timestep_conditions(
        self, timestep_conditions: simulation_states.TimestepConditions
    ) -> dict[str, typing.Any]:
        """
        Resolve `timestep_parameter_map` against `timestep_conditions`.

        Each value is a dotted attribute path. For the map
        {
            "i_sp_frozen": "propellant_properties.i_sp_frozen",
            "chamber_pressure": "chamber_pressure",
        }
        this returns
        {
            "i_sp_frozen": timestep_conditions.propellant_properties.i_sp_frozen,
            "chamber_pressure": timestep_conditions.chamber_pressure,
        }
        """
        return {
            parameter: functools.reduce(getattr, path.split("."), timestep_conditions)
            for parameter, path in self.timestep_parameter_map.items()
        }

    def get_loss_fraction(
        self, timestep_conditions: simulation_states.TimestepConditions
    ) -> float:
        """
        Return the loss as a fraction in [0, 1] for the timestep conditions.

        Args:
            timestep_conditions: Timestep conditions to evaluate the loss fraction at.

        Returns:
            Loss fraction in [0, 1].

        Raises:
            ValueError: If the loss fraction is outside [0, 1].

        Warns:
            UserWarning: If the loss fraction is outside `typical_range`, if defined.
        """
        parameters = self._parse_timestep_conditions(timestep_conditions)
        fraction = self.loss_fraction(**parameters)

        if not 0.0 <= fraction <= 1.0:
            raise ValueError(f"{self.name} loss fraction {fraction} is outside [0, 1].")
        if self.typical_range is not None:
            lower, upper = self.typical_range
            if not lower <= fraction <= upper:
                warnings.warn(
                    f"{self.name} loss fraction {fraction} is outside its typical "
                    f"range [{lower}, {upper}]."
                )
        return fraction

    def applies_to(self, mixture_type: propellants.MixtureType) -> bool:
        """Whether the component is valid for the given mixture type."""
        return mixture_type in self.applicable_mixture_types
