from abc import ABC, abstractmethod


class Tank(ABC):
    """Abstract base class for a propellant tank model.

    Defines the interface for obtaining tank pressure and removing propellant mass.
    """

    @abstractmethod
    def get_pressure(self) -> float:
        """Returns the current tank pressure [Pa].

        Returns:
            float: The current absolute pressure in the tank [Pa].
        """
        pass

    @abstractmethod
    def remove_propellant(self, mass: float) -> None:
        """Removes a specified mass of propellant from the tank.

        Args:
            mass (float): The mass of propellant to remove [kg].
        """
        pass
