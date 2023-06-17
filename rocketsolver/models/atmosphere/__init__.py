from abc import ABC, abstractmethod

from fluids.atmosphere import ATMOSPHERE_1976


class Atmosphere(ABC):
    """Abstract class that represents an atmospheric model."""

    @abstractmethod
    def get_density(self, y_amsl: float) -> float:
        """
        Get the air density at the given altitude above mean sea level (AMSL).

        Args:
            y_amsl (float): Altitude above mean sea level in meters.

        Returns:
            float: Air density in kg/m^3.
        """
        pass

    @abstractmethod
    def get_gravity(self, y_amsl: float) -> float:
        """
        Get the acceleration due to gravity at the given altitude above mean
        sea level (AMSL).

        Args:
            y_amsl (float): Altitude above mean sea level in meters.

        Returns:
            float: Acceleration due to gravity in m/s^2.
        """
        pass

    @abstractmethod
    def get_pressure(self, y_amsl: float) -> float:
        """
        Get the air pressure at the given altitude above mean sea level (AMSL).

        Args:
            y_amsl (float): Altitude above mean sea level in meters.

        Returns:
            float: Air pressure in Pascal (Pa).
        """
        pass

    @abstractmethod
    def get_sonic_velocity(self, y_amsl: float) -> float:
        """
        Get the speed of sound in air at the given altitude above mean sea
        level (AMSL).

        Args:
            y_amsl (float): Altitude above mean sea level in meters.

        Returns:
            float: Speed of sound in m/s.
        """
        pass

    @abstractmethod
    def get_wind_velocity(self, y_amsl: float) -> tuple[float, float]:
        """
        Get the wind velocity components at the given altitude above mean
        sea level (AMSL).

        Args:
            y_amsl (float): Altitude above mean sea level in meters.

        Returns:
            tuple[float, float]: Wind velocity components (u, v) in m/s.
        """
        pass

    @abstractmethod
    def get_viscosity(self, y_amsl: float) -> float:
        """
        Get the dynamic viscosity of air at the given altitude above mean sea
        level (AMSL).

        Args:
            y_amsl (float): Altitude above mean sea level in meters.

        Returns:
            float: Dynamic viscosity of air in Pascal-second (Pa-s).
        """
        pass


class Atmosphere1976(Atmosphere):
    def get_density(self, y_amsl: float) -> float:
        """
        Get the air density using the AMSL elevation and the fluids library.

        Args:
            y_amsl (float): Altitude above mean sea level in meters.

        Returns:
            float: Air density in kg/m^3.
        """
        return ATMOSPHERE_1976(y_amsl).rho

    def get_gravity(self, y_amsl: float) -> float:
        """
        Get the gravity using the AMSL elevation and the fluids library.

        Args:
            y_amsl (float): Altitude above mean sea level in meters.

        Returns:
            float: Acceleration due to gravity in m/s^2.
        """
        return ATMOSPHERE_1976.gravity(y_amsl)

    def get_pressure(self, y_amsl: float) -> float:
        """
        Get the air pressure using the AMSL elevation and the fluids library.

        Args:
            y_amsl (float): Altitude above mean sea level in meters.

        Returns:
            float: Air pressure in Pascal (Pa).
        """
        return ATMOSPHERE_1976(y_amsl).P

    def get_sonic_velocity(self, y_amsl: float) -> float:
        """
        Get the speed of sound in air using the AMSL elevation and the fluids
        library.

        Args:
            y_amsl (float): Altitude above mean sea level in meters.

        Returns:
            float: Speed of sound in m/s.
        """
        return ATMOSPHERE_1976(y_amsl).v_sonic

    def get_wind_velocity(
        self, y_amsl: float, *args, **kwargs
    ) -> tuple[float, float]:
        """
        Get the wind velocity components at the given altitude above mean sea
        level (AMSL).

        Note:
            Returning a fixed wind velocity for now. Not representative of an
            actual atmosphere.

        Args:
            y_amsl (float): Altitude above mean sea level in meters.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            tuple[float, float]: Wind velocity components (u, v) in m/s.
        """
        return (10, 10)

    def get_viscosity(self, y_amsl: float) -> float:
        """
        Get the dynamic viscosity of air using the AMSL elevation and the
        fluids library.

        Args:
            y_amsl (float): Altitude above mean sea level in meters.

        Returns:
            float: Dynamic viscosity of air in Pascal-second (Pa-s).
        """
        return ATMOSPHERE_1976(y_amsl).mu  # Pa-s
