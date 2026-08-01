from abc import ABC, abstractmethod

import machwave.models.feed_systems.tank as tank
import machwave.models.thrust_chamber.injector as injector_models


class FeedSystem(ABC):
    """Abstract base class for a bipropellant feed system in a biliquid rocket engine."""

    def __init__(self, fuel_tank: tank.Tank, oxidizer_tank: tank.Tank):
        """
        Initialize the FeedSystem with associated tank objects.

        Args:
            fuel_tank: Instance representing the fuel tank.
            oxidizer_tank: Instance representing the oxidizer tank.
        """
        self.fuel_tank = fuel_tank
        self.oxidizer_tank = oxidizer_tank

    def get_initial_propellant_mass(self) -> float:
        """Compute and return the initial propellant mass in the system [kg]."""
        return self.fuel_tank.initial_fluid_mass + self.oxidizer_tank.initial_fluid_mass

    @abstractmethod
    def get_mass_flow_ox(
        self,
        chamber_pressure: float,
        *,
        injector: injector_models.BipropellantInjector,
        oxidizer_mass: float,
    ) -> float:
        """
        Compute and return the current oxidizer mass flow rate [kg/s].

        Args:
            chamber_pressure: Chamber pressure [Pa].
            injector: Bipropellant injector handling the orifice dispatch.
            oxidizer_mass: Current oxidizer mass in the tank [kg].

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
        fuel_mass: float,
        oxidizer_mass: float,
    ) -> float:
        """
        Compute and return the current fuel mass flow rate [kg/s].

        Args:
            chamber_pressure: Chamber pressure [Pa].
            injector: Bipropellant injector handling the orifice dispatch.
            fuel_mass: Current fuel mass in the tank [kg].
            oxidizer_mass: Current oxidizer mass in the tank [kg]. Needed because
                some feed systems pressurize the fuel from the oxidizer side.

        Returns:
            Fuel mass flow rate [kg/s].
        """
        pass

    @abstractmethod
    def get_oxidizer_tank_pressure(self, *, oxidizer_mass: float) -> float:
        """
        Compute and return the oxidizer pressure at the injector inlet [Pa].

        Whatever the feed system takes between the tank and the injector comes
        off here, so the value is what the injector has to push with.

        Args:
            oxidizer_mass: Current oxidizer mass in the tank [kg].
        """
        pass

    @abstractmethod
    def get_fuel_tank_pressure(
        self, *, oxidizer_mass: float, fuel_mass: float
    ) -> float:
        """
        Compute and return the fuel pressure at the injector inlet [Pa].

        Whatever the feed system takes between the tank and the injector comes
        off here, so the value is what the injector has to push with.

        Args:
            oxidizer_mass: Current oxidizer mass in the tank [kg].
            fuel_mass: Current fuel mass in the tank [kg].
        """
        pass
