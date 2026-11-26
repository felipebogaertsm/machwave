from __future__ import annotations

import dataclasses
import math
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
        saturated_inlet_flux_maximum: tuple[float, float] | None = None,
        vapor_pressure: float | None = None,
    ) -> float:
        """
        Compute the mass flow rate through this element.

        Args:
            inlet: Propellant state at the injector inlet.
            chamber_pressure: Chamber pressure [Pa].
            saturated_inlet_flux_maximum: Result of
                `get_saturated_inlet_flux_maximum` at the inlet temperature and
                chamber pressure. If `None`, it is computed when needed.
            vapor_pressure: Result of `get_vapor_pressure` at the inlet
                temperature. If `None`, it is looked up when needed.

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
            saturated_inlet_flux_maximum=saturated_inlet_flux_maximum,
            vapor_pressure=vapor_pressure,
        )
        return self.discharge_coefficient * self.area * mass_flux

    def get_vapor_pressure(
        self, *, fluid_name: str, temperature: float
    ) -> float | None:
        """
        Compute the vapor pressure every inlet at the given temperature shares.

        Args:
            fluid_name: CoolProp fluid name.
            temperature: Inlet temperature [K].

        Returns:
            Saturation pressure [Pa]. `None` if the non-equilibrium factor is
            infinite or the temperature is at or above the critical temperature,
            where the flow needs no vapor pressure.
        """
        if math.isinf(self.non_equilibrium_factor):
            return None
        import machwave.services.coolprop as coolprop_service

        coolprop = coolprop_service.CoolPropService(fluid_name)
        if temperature >= coolprop.get_critical_temperature():
            return None
        return coolprop.get_saturation_pressure(temperature)

    def get_saturated_inlet_flux_maximum(
        self,
        *,
        fluid_name: str,
        temperature: float,
        chamber_pressure: float,
        vapor_pressure: float | None = None,
    ) -> tuple[float, float] | None:
        """
        Compute the equilibrium flux maximum shared by saturated inlets.

        Every saturated inlet at the given temperature and chamber pressure reuses it
        through `get_mass_flow`, whatever its pressure.

        Args:
            fluid_name: CoolProp fluid name.
            temperature: Inlet temperature [K].
            chamber_pressure: Chamber pressure [Pa].
            vapor_pressure: Result of `get_vapor_pressure` at the temperature. If
                `None`, it is looked up when needed.

        Returns:
            Mass flux [kg/(m^2-s)] and the pressure it occurs at [Pa], from
            `machwave.core.two_phase_flow.get_saturated_inlet_flux_maximum`.
            `None` if the non-equilibrium factor is infinite, the temperature is at or
            above the critical temperature, or the chamber is at or above the
            saturation pressure.
        """
        if math.isinf(self.non_equilibrium_factor):
            return None
        import machwave.services.coolprop as coolprop_service

        coolprop = coolprop_service.CoolPropService(fluid_name)
        if temperature >= coolprop.get_critical_temperature():
            return None
        if vapor_pressure is None:
            vapor_pressure = coolprop.get_saturation_pressure(temperature)
        if chamber_pressure >= vapor_pressure:
            return None
        return two_phase_flow.get_saturated_inlet_flux_maximum(
            fluid_name, temperature, chamber_pressure
        )


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
        saturated_inlet_flux_maxima: (
            Mapping[str, tuple[float, float] | None] | None
        ) = None,
        vapor_pressures: Mapping[str, float | None] | None = None,
    ) -> dict[str, float]:
        """
        Compute the mass flow rate through every element.

        Args:
            inlet_states: Propellant state at the inlet of every line, keyed by
                line name.
            chamber_pressure: Chamber pressure [Pa].
            saturated_inlet_flux_maxima: Result of
                `InjectorElement.get_saturated_inlet_flux_maximum` of every line,
                keyed by line name. A line left out computes it when needed.
            vapor_pressures: Result of `InjectorElement.get_vapor_pressure` of
                every line, keyed by line name. A line left out looks it up when
                needed.

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
                inlet=inlet_states[name],
                chamber_pressure=chamber_pressure,
                saturated_inlet_flux_maximum=(saturated_inlet_flux_maxima or {}).get(
                    name
                ),
                vapor_pressure=(vapor_pressures or {}).get(name),
            )
            for name, element in self.elements.items()
        }
