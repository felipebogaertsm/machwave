"""
Implementation of the 1976 Standard Atmosphere model.
"""

from fluids.atmosphere import ATMOSPHERE_1976

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
        TODO: Implement wind velocity calculation.
        """
        return (10, 10)

    def get_viscosity(self, y_amsl: float) -> float:
        return ATMOSPHERE_1976(y_amsl).mu
