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

from machwave.common import decorators
from machwave.core import conversions


@decorators.check_bounds(lower=0.0, upper=1.0)
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


@decorators.check_bounds(lower=0.0, upper=1.0)
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


@decorators.check_bounds(lower=0.0, upper=1.0)
def get_boundary_layer_correction_factor(
    chamber_pressure: float,
    throat_diameter: float,
    expansion_ratio: float,
    time: float,
    c_1: float,
    c_2: float,
) -> float:
    """
    Boundary layer correction factor accounts for the decrement in
    performance due to the viscous and heat transfer effects in the
    nozzle walls. It is time dependent.

    Valid for liquid, solid, and hybrid propellants.

    The time depencence is exponential due to the transient heat up,
    important in motors with short burn durations (less than 4
    seconds). Dependence on expansion ratio represents the effect of
    a the amount of nozzle surface area.

    Time constant C2 comes from analysis of a the transient heating of
    a BATES motor.

    Time constant C1 was obtained from a direct measurement of the heat
    loss in a BATES motor, among other things.

    Ordinary nozzle:
    C1 = 0.003650
    C2 = 0.000937

    Solid steel nozzle with relatively thick walls:
    C1 = 0.005060
    C2 = 0.000000

    Args:
        chamber_pressure (float): The chamber pressure in Pascals.
        throat_diameter (float): The throat diameter in meters.
        expansion_ratio (float): The expansion ratio of the nozzle.
        time (float): The time in seconds.
        c_1 (float): Coefficient for the boundary layer correction factor.
        c_2 (float): Coefficient for the boundary layer correction factor.
    Returns:
        float: The boundary layer correction factor.
    """
    chamber_pressure_psi = conversions.convert_pa_to_psi(chamber_pressure)
    throat_diameter_inch = conversions.convert_meter_to_inch(throat_diameter)

    term_1 = c_1 * (chamber_pressure_psi**0.8) / (throat_diameter_inch**0.2)
    term_2 = 1 + 2 * np.exp(
        (-c_2 * chamber_pressure_psi**0.8 * time) / (throat_diameter_inch**0.2)
    )
    term_3 = 1 + 0.016 * (expansion_ratio - 9)

    return term_1 * term_2 * term_3


@decorators.check_bounds(lower=0.0, upper=1.0)
def get_two_phase_flow_correction_factor(
    chamber_pressure: float,
    mole_fraction_of_condensed_phase: float,
    particle_size: float,
    expansion_ratio: float,
    throat_diameter: float,
) -> float:
    """
    Two-phase flow correction factor accounts for the decrement in
    performance due to the presence of a condensed phase in the
    combustion products.

    Valid for solid, and hybrid propellants.

    Args:
        chamber_pressure (float): The chamber pressure in Pascals.
        mole_fraction_of_condensed_phase (float): The mole fraction of
            the condensed phase in moles / 100 gm.
        particle_size (float): The particle size in meters.
        expansion_ratio (float): The expansion ratio of the nozzle.
        throat_diameter (float): The throat diameter in meters.
    Returns:
        float: The two-phase flow correction factor.
    """
    throat_diameter_inch: float = conversions.convert_meter_to_inch(throat_diameter)
    chamber_pressure_psi: float = conversions.convert_pa_to_psi(chamber_pressure)
    particle_size_um: float = conversions.convert_meter_to_micrometer(particle_size)
    xi: float = mole_fraction_of_condensed_phase  # rename for brevity

    if xi >= 0.09:
        c_4 = 0.5
        if throat_diameter_inch < 1.0:
            c_3, c_5, c_6 = 9.0, 1.0, 1.0
        elif throat_diameter_inch < 2.0:
            c_3, c_5, c_6 = 9.0, 1.0, 0.8
        else:  # throat_diameter_inch >= 2
            if particle_size_um < 4.0:
                c_3, c_5, c_6 = 13.4, 0.8, 0.8
            elif particle_size_um <= 8.0:
                c_3, c_5, c_6 = 10.2, 0.8, 0.4
            else:
                c_3, c_5, c_6 = 7.58, 0.8, 0.33
    else:  # xi < 0.09
        c_4 = 1.0
        if throat_diameter_inch < 1.0:
            c_3, c_5, c_6 = 30.0, 1.0, 1.0
        elif throat_diameter_inch < 2.0:
            c_3, c_5, c_6 = 30.0, 1.0, 0.8
        else:  # throat_diameter_inch >= 2
            if particle_size_um < 4.0:
                c_3, c_5, c_6 = 44.5, 0.8, 0.8
            elif particle_size_um <= 8.0:
                c_3, c_5, c_6 = 34.0, 0.8, 0.4
            else:
                c_3, c_5, c_6 = 25.2, 0.8, 0.33

    numerator = np.power(xi, c_4) * np.power(particle_size_um, c_5)
    denominator = (
        np.power(chamber_pressure_psi, 0.15)
        * np.power(expansion_ratio, 0.08)
        * np.power(throat_diameter_inch, c_6)
    )

    eta_tp: float = c_3 * numerator / denominator

    return float(eta_tp)
