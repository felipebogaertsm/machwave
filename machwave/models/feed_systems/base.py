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

    def get_oxidizer_inlet_state(
        self,
        *,
        oxidizer_mass: float,
        oxidizer_internal_energy: float | None = None,
    ) -> injector_models.InjectorInletState:
        """
        Return the oxidizer state delivered to the injector inlet.

        The tank fluid at the tank temperature and density, at whatever
        pressure survives the path to the injector. A cycle that heats or
        pressurizes the oxidizer on the way, such as one running it through a
        regenerative jacket, overrides this.

        Args:
            oxidizer_mass: Current oxidizer mass in the tank [kg].
            oxidizer_internal_energy: Current internal energy of the oxidizer
                [J]. Required for a tank running an energy balance, unused
                otherwise.
        """
        return injector_models.InjectorInletState(
            fluid_name=self.oxidizer_tank.fluid_name,
            pressure=self.get_oxidizer_tank_pressure(
                oxidizer_mass=oxidizer_mass,
                oxidizer_internal_energy=oxidizer_internal_energy,
            ),
            temperature=self.oxidizer_tank.get_temperature(
                oxidizer_mass, oxidizer_internal_energy
            ),
            density=self.oxidizer_tank.get_density(
                oxidizer_mass, oxidizer_internal_energy
            ),
        )

    def get_fuel_inlet_state(
        self,
        *,
        oxidizer_mass: float,
        fuel_mass: float,
        fuel_internal_energy: float | None = None,
        oxidizer_internal_energy: float | None = None,
    ) -> injector_models.InjectorInletState:
        """
        Return the fuel state delivered to the injector inlet.

        The tank fluid at the tank temperature and density, at whatever
        pressure survives the path to the injector. A cycle that heats or
        pressurizes the fuel on the way, such as one running it through a
        regenerative jacket, overrides this.

        Args:
            oxidizer_mass: Current oxidizer mass in the tank [kg]. Needed
                because some feed systems pressurize the fuel from the oxidizer
                side.
            fuel_mass: Current fuel mass in the tank [kg].
            fuel_internal_energy: Current internal energy of the fuel [J].
                Required for a tank running an energy balance, unused
                otherwise.
            oxidizer_internal_energy: Current internal energy of the oxidizer
                [J]. Required for a tank running an energy balance, unused
                otherwise.
        """
        return injector_models.InjectorInletState(
            fluid_name=self.fuel_tank.fluid_name,
            pressure=self.get_fuel_tank_pressure(
                oxidizer_mass=oxidizer_mass,
                fuel_mass=fuel_mass,
                fuel_internal_energy=fuel_internal_energy,
                oxidizer_internal_energy=oxidizer_internal_energy,
            ),
            temperature=self.fuel_tank.get_temperature(fuel_mass, fuel_internal_energy),
            density=self.fuel_tank.get_density(fuel_mass, fuel_internal_energy),
        )

    @abstractmethod
    def get_oxidizer_tank_pressure(
        self, *, oxidizer_mass: float, oxidizer_internal_energy: float | None = None
    ) -> float:
        """
        Compute and return the oxidizer pressure at the injector inlet [Pa].

        Whatever the feed system takes between the tank and the injector comes
        off here, so the value is what the injector has to push with.

        Args:
            oxidizer_mass: Current oxidizer mass in the tank [kg].
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
        fuel_internal_energy: float | None = None,
        oxidizer_internal_energy: float | None = None,
    ) -> float:
        """
        Compute and return the fuel pressure at the injector inlet [Pa].

        Whatever the feed system takes between the tank and the injector comes
        off here, so the value is what the injector has to push with.

        Args:
            oxidizer_mass: Current oxidizer mass in the tank [kg].
            fuel_mass: Current fuel mass in the tank [kg].
            fuel_internal_energy: Current internal energy of the fuel [J].
                Required for a tank running an energy balance, unused
                otherwise.
            oxidizer_internal_energy: Current internal energy of the oxidizer
                [J]. Required for a tank running an energy balance, unused
                otherwise.
        """
        pass
