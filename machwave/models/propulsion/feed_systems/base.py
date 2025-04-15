from abc import ABC, abstractmethod
from machwave.models.propulsion.feed_systems.tanks.base import Tank


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
