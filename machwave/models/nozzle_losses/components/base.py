from __future__ import annotations

import abc
import functools
import inspect
import typing
import warnings

import machwave.models.nozzle_losses.base as losses_base
import machwave.models.propellants as propellants

if typing.TYPE_CHECKING:
    import machwave.simulation.states as simulation_states


class LossComponent(abc.ABC):
    """
    A single nozzle thrust coefficient loss.

    Every subclass must define:
    1. a `compute_loss_fraction` method that returns the fraction from scalar inputs
    (applying any unit conversions itself);
    2. a `timestep_parameter_map` binding each of the `compute_loss_fraction` parameters
    to a dotted attribute path on the timestep conditions.

    Attributes:
        name: Identifier for the loss.
        label: Display name.
        applicable_mixture_types: Mixture types the loss is valid for.
        target: Thrust coefficient term(s) the loss derates.
        timestep_parameter_map: Maps each `compute_loss_fraction` argument to an
            attribute path of timestep conditions.
        typical_range: (lower, upper) fraction the loss is expected to fall within.
        compute_loss_fraction: Computes the loss fraction. Must be defined by every
            subclass.
    """

    name: str
    label: str
    applicable_mixture_types: typing.ClassVar[frozenset[propellants.MixtureType]]
    target: typing.ClassVar[losses_base.ThrustCoefficientTermTarget]
    timestep_parameter_map: typing.ClassVar[dict[str, str]] = {}
    typical_range: typing.ClassVar[tuple[float, float] | None] = None
    compute_loss_fraction: typing.ClassVar[typing.Callable[..., float]]

    def __init_subclass__(cls, **kwargs: typing.Any) -> None:
        super().__init_subclass__(**kwargs)

        for required in ("applicable_mixture_types", "target"):
            if not hasattr(cls, required):
                raise TypeError(f"{cls.__name__} must define `{required}`.")

        compute_loss_fraction = inspect.getattr_static(
            cls, "compute_loss_fraction", None
        )
        if not isinstance(compute_loss_fraction, (staticmethod, classmethod)):
            raise TypeError(
                f"{cls.__name__} must define `compute_loss_fraction` as a static or "
                "class method."
            )

    def _parse_compute_loss_fraction_arguments(
        self, timestep_conditions: simulation_states.TimestepConditions
    ) -> dict[str, typing.Any]:
        """Resolve the keyword arguments for `compute_loss_fraction` for a given timestep."""
        return {
            argument: functools.reduce(getattr, path.split("."), timestep_conditions)
            for argument, path in self.timestep_parameter_map.items()
        }

    def get_loss_fraction(
        self, timestep_conditions: simulation_states.TimestepConditions
    ) -> float:
        """
        Return the loss fraction for the timestep conditions, validated to [0, 1].

        Args:
            timestep_conditions: Timestep conditions to evaluate the loss fraction at.

        Returns:
            Loss fraction in [0, 1].

        Raises:
            ValueError: If the loss fraction is outside [0, 1].

        Warns:
            UserWarning: If the loss fraction is outside `typical_range`, if defined.
        """
        arguments = self._parse_compute_loss_fraction_arguments(timestep_conditions)
        fraction = self.compute_loss_fraction(**arguments)

        if not 0.0 <= fraction <= 1.0:
            raise ValueError(f"{self.name} loss fraction {fraction} is outside [0, 1].")
        if self.typical_range is not None:
            lower, upper = self.typical_range
            if not lower <= fraction <= upper:
                warnings.warn(
                    f"{self.name} loss fraction is outside its typical "
                    f"range [{lower}, {upper}]."
                )
        return fraction

    def applies_to(self, mixture_type: propellants.MixtureType) -> bool:
        """Whether the component is valid for the given mixture type."""
        return mixture_type in self.applicable_mixture_types
