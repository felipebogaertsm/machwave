from dataclasses import dataclass

import scipy.constants

from .base import Propellant


class BurnRateOutOfBoundsError(Exception):
    """
    Exception raised when the chamber pressure is out of the burn rate range.

    This exception is raised when the chamber pressure provided is outside the
    valid burn rate range for a specific solid propellant.

    Attributes:
        value: The chamber pressure that caused the error.
        message: The error message.
    """

    def __init__(self, value: float) -> None:
        self.value = value
        self.message = f"Chamber pressure out of bounds: {value * 1e-6:.2f} MPa"
        super().__init__(self.message)


@dataclass
class SolidPropellant(Propellant):
    """
    Single-class representation of a solid propellant, encompassing both the
    generic propellant properties and solid-specific attributes.

    Attributes:
        burn_rate: List of dictionaries describing
            burn rate behavior (St. Robert's law parameters) with keys:
            "min", "max", "a", and "n".
        combustion_efficiency: Combustion efficiency (0 to 1).
        density: Propellant density [kg/m^3].
        k_mix: Isentropic exponent for the combustion chamber.
        k_ex: Isentropic exponent for the exhaust.
        T0_ideal: Ideal combustion temperature [K].
        M_ch: Molar weight in the chamber [kg/mol].
        M_ex: Molar weight in the exhaust [kg/mol].
        Isp_frozen: Frozen specific impulse [s].
        Isp_shifting: Shifting specific impulse [s].
        qsi_ch: Number of condensed-phase moles per 100 g in the chamber.
        qsi_ex: Number of condensed-phase moles per 100 g in the exhaust.
    """

    burn_rate: list[dict[str, float | int]]
    combustion_efficiency: float
    density: float
    k_mix: float
    k_ex: float
    T0_ideal: float
    M_ch: float
    M_ex: float
    Isp_frozen: float
    Isp_shifting: float
    qsi_ch: float
    qsi_ex: float

    def __post_init__(self) -> None:
        # Effective combustion temperature:
        self.T0 = self.T0_ideal * self.combustion_efficiency

        # Gas constants for chamber and exhaust:
        self.R_ch = scipy.constants.R / self.M_ch
        self.R_ex = scipy.constants.R / self.M_ex

    def get_burn_rate(self, chamber_pressure: float) -> float:
        """
        Calculates the instantaneous burn rate of the solid propellant using St. Robert's law.

        Args:
            chamber_pressure (float): The instantaneous stagnation pressure [Pa].

        Returns:
            float: The instantaneous burn rate in meters per second.

        Raises:
            BurnRateOutOfBoundsError: If the chamber pressure is not within any
            burn rate range.
        """
        for item in self.burn_rate:
            if item["min"] <= chamber_pressure <= item["max"]:
                a = item["a"]
                n = item["n"]
                # Convert pressure from Pa to MPa, apply St. Robert's law,
                # then convert from mm/s to m/s
                return (a * (chamber_pressure * 1e-6) ** n) * 1e-3

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

MIT_CHERRY_LIMEADE = SolidPropellant(
    [{"min": 0, "max": 6.35e6, "a": 3.2373, "n": 0.3273}],
    0.95,
    1670.0,
    1.2100,
    1.2501,
    2800,
    23.724 * 1e-3,
    23.811 * 1e-3,
    241.3,
    245.1,
    0.138,
    0.139,
)
