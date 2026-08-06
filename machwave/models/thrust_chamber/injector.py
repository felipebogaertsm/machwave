from __future__ import annotations

import dataclasses
import enum
from collections.abc import Mapping

import machwave.common.fluid_state as fluid_state_models
import machwave.core.incompressible_flow as incompressible_flow
import machwave.core.two_phase_flow as two_phase_flow


class MassFlowModel(enum.StrEnum):
    """
    Models for computing mass flow through an injector orifice.

    SPI: Single-phase incompressible orifice equation. Valid for subcooled liquid
        propellants.
    HEM: Homogeneous-equilibrium two-phase model. Required for self-pressurized
        propellants such as nitrous oxide, where flow can choke at the injector due to
        flash boiling.
    """

    SPI = "spi"
    HEM = "hem"


@dataclasses.dataclass(frozen=True, kw_only=True)
class InjectorElement:
    """
    The orifices one propellant line flows through at the injector face.

    An element is a pure function of its own inlet: everything upstream of the
    face is the feed system's to account for.

    Attributes:
        discharge_coefficient: Discharge coefficient (dimensionless).
        area: Effective flow area [m^2].
        mass_flow_model: Model the orifice flow is computed with.
    """

    discharge_coefficient: float
    area: float
    mass_flow_model: MassFlowModel = MassFlowModel.SPI

    def __post_init__(self) -> None:
        if self.area <= 0.0:
            raise ValueError(f"area must be strictly positive, got {self.area}")
        if not 0.0 < self.discharge_coefficient <= 1.0:
            raise ValueError(
                "discharge_coefficient must be in (0, 1], got "
                f"{self.discharge_coefficient}"
            )

        object.__setattr__(self, "mass_flow_model", MassFlowModel(self.mass_flow_model))

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

        Raises:
            ValueError: If the mass flow model is unsupported.
        """
        if inlet.pressure <= chamber_pressure:
            return 0.0

        if self.mass_flow_model == MassFlowModel.HEM:
            mass_flux = two_phase_flow.get_homogeneous_equilibrium_mass_flux(
                fluid_name=inlet.fluid_name,
                temperature_upstream=inlet.temperature,
                pressure_downstream=chamber_pressure,
                pressure_upstream=inlet.pressure,
            )
            return self.discharge_coefficient * self.area * mass_flux
        elif self.mass_flow_model == MassFlowModel.SPI:
            return incompressible_flow.get_mass_flow_orifice(
                discharge_coefficient=self.discharge_coefficient,
                area=self.area,
                density=inlet.density,
                pressure_upstream=inlet.pressure,
                pressure_downstream=chamber_pressure,
            )

        raise ValueError(f"Unsupported mass flow model: {self.mass_flow_model}")


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
