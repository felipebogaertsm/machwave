"""Performance metrics and calculations."""

import numpy as np
import numpy.typing as npt
import scipy.constants


def get_effective_flame_temperature(
    adiabatic_flame_temperature: float, combustion_efficiency: float
) -> float:
    """
    Get the flame temperature that delivers the derated characteristic velocity.

    The combustion efficiency is a characteristic velocity (c*) efficiency,
    eta_c* = c*_actual / c*_ideal. Since c* = sqrt(R T) / Gamma(k), the
    temperature is scaled by its square, T_eff = eta_c*^2 T0. With R and k held
    at their ideal values, the chamber then delivers c* = eta_c* c*_ideal, and the
    chamber pressure for a given mass flow and throat scales by eta_c*.

    Args:
        adiabatic_flame_temperature: Adiabatic flame temperature [K].
        combustion_efficiency: Characteristic velocity efficiency in (0, 1].

    Returns:
        Effective flame temperature [K].
    """
    return combustion_efficiency**2 * adiabatic_flame_temperature


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


def get_specific_impulse(
    total_impulse: float, expelled_propellant_mass: float
) -> float:
    """
    Get specific impulse.

    Args:
        total_impulse: Total impulse [N-s].
        expelled_propellant_mass: Propellant mass expelled over the run [kg].

    Returns:
        Specific impulse [s], or NaN if no propellant was expelled.
    """
    if expelled_propellant_mass <= 0.0:
        return np.nan
    return total_impulse / expelled_propellant_mass / scipy.constants.g
