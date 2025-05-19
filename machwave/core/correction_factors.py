"""
Correction factors for rocket engines.
All functions return a correction factor that is between 0 and 1.

References:
    Coats, D. E., Levine, J. N., Nickerson, G. R., Tyson, T. J.,
    Cohen, N. S., Harry, D. P. III, & Price, C. F. (1975).
    *A Computer Program for the Prediction of Solid Propellant
    Rocket Motor Performance. Volume I* (Technical Report
    AFRPL-TR-75-36, DTIC Accession AD-A015 140). Air Force
    Rocket Propulsion Laboratory, Edwards Air Force Base, CA.
"""

import numpy as np

from machwave.core import conversions


def get_nozzle_divergent_correction_factor(divergent_angle: float) -> float:
    """
    Calculates the divergent nozzle correction factor given the half angle.
    NOTE: only applicable for a conical convergent-divergent nozzle.

    Args:
        divergent_angle (float): The half angle of the divergent nozzle.

    Returns:
        float: The divergent correction factor.

    Example:
        correction_factor = get_divergent_correction_factor(15.0)
    """
    return 0.5 * (1 - np.cos(np.deg2rad(divergent_angle)))


def get_kinetics_correction_factor(
    i_sp_th_frozen: float, i_sp_th_shifting: float, chamber_pressure: float
) -> float:
    """
    The kinetics correction factor accounts for the decrement in
    performance due to incomplete heat transfer of latent heat to
    sensible heat caused by the finite time required for the
    gas phase chemical reactions to occur.

    Valid for liquid, solid, and hybrid propellants.
    The expansion ratio of the i_sp_th_frozen and i_sp_th_shifting
    should be the same.

    Pressure correction is applied for chamber pressures
    above 1.379 MPa (200 psi), in order to dampen the effect of
    the kinetics correction factor.

    Args:
        i_sp_th_frozen (float): The specific impulse of the frozen flow.
        i_sp_th_shifting (float): The specific impulse of the shifting flow.
        chamber_pressure (float): The chamber pressure in Pascals.
    Returns:
        float: The kinetics correction factor.
    """
    i_sp_th_ratio = i_sp_th_frozen / i_sp_th_shifting

    if chamber_pressure < 1.379e6:
        pressure_correction = 1.0
    else:
        pressure_correction = 1.379e-6 / chamber_pressure

    return 33.3 / 100 * (1 - i_sp_th_ratio) * pressure_correction
