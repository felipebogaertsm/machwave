"""
Performance metrics and calculations.
"""

import numpy as np
import numpy.typing as npt
import scipy.constants


def get_total_impulse(average_thrust: float, thrust_time: float) -> float:
    """Get total impulse.

    Args:
        average_thrust: Average thrust [N].
        thrust_time: Thrust time [s].

    Returns:
        Total impulse [N-s].
    """
    return average_thrust * thrust_time


def get_total_impulse_trapezoidal(
    thrust: npt.NDArray[np.float64],
    time: npt.NDArray[np.float64],
) -> float:
    """Get total impulse by trapezoidal integration of the thrust curve.

    Args:
        thrust: Thrust samples [N].
        time: Time samples [s] matching the thrust samples.

    Returns:
        Total impulse [N-s].
    """
    return float(np.trapezoid(thrust, time))


def get_specific_impulse(total_impulse: float, initial_propellant_mass: float) -> float:
    """Get specific impulse.

    Args:
        total_impulse: Total impulse [N-s].
        initial_propellant_mass: Initial propellant mass [kg].

    Returns:
        Specific impulse [s].
    """
    return total_impulse / initial_propellant_mass / scipy.constants.g
