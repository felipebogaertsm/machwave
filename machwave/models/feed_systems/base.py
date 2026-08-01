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
        oxidizer_internal_energy: float | None = None,
    ) -> float:
        """
        Compute and return the current oxidizer mass flow rate [kg/s].

        Args:
            chamber_pressure: Chamber pressure [Pa].
            injector: Bipropellant injector handling the orifice dispatch.
            oxidizer_mass: Current oxidizer mass in the tank [kg].
            oxidizer_internal_energy: Current internal energy of the oxidizer
                [J]. Required for a tank running an energy balance, unused
                otherwise.

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
        fuel_internal_energy: float | None = None,
        oxidizer_internal_energy: float | None = None,
    ) -> float:
        """
        Compute and return the current fuel mass flow rate [kg/s].

        Args:
            chamber_pressure: Chamber pressure [Pa].
            injector: Bipropellant injector handling the orifice dispatch.
            fuel_mass: Current fuel mass in the tank [kg].
            oxidizer_mass: Current oxidizer mass in the tank [kg]. Needed because
                some feed systems pressurize the fuel from the oxidizer side.
            fuel_internal_energy: Current internal energy of the fuel [J].
                Required for a tank running an energy balance, unused
                otherwise.
            oxidizer_internal_energy: Current internal energy of the oxidizer
                [J]. Required for a tank running an energy balance, unused
                otherwise.

        Returns:
            Fuel mass flow rate [kg/s].
        """
        pass

    @abstractmethod
    def get_oxidizer_tank_pressure(
        self,
        *,
        oxidizer_mass: float,
        mass_flow_rate: float = 0.0,
        oxidizer_internal_energy: float | None = None,
    ) -> float:
        """
        Compute and return the oxidizer pressure at the injector inlet [Pa].

        Whatever the feed system takes between the tank and the injector comes
        off here, so the value is what the injector has to push with.

        Args:
            oxidizer_mass: Current oxidizer mass in the tank [kg].
            mass_flow_rate: Oxidizer flow drawn from the tank [kg/s]. Losses
                that grow with the flow vanish at the default of no flow,
                leaving the resting pressure.
            oxidizer_internal_energy: Current internal energy of the oxidizer
                [J]. Required for a tank running an energy balance, unused
                otherwise.
        """
        pass

    @abstractmethod
    def get_fuel_tank_pressure(
        self,
        *,
        oxidizer_mass: float,
        fuel_mass: float,
        mass_flow_rate: float = 0.0,
        fuel_internal_energy: float | None = None,
        oxidizer_internal_energy: float | None = None,
    ) -> float:
        """
        Compute and return the fuel pressure at the injector inlet [Pa].

        Args:
            oxidizer_mass: Current oxidizer mass in the tank [kg].
            fuel_mass: Current fuel mass in the tank [kg].
            mass_flow_rate: Fuel flow drawn from the tank [kg/s]. Losses that
                grow with the flow vanish at the default of no flow, leaving
                the resting pressure.
            fuel_internal_energy: Current internal energy of the fuel [J].
                Required for a tank running an energy balance, unused
                otherwise.
            oxidizer_internal_energy: Current internal energy of the oxidizer
                [J]. Required for a tank running an energy balance, unused
                otherwise.
        """
        pass
