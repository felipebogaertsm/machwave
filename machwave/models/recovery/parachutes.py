from abc import ABC, abstractmethod

from machwave.services.math.geometric import (
    get_circle_area,
    get_torus_area,
)


class Parachute(ABC):
    """
    Base class for implementing different parachute geometries using the
    Strategy design pattern.

    Subclasses should inherit from Parachute and override its methods to
    customize the behavior for specific parachute geometries.
    """

    def __init__(self) -> None:
        pass

    @property
    @abstractmethod
    def drag_coefficient(self) -> float:
        """
        The drag coefficient of the parachute.
        Subclasses must override this property to provide the appropriate drag
        coefficient value.
        """
        pass

    @property
    @abstractmethod
    def area(self) -> float:
        """
        The area of the parachute.
        Subclasses must override this property to provide the appropriate area
        value.
        """
        pass


class HemisphericalParachute(Parachute):
    def __init__(self, diameter) -> None:
        """
        Initializes a HemisphericalParachute object.

        Args:
            diameter (float): The diameter of the parachute.
        """
        super().__init__()
        self.diameter = diameter

    @property
    def drag_coefficient(self) -> float:
        """
        The drag coefficient of the hemispherical parachute.

        Returns:
            float: The drag coefficient value for the hemispherical parachute.
        """
        return 0.71

    @property
    def area(self) -> float:
        """
        The area of the hemispherical parachute.

        Returns:
            float: The area value for the hemispherical parachute.
        """
        return get_circle_area(self.diameter)


class ToroidalParachute(Parachute):
    def __init__(self, major_radius: float, minor_radius: float) -> None:
        """
        Initializes a ToroidalParachute object.

        Args:
            major_radius (float): The major radius of the toroidal parachute.
            minor_radius (float): The minor radius of the toroidal parachute.
        """
        super().__init__()
        self.major_radius = major_radius
        self.minor_radius = minor_radius

    @property
    def drag_coefficient(self) -> float:
        """
        The drag coefficient of the toroidal parachute.

        Returns:
            float: The drag coefficient value for the toroidal parachute.
        """
        return 0.85

    @property
    def area(self) -> float:
        """
        The area of the toroidal parachute.

        Returns:
            float: The area value for the toroidal parachute.
        """
        return get_torus_area(self.major_radius, self.minor_radius)
