from __future__ import annotations

import dataclasses
from collections.abc import Mapping

import machwave.common.fluid_state as fluid_state_models
import machwave.core.two_phase_flow as two_phase_flow


@dataclasses.dataclass(frozen=True, kw_only=True)
class InjectorElement:
    """
    The orifices one propellant line flows through at the injector face.

    An element is a pure function of its own inlet: everything upstream of the
    face is the feed system's to account for. It flows by Dyer's non-homogeneous
    non-equilibrium model, `machwave.core.two_phase_flow.get_dyer_mass_flux`:
    the incompressible orifice flow where nothing flashes, blended with the
    homogeneous equilibrium flow where the liquid is near saturation, as
    self-pressurized nitrous oxide is.

    Attributes:
        discharge_coefficient: Discharge coefficient (dimensionless).
        area: Effective flow area [m^2].
        non_equilibrium_factor: Multiplier on Dyer's non-equilibrium parameter
            kappa (dimensionless). A calibration knob next to the discharge
            coefficient: below 1.0 weights the equilibrium flow, as a long orifice
            does; above 1.0 the incompressible flow; infinite is the incompressible
            flow alone.
    """

    discharge_coefficient: float
    area: float
    non_equilibrium_factor: float = 1.0

    def __post_init__(self) -> None:
        if self.area <= 0.0:
            raise ValueError(f"area must be strictly positive, got {self.area}")
        if not 0.0 < self.discharge_coefficient <= 1.0:
            raise ValueError(
                "discharge_coefficient must be in (0, 1], got "
                f"{self.discharge_coefficient}"
            )
        if not self.non_equilibrium_factor > 0.0:
            raise ValueError(
                "non_equilibrium_factor must be strictly positive, got "
                f"{self.non_equilibrium_factor}"
            )

    def get_mass_flow(
        self,
        *,
        inlet: fluid_state_models.FluidState,
        chamber_pressure: float,
    ) -> float:
        """
        Compute the mass flow rate through this element.

        Args:
            inlet: Propellant state at the injector inlet.
            chamber_pressure: Chamber pressure [Pa].

        Returns:
            Mass flow rate [kg/s]. Zero once the chamber has caught up with the
            inlet, which is where the line stops feeding.
        """
        if inlet.pressure <= chamber_pressure:
            return 0.0

        mass_flux = two_phase_flow.get_dyer_mass_flux(
            fluid_name=inlet.fluid_name,
            temperature_upstream=inlet.temperature,
            density_upstream=inlet.density,
            pressure_upstream=inlet.pressure,
            pressure_downstream=chamber_pressure,
            non_equilibrium_factor=self.non_equilibrium_factor,
        )
        return self.discharge_coefficient * self.area * mass_flux


@dataclasses.dataclass(frozen=True, kw_only=True)
class Injector:
    """
    An injector, with one element per propellant line.

    Attributes:
        elements: Injector element of every line, keyed by the feed system's
            line names.
    """

    elements: dict[str, InjectorElement]

    def __post_init__(self) -> None:
        if not self.elements:
            raise ValueError("elements must hold at least one injector element")

    def get_mass_flows(
        self,
        *,
        inlet_states: Mapping[str, fluid_state_models.FluidState],
        chamber_pressure: float,
    ) -> dict[str, float]:
        """
        Compute the mass flow rate through every element.

        Args:
            inlet_states: Propellant state at the inlet of every line, keyed by
                line name.
            chamber_pressure: Chamber pressure [Pa].

        Returns:
            Mass flow rate of every line [kg/s], keyed by line name.

        Raises:
            ValueError: If any element of the injector has no inlet state.
        """
        missing = [name for name in self.elements if name not in inlet_states]
        if missing:
            raise ValueError(f"no inlet state was given for {missing}")

        return {
            name: element.get_mass_flow(
                inlet=inlet_states[name], chamber_pressure=chamber_pressure
            )
            for name, element in self.elements.items()
        }
