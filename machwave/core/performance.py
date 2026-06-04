"""Performance metrics and calculations."""

import numpy as np
import numpy.typing as npt
import scipy.constants


def get_effective_flame_temperature(
    adiabatic_flame_temperature: float, combustion_efficiency: float
) -> float:
    """
    Apply the combustion efficiency to the adiabatic flame temperature.

    Args:
        adiabatic_flame_temperature: Adiabatic flame temperature [K].
        combustion_efficiency: Combustion efficiency in (0, 1], the ratio of the actual
            to the ideal (adiabatic) flame temperature.

    Returns:
        Effective flame temperature [K].
    """
    return combustion_efficiency * adiabatic_flame_temperature


def get_total_impulse(
    thrust: npt.NDArray[np.float64],
    time: npt.NDArray[np.float64],
) -> float:
    """
    Get total impulse by trapezoidal integration of the thrust curve.

    Args:
        thrust: Thrust samples [N].
        time: Time samples [s] matching the thrust samples.

    Returns:
        Total impulse [N-s].
    """
    return float(np.trapezoid(thrust, time))


def get_specific_impulse(total_impulse: float, initial_propellant_mass: float) -> float:
    """
    Get specific impulse.

    Args:
        total_impulse: Total impulse [N-s].
        initial_propellant_mass: Initial propellant mass [kg].

    Returns:
        Specific impulse [s].
    """
    return total_impulse / initial_propellant_mass / scipy.constants.g
