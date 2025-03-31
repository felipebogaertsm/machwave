from abc import ABC, abstractmethod


class FeedSystem(ABC):
    """
    Abstract base class for a bipropellant feed system in a liquid rocket
    engine (LRE).

    This class is responsible for determining oxidizer and fuel mass flows as a
    function of tank/pressurant states, pumps (if any), and current chamber
    conditions. Subclasses must implement the abstract methods to specify the
    actual flow calculations.
    """

    @abstractmethod
    def get_mass_flow_ox(self, *args, **kwargs) -> float:
        """
        Returns the current oxidizer mass flow rate [kg/s].
        """
        pass

    @abstractmethod
    def get_mass_flow_fuel(self, *args, **kwargs) -> float:
        """
        Returns the current fuel mass flow rate [kg/s].
        """
        pass
