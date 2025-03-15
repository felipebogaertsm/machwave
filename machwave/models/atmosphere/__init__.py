"""
Atmospheric models for use in rocket simulations. The models are used to
calculate the properties of the atmosphere at a given altitude above mean sea
level (AMSL).
"""

from abc import abstractmethod


class Atmosphere:
    """Abstract class that represents an atmospheric model."""

    @abstractmethod
    def get_density(self, y_amsl: float) -> float:
        """
        Get the air density at the given altitude above mean sea level (AMSL).

        Args:
            y_amsl: Altitude above mean sea level in meters.

        Returns:
            Air density in kg/m^3.
        """

    @abstractmethod
    def get_gravity(self, y_amsl: float) -> float:
        """
        Get the acceleration due to gravity at the given altitude above mean
        sea level (AMSL).

        Args:
            y_amsl: Altitude above mean sea level in meters.

        Returns:
            Acceleration due to gravity in m/s^2.
        """

    @abstractmethod
    def get_pressure(self, y_amsl: float) -> float:
        """
        Get the air pressure at the given altitude above mean sea level (AMSL).

        Args:
            y_amsl: Altitude above mean sea level in meters.

        Returns:
            Air pressure in Pascal (Pa).
        """

    @abstractmethod
    def get_sonic_velocity(self, y_amsl: float) -> float:
        """
        Get the speed of sound in air at the given altitude above mean sea
        level (AMSL).

        Args:
            y_amsl: Altitude above mean sea level in meters.

        Returns:
            Speed of sound in m/s.
        """

    @abstractmethod
    def get_wind_velocity(self, y_amsl: float) -> tuple[float, float]:
        """
        Get the wind velocity components at the given altitude above mean
        sea level (AMSL).

        Args:
            y_amsl: Altitude above mean sea level in meters.

        Returns:
            Wind velocity components (Northward, Eastward) in m/s.
        """

    @abstractmethod
    def get_viscosity(self, y_amsl: float) -> float:
        """
        Get the dynamic viscosity of air at the given altitude above mean sea
        level (AMSL).

        Args:
            y_amsl: Altitude above mean sea level in meters.

        Returns:
            Dynamic viscosity of air in Pascal-second (Pa-s).
        """
