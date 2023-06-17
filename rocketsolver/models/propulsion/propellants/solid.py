from abc import ABC
from dataclasses import dataclass

import scipy.constants

from . import Propellant


class BurnRateOutOfBoundsError(Exception):
    """
    Exception raised when the chamber pressure is out of the burn rate range.

    This exception is raised when the chamber pressure provided is outside the
    valid burn rate range for a specific solid propellant.

    Attributes:
        value (float): The chamber pressure that caused the error.
        message (str): The error message.
    """

    def __init__(self, value: float) -> None:
        self.value = value
        self.message = (
            f"Chamber pressure out of bounds: {value * 1e-6:.2f} MPa"
        )

        super().__init__(self.message)


@dataclass
class SolidPropellant(Propellant):
    """
    Class that stores solid propellant data.

    This class represents a specific type of propellant, SolidPropellant, which
    inherits properties from the Propellant base class. It provides attributes to
    store the data related to a solid propellant, such as burn rate information,
    combustion efficiency, density, isentropic exponents, molar weights, specific
    impulses, and more.

    The burn rate data is described using a list of dictionaries, where each
    dictionary contains the minimum and maximum chamber pressure values, the burn
    rate coefficient 'a', and the burn rate exponent 'n'. The burn rate coefficients
    can vary with the chamber pressure, and the list must be ordered by increasing
    minimum chamber pressure.

    Inherits:
        Propellant: Base class representing a propellant.

    Attributes:
        burn_rate (list[dict[str, float | int]]): Burn rate information list.
            Each dictionary in the list describes the burn rate behavior within a
            specific chamber pressure range.
        combustion_efficiency (float): Combustion efficiency (0 to 1).
        density (float): Propellant density [kg/m^3].
        k_mix_ch (float): Isentropic exponent (chamber).
        k_2ph_ex (float): Isentropic exponent (exhaust).
        T0_ideal (float): Ideal combustion temperature [K].
        M_ch (float): Molar weight (chamber) [100g/mole].
        M_ex (float): Molar weight (exhaust) [100g/mole].
        Isp_frozen (float): Frozen specific impulse [s].
        Isp_shifting (float): Shifting specific impulse [s].
        qsi_ch (float): Number of condensed phase moles per 100 gram (chamber) [moles].
        qsi_ex (float): Number of condensed phase moles per 100 gram (exhaust) [moles].
    """

    burn_rate: list[dict[str, float | int]]
    combustion_efficiency: float
    density: float
    k_mix_ch: float
    k_2ph_ex: float
    T0_ideal: float
    M_ch: float
    M_ex: float
    Isp_frozen: float
    Isp_shifting: float
    qsi_ch: float
    qsi_ex: float

    def __post_init__(self) -> None:
        """
        Perform post-initialization tasks.

        This method is called after the object initialization to perform any
        additional setup or calculations required based on the provided
        attributes.

        Args:
            None

        Returns:
            None
        """
        # Real combustion temperature based on the ideal temperature and the
        # combustion efficiency [K]:
        self.T0 = self.T0_ideal * self.combustion_efficiency

        # Gas constant per molecular weight calculations:
        self.R_ch = scipy.constants.R / self.M_ch
        self.R_ex = scipy.constants.R / self.M_ex

    def get_burn_rate(self, chamber_pressure: float) -> float:
        """
        Get the instantaneous burn rate.

        This method calculates the instantaneous burn rate of the solid propellant
        based on the provided chamber pressure using St. Robert's law.

        Args:
            chamber_pressure (float): Instantaneous stagnation pressure [Pa].

        Returns:
            float: Instantaneous burn rate in meters per second [m/s].

        Raises:
            BurnRateOutOfBoundsError: If the chamber pressure is out of the burn rate range.
        """
        for item in self.burn_rate:
            if item["min"] <= chamber_pressure <= item["max"]:
                a = item["a"]
                n = item["n"]
                return (a * (chamber_pressure * 1e-6) ** n) * 1e-3  # in m/s

        raise BurnRateOutOfBoundsError(chamber_pressure)


# Propellant instances
KNDX = SolidPropellant(
    [
        {"min": 0, "max": 0.779e6, "a": 8.875, "n": 0.619},
        {"min": 0.779e6, "max": 2.572e6, "a": 7.553, "n": -0.009},
        {"min": 2.572e6, "max": 5.930e6, "a": 3.841, "n": 0.688},
        {"min": 5.930e6, "max": 8.502e6, "a": 17.20, "n": -0.148},
        {"min": 8.502e6, "max": 11.20e6, "a": 4.775, "n": 0.442},
    ],
    0.95,
    1795.0 * 1.00,
    1.1308,
    1.0430,
    1712,
    42.391 * 1e-3,
    42.882 * 1e-3,
    152.4,
    154.1,
    0.307,
    0.321,
)

KNSB = SolidPropellant(
    [
        {"min": 0, "max": 11e6, "a": 5.13, "n": 0.222},
    ],
    0.95,
    1837.3 * 0.95,
    1.1361,
    1.0420,
    1603,
    39.857 * 1e-3,
    40.048 * 1e-3,
    151.4,
    153.5,
    0.316,
    0.321,
)

KNSB_NAKKA = SolidPropellant(
    [
        {"min": 0, "max": 0.807e6, "a": 10.708, "n": 0.625},
        {"min": 0.807e6, "max": 1.503e6, "a": 8.763, "n": -0.314},
        {"min": 1.503e6, "max": 3.792e6, "a": 7.852, "n": -0.013},
        {"min": 3.792e6, "max": 7.033e6, "a": 3.907, "n": 0.535},
        {"min": 7.033e6, "max": 10.67e6, "a": 9.653, "n": 0.064},
    ],
    0.95,
    1837.3 * 0.95,
    1.1361,
    1.0420,
    1603,
    39.857 * 1e-3,
    40.048 * 1e-3,
    151.4,
    153.5,
    0.316,
    0.321,
)

KNSU = SolidPropellant(
    [{"min": 0, "max": 100e6, "a": 8.260, "n": 0.319}],
    0.95,
    1899.5 * 0.95,
    1.1330,
    1.1044,
    1722,
    41.964 * 1e-3,
    41.517 * 1e-3,
    153.3,
    155.1,
    0.306,
    0.321,
)

# NOTE: Data for both RNXs still needs to be revised and updated according
# to ProPEP3.

RNX_57 = SolidPropellant(
    [{"min": 0, "max": 100e6, "a": 1.95, "n": 0.477}],
    0.95,
    1844.5 * 0.95,
    1.159,
    1.026,
    1644,
    45.19 * 1e-3,
    45.19 * 1e-3,
    158.1,
    158.1,
    0.306,
    0.321,
)

RNX_71V = SolidPropellant(
    [{"min": 0, "max": 100e6, "a": 2.57, "n": 0.371}],
    0.95,
    1816.1 * 0.95,
    1.180,
    1.027,
    1434,
    41.83 * 1e-3,
    41.83 * 1e-3,
    153.6,
    153.6,
    0.306,
    0.321,
)

KNER = SolidPropellant(
    [{"min": 0, "max": 100e6, "a": 2.903, "n": 0.395}],
    0.94,
    1820.0 * 0.95,
    1.1390,
    1.0426,
    1608,
    38.570 * 1e-3,
    38.779 * 1e-3,
    153.8,
    156.0,
    0.315,
    0.321,
)
