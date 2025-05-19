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
