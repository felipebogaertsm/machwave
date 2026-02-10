from abc import ABC, abstractmethod

from machwave.core.geometric import (
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
        """Initialize a HemisphericalParachute object.

        Args:
            diameter: Parachute diameter [m].
        """
        super().__init__()
        self.diameter = diameter

    @property
    def drag_coefficient(self) -> float:
        """Drag coefficient of the hemispherical parachute."""
        return 0.71

    @property
    def area(self) -> float:
        """Area of the hemispherical parachute [m^2]."""
        return get_circle_area(self.diameter)


class ToroidalParachute(Parachute):
    def __init__(self, major_radius: float, minor_radius: float) -> None:
        """Initialize a ToroidalParachute object.

        Args:
            major_radius: Major radius of the toroidal parachute [m].
            minor_radius: Minor radius of the toroidal parachute [m].
        """
        super().__init__()
        self.major_radius = major_radius
        self.minor_radius = minor_radius

    @property
    def drag_coefficient(self) -> float:
        """Drag coefficient of the toroidal parachute."""
        return 0.85

    @property
    def area(self) -> float:
        """Area of the toroidal parachute [m^2]."""
        return get_torus_area(self.major_radius, self.minor_radius)
