from abc import ABC, abstractmethod

import machwave.models.feed_systems.tanks as tanks
import machwave.models.thrust_chamber.injector as injector_models


class FeedSystem(ABC):
    """Abstract base class for a bipropellant feed system in a biliquid rocket engine."""

    def __init__(self, fuel_tank: tanks.Tank, oxidizer_tank: tanks.Tank):
        """
        Initialize the FeedSystem with associated tank objects.

        Args:
            fuel_tank: Instance representing the fuel tank.
            oxidizer_tank: Instance representing the oxidizer tank.
        """
        self.fuel_tank = fuel_tank
        self.oxidizer_tank = oxidizer_tank

    def get_propellant_mass(self) -> float:
        """Compute and return the initial propellant mass in the system [kg]."""
        return self.fuel_tank.fluid_mass + self.oxidizer_tank.fluid_mass

    @abstractmethod
    def get_mass_flow_ox(
        self,
        chamber_pressure: float,
        *,
        injector: injector_models.BipropellantInjector,
    ) -> float:
        """
        Compute and return the current oxidizer mass flow rate [kg/s].

        Args:
            chamber_pressure: Chamber pressure [Pa].
            injector: Bipropellant injector handling the orifice dispatch.

        Returns:
            Oxidizer mass flow rate [kg/s].
        """
        pass

    @abstractmethod
    def get_mass_flow_fuel(
        self,
        chamber_pressure: float,
        *,
        injector: injector_models.BipropellantInjector,
    ) -> float:
        """
        Compute and return the current fuel mass flow rate [kg/s].

        Args:
            chamber_pressure: Chamber pressure [Pa].
            injector: Bipropellant injector handling the orifice dispatch.

        Returns:
            Fuel mass flow rate [kg/s].
        """
        pass

    @abstractmethod
    def get_oxidizer_tank_pressure(self) -> float:
        """Compute and return the current oxidizer tank pressure [Pa]."""
        pass

    @abstractmethod
    def get_fuel_tank_pressure(self) -> float:
        """Compute and return the current fuel tank pressure [Pa]."""
        pass
