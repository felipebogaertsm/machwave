"""
Implementation of the 1976 Standard Atmosphere model.
"""

from fluids.atmosphere import ATMOSPHERE_1976
import numpy as np

from machwave.models.atmosphere import Atmosphere


class Atmosphere1976(Atmosphere):
    """
    Atmospheric model based on the 1976 Standard Atmosphere. This model uses
    the fluids library to calculate the properties of the atmosphere.
    """

    def get_density(self, y_amsl: float) -> float:
        return ATMOSPHERE_1976(y_amsl).rho

    def get_gravity(self, y_amsl: float) -> float:
        return ATMOSPHERE_1976.gravity(y_amsl)

    def get_pressure(self, y_amsl: float) -> float:
        return ATMOSPHERE_1976(y_amsl).P

    def get_sonic_velocity(self, y_amsl: float) -> float:
        return ATMOSPHERE_1976(y_amsl).v_sonic

    def get_wind_velocity(self, y_amsl: float) -> tuple[float, float]:
        """
        7 m/s wind velocity in both x and y directions.
        """
        return (7, 7)

    def get_viscosity(self, y_amsl: float) -> float:
        return ATMOSPHERE_1976(y_amsl).mu


class Atmosphere1976WindPowerLaw(Atmosphere1976):
    """
    Atmospheric model based on the 1976 Standard Atmosphere, using a power-law
    model for wind velocity variation with altitude.
    """

    def __init__(self, v_ref: float, z_ref: float, alpha: float, direction_deg: float):
        """
        Initialize the atmosphere model with power-law wind parameters.

        Args:
            v_ref (float): Wind speed at the reference height (in m/s).
            z_ref (float): Reference height (in meters) where the wind speed is known.
            alpha (float): Wind shear exponent.
            direction_deg (float): Wind direction in degrees (0° is North, 90° is East).
        """
        super().__init__()

        if z_ref == 0:
            raise ValueError("Please provide a non-zero reference height 'z_ref'.")

        self.v_ref = v_ref
        self.z_ref = z_ref
        self.alpha = alpha
        self.direction_deg = direction_deg

    def get_wind_velocity(self, y_amsl: float) -> tuple[float, float]:
        """
        Get the wind velocity components at the given altitude above mean sea level (AMSL)
        using the power law.

        Args:
            y_amsl (float): Altitude above mean sea level in meters.

        Returns:
            tuple[float, float]: Wind velocity components (Northward, Eastward) in m/s.
        """
        if y_amsl <= 0:
            y_amsl = self.z_ref

        wind_speed = self.v_ref * (y_amsl / self.z_ref) ** self.alpha

        direction_rad = np.radians(self.direction_deg)

        v_northward = wind_speed * np.cos(direction_rad)
        v_eastward = wind_speed * np.sin(direction_rad)

        return v_northward, v_eastward
