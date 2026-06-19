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

    Each component must define a `loss_fraction` static method as a function of scalar
    inputs. In case the `loss_fraction` requires one or more parameters,
    `timestep_parameter_sources` must be defined.

    Defining `typical_range` throws a warning if the evaluated loss fraction is outside
    the range for a given timestep condition.
    """

    name: str
    applicable_mixture_types: frozenset[propellants.MixtureType]
    target: losses_base.ThrustCoefficientTermTarget

    # Maps each loss_fraction parameter to a dotted attribute path resolved
    # against the timestep conditions.
    timestep_parameter_sources: typing.ClassVar[dict[str, str]] = {}

    # Range (fractions) the loss is expected to fall within
    typical_range: typing.ClassVar[tuple[float, float] | None] = None

    # Must be defined by each subclass
    loss_fraction: typing.ClassVar[typing.Callable[..., float]]

    def _parse_timestep_conditions(
        self, timestep_conditions: simulation_states.TimestepConditions
    ) -> dict[str, typing.Any]:
        """
        Uses `timestep_parameter_sources` to extract params from `timestep_conditions`.

        Example:
            For `timestep_parameter_sources`
            {
                "i_sp_th_frozen": "propellant_properties.i_sp_frozen",
                "chamber_pressure_psi": "chamber_pressure_psi",
            }
            Then return
            {
                "i_sp_th_frozen": timestep_conditions.propellant_properties.i_sp_frozen,
                "chamber_pressure_psi": timestep_conditions.chamber_pressure_psi,
            }
        """
        return {
            parameter: functools.reduce(getattr, path.split("."), timestep_conditions)
            for parameter, path in self.timestep_parameter_sources.items()
        }

    def get_loss_fraction(
        self, timestep_conditions: simulation_states.TimestepConditions
    ) -> float:
        """Return the loss as a fraction in [0, 1] for the timestep conditions."""
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
