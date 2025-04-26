from abc import ABC, abstractmethod

from machwave.models.propulsion.feed_systems.tanks import Tank


class FeedSystem(ABC):
    """
    Abstract base class for a bipropellant feed system in a liquid rocket engine (LRE).

    This class is responsible for determining oxidizer and fuel mass flows as a function of tank/pressurant states,
    pumps (if any), and current chamber conditions. Subclasses must implement the abstract methods to specify the
    actual flow calculations.
    """

    def __init__(self, fuel_tank: Tank, oxidizer_tank: Tank):
        """
        Initialize the FeedSystem with associated tank objects.

        Args:
            fuel_tank (Tank): An instance representing the fuel tank.
            oxidizer_tank (Tank): An instance representing the oxidizer tank.
        """
        self.fuel_tank = fuel_tank
        self.oxidizer_tank = oxidizer_tank

    def get_propellant_mass(self) -> float:
        """
        Compute and return the initial propellant mass in the system.

        Returns:
            float: The initial propellant mass in kilograms (kg).
        """
        return self.fuel_tank.fluid_mass + self.oxidizer_tank.fluid_mass

    @abstractmethod
    def get_mass_flow_ox(self, *args, **kwargs) -> float:
        """
        Compute and return the current oxidizer mass flow rate.

        Returns:
            float: The oxidizer mass flow rate in kilograms per second (kg/s).
        """
        pass

    @abstractmethod
    def get_mass_flow_fuel(self, *args, **kwargs) -> float:
        """
        Compute and return the current fuel mass flow rate.

        Returns:
            float: The fuel mass flow rate in kilograms per second (kg/s).
        """
        pass

    @abstractmethod
    def get_oxidizer_tank_pressure(self) -> float:
        """
        Compute and return the current oxidizer tank pressure.

        Returns:
            float: The oxidizer tank pressure in pascals (Pa).
        """
        pass

    @abstractmethod
    def get_fuel_tank_pressure(self) -> float:
        """
        Compute and return the current fuel tank pressure.

        Returns:
            float: The fuel tank pressure in pascals (Pa).
        """
        pass
