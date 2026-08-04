from __future__ import annotations

import enum

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


class BipropellantInjector:
    """
    A simple injector class for a biliquid rocket engine.

    Each side is fed a stagnation state at the injector face. What the orifice
    sees is all the injector needs, so anything upstream of the face is the
    feed system's to account for.
    """

    def __init__(
        self,
        discharge_coefficient_fuel: float,
        discharge_coefficient_oxidizer: float,
        area_fuel: float,
        area_ox: float,
        mass_flow_model_fuel: MassFlowModel = MassFlowModel.SPI,
        mass_flow_model_oxidizer: MassFlowModel = MassFlowModel.SPI,
    ):
        """
        Initialize an Injector instance.

        Args:
            discharge_coefficient_fuel:
                Discharge coefficient for the fuel side (dimensionless).
            discharge_coefficient_oxidizer:
                Discharge coefficient for the oxidizer side (dimensionless).
            area_fuel:
                Effective flow area of the fuel injector [m^2].
            area_ox:
                Effective flow area of the oxidizer injector [m^2].
            mass_flow_model_fuel:
                Mass flow model for the fuel side.
            mass_flow_model_oxidizer:
                Mass flow model for the oxidizer side.
        """
        self.discharge_coefficient_fuel = discharge_coefficient_fuel
        self.discharge_coefficient_oxidizer = discharge_coefficient_oxidizer
        self.area_fuel = area_fuel
        self.area_ox = area_ox
        self.mass_flow_model_fuel = MassFlowModel(mass_flow_model_fuel)
        self.mass_flow_model_oxidizer = MassFlowModel(mass_flow_model_oxidizer)

        self._validate()

    def _validate(self) -> None:
        """
        Validate the injector inputs.

        Raises:
            ValueError: If any field is outside its valid physical range.
        """
        if self.area_fuel <= 0.0:
            raise ValueError(
                f"area_fuel must be strictly positive, got {self.area_fuel}"
            )
        if self.area_ox <= 0.0:
            raise ValueError(f"area_ox must be strictly positive, got {self.area_ox}")
        if not 0.0 < self.discharge_coefficient_fuel <= 1.0:
            raise ValueError(
                "discharge_coefficient_fuel must be in (0, 1], got "
                f"{self.discharge_coefficient_fuel}"
            )
        if not 0.0 < self.discharge_coefficient_oxidizer <= 1.0:
            raise ValueError(
                "discharge_coefficient_oxidizer must be in (0, 1], got "
                f"{self.discharge_coefficient_oxidizer}"
            )

    def get_mass_flow_fuel(
        self,
        *,
        inlet: fluid_state_models.FluidState,
        chamber_pressure: float,
    ) -> float:
        """
        Compute the fuel-side mass flow rate through this injector.

        Args:
            inlet: Fuel state at the injector inlet.
            chamber_pressure: Chamber pressure [Pa].

        Returns:
            Fuel mass flow rate [kg/s].
        """
        return self._get_mass_flow(
            inlet=inlet,
            chamber_pressure=chamber_pressure,
            discharge_coefficient=self.discharge_coefficient_fuel,
            injector_area=self.area_fuel,
            mass_flow_model=self.mass_flow_model_fuel,
        )

    def get_mass_flow_ox(
        self,
        *,
        inlet: fluid_state_models.FluidState,
        chamber_pressure: float,
    ) -> float:
        """
        Compute the oxidizer-side mass flow rate through this injector.

        Args:
            inlet: Oxidizer state at the injector inlet.
            chamber_pressure: Chamber pressure [Pa].

        Returns:
            Oxidizer mass flow rate [kg/s].
        """
        return self._get_mass_flow(
            inlet=inlet,
            chamber_pressure=chamber_pressure,
            discharge_coefficient=self.discharge_coefficient_oxidizer,
            injector_area=self.area_ox,
            mass_flow_model=self.mass_flow_model_oxidizer,
        )

    @staticmethod
    def _get_mass_flow(
        *,
        inlet: fluid_state_models.FluidState,
        chamber_pressure: float,
        discharge_coefficient: float,
        injector_area: float,
        mass_flow_model: MassFlowModel,
    ) -> float:
        """
        Dispatch a mass flow calculation through the requested model.

        Args:
            inlet: Propellant state at the injector inlet.
            chamber_pressure: Chamber pressure [Pa].
            discharge_coefficient: Discharge coefficient (dimensionless).
            injector_area: Effective flow area [m^2].
            mass_flow_model: Mass flow model for this side.

        Returns:
            Mass flow rate [kg/s].
        """
        if mass_flow_model == MassFlowModel.HEM:
            mass_flux = two_phase_flow.get_homogeneous_equilibrium_mass_flux(
                fluid_name=inlet.fluid_name,
                temperature_upstream=inlet.temperature,
                pressure_downstream=chamber_pressure,
                pressure_upstream=inlet.pressure,
            )
            return discharge_coefficient * injector_area * mass_flux
        elif mass_flow_model == MassFlowModel.SPI:
            return incompressible_flow.get_mass_flow_orifice(
                discharge_coefficient=discharge_coefficient,
                area=injector_area,
                density=inlet.density,
                pressure_upstream=inlet.pressure,
                pressure_downstream=chamber_pressure,
            )

        raise ValueError(f"Unsupported mass flow model: {mass_flow_model}")
