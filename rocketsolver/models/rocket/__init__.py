from abc import ABC, abstractmethod
from rocketsolver.models.rocket.fuselage import Fuselage
from rocketsolver.models.propulsion import Motor
from rocketsolver.models.recovery import Recovery


class RocketBaseClass(ABC):
    """
    Base class for a Rocket.
    """

    def __init__(
        self,
        propulsion: Motor,
        recovery: Recovery,
        fuselage: Fuselage,
    ) -> None:
        """
        Initializes a RocketBaseClass object.

        Args:
            propulsion (Motor): The motor or propulsion system of the rocket.
            recovery (Recovery): The recovery system of the rocket.
            fuselage (Fuselage): The fuselage or body of the rocket.
        """
        self.propulsion = propulsion
        self.recovery = recovery
        self.fuselage = fuselage

    @abstractmethod
    def get_launch_mass(self) -> float:
        """
        Calculates the total mass of the rocket at launch.

        Returns:
            float: The total mass of the rocket at launch, in kg.
        """
        pass

    @abstractmethod
    def get_dry_mass(self) -> float:
        """
        Calculates the dry mass of the rocket.

        Returns:
            float: The dry mass of the rocket, in kg.
        """
        pass


class Rocket(RocketBaseClass):
    def __init__(
        self,
        propulsion: Motor,
        recovery: Recovery,
        fuselage: Fuselage,
        mass_without_motor: float,
    ) -> None:
        """
        Initializes a Rocket object.

        Args:
            propulsion (Motor): The motor or propulsion system of the rocket.
            recovery (Recovery): The recovery system of the rocket.
            fuselage (Fuselage): The fuselage or body of the rocket.
            mass_without_motor (float): The mass of the rocket without the motor, in kg.
        """
        super().__init__(
            propulsion=propulsion,
            recovery=recovery,
            fuselage=fuselage,
        )
        self.mass_without_motor = mass_without_motor

    def get_launch_mass(self) -> float:
        """
        Calculates the total mass of the rocket at launch.

        Returns:
            float: The total mass of the rocket at launch, in kg.
        """
        return self.mass_without_motor + self.propulsion.get_launch_mass()

    def get_dry_mass(self) -> float:
        """
        Calculates the dry mass of the rocket.

        Returns:
            float: The dry mass of the rocket, in kg.
        """
        return self.mass_without_motor + self.propulsion.get_dry_mass()
