"""
Losses and correction factors for rocket engines.
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

KINETICS_LOSS_PRESSURE_THRESHOLD_PSI = 200  # psi
OTHER_LOSSES_DEFAULT = 12.0

"""
AD-A015 140 cites typical ranges for the correction factors.
Some of these ranges were adjusted based on the experience of the
authors and the typical outcomes for validation cases.
"""

TYPICAL_RANGES = {
    "divergent_loss": {"lower": 0.75, "upper": 5},
    "kinetics_loss": {"lower": 0.1, "upper": 5},
    "boundary_layer_loss": {"lower": 0.1, "upper": 3},
    "two_phase_flow_loss": {"lower": 0.1, "upper": 5},
}


@decorators.check_bounds(lower=0.0, upper=100.0)
@decorators.warn_if_outside_range(**TYPICAL_RANGES["divergent_loss"])
def get_nozzle_divergent_percentage_loss(divergent_angle: float) -> float:
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
    return 50 * (1 - np.cos(np.deg2rad(divergent_angle)))


@decorators.check_bounds(lower=0.0, upper=100.0)
@decorators.warn_if_outside_range(**TYPICAL_RANGES["kinetics_loss"])
def get_kinetics_percentage_loss(
    i_sp_th_frozen: float, i_sp_th_shifting: float, chamber_pressure_psi: float
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
        i_sp_th_frozen (float): The specific impulse of the frozen
            flow.
        i_sp_th_shifting (float): The specific impulse of the shifting
            flow.
        chamber_pressure_psi (float): The chamber pressure in psi.
    Returns:
        float: The kinetics correction factor.
    """
    i_sp_th_ratio = i_sp_th_frozen / i_sp_th_shifting

    if chamber_pressure_psi < KINETICS_LOSS_PRESSURE_THRESHOLD_PSI:
        pressure_correction = 1.0
    else:
        pressure_correction = (
            KINETICS_LOSS_PRESSURE_THRESHOLD_PSI / chamber_pressure_psi
        )

    return 33.3 * (1 - i_sp_th_ratio) * pressure_correction


@decorators.check_bounds(lower=0.0, upper=100.0)
@decorators.warn_if_outside_range(**TYPICAL_RANGES["boundary_layer_loss"])
def get_boundary_layer_percentage_loss(
    chamber_pressure_psi: float,
    throat_diameter_inch: float,
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
        chamber_pressure_psi (float): The chamber pressure in psi.
        throat_diameter_inch (float): The throat diameter in inches.
        expansion_ratio (float): The expansion ratio of the nozzle.
        time (float): The time in seconds.
        c_1 (float): Coefficient for the boundary layer correction factor.
        c_2 (float): Coefficient for the boundary layer correction factor.
    Returns:
        float: The boundary layer correction factor.
    """
    term_1 = c_1 * (chamber_pressure_psi**0.8) / (throat_diameter_inch**0.2)
    term_2 = 1 + 2 * np.exp(
        (-c_2 * chamber_pressure_psi**0.8 * time) / (throat_diameter_inch**0.2)
    )
    term_3 = 1 + 0.016 * (expansion_ratio - 9)

    return term_1 * term_2 * term_3


def _get_two_phase_phase_loss_particle_size(
    chamber_pressure_psi: float,
    xi: float,
    throat_diameter_inch: float,
    characteristic_length_inch: float,
) -> float:
    """
    Helper function to calculate the two-phase flow loss due to
    particle size.

    Combines theories of particle growth by condensation in the chamber
    and collisions in the nozzle.

    Args:
        chamber_pressure_psi (float): The chamber pressure in psi.
        xi (float): The mole fraction of the condensed phase.
        throat_diameter_inch (float): The throat diameter in inches.
        characteristic_length_inch (float): The characteristic length
            in inches.

    Returns:
        float: The two-phase flow average particle size in micrometers.
    """
    return (
        0.454
        * chamber_pressure_psi ** (1 / 3)
        * xi ** (1 / 3)
        * (1 - np.exp(-0.004 * characteristic_length_inch))
        * (1 + 0.045 * throat_diameter_inch)
    )


@decorators.check_bounds(lower=0.0, upper=100.0)
@decorators.warn_if_outside_range(**TYPICAL_RANGES["two_phase_flow_loss"])
def get_two_phase_flow_percentage_loss(
    chamber_pressure_psi: float,
    mole_fraction_of_condensed_phase: float,
    expansion_ratio: float,
    throat_diameter_inch: float,
    characteristic_length_inch: float,
) -> float:
    """
    Two-phase flow correction factor accounts for the decrement in
    performance due to the presence of a condensed phase in the
    combustion products.

    Valid for solid, and hybrid propellants.

    Args:
        chamber_pressure_psi (float): The chamber pressure in psi.
        mole_fraction_of_condensed_phase (float): The mole fraction of
            the condensed phase in moles / 100 gm.
        expansion_ratio (float): The expansion ratio of the nozzle.
        throat_diameter_inch (float): The throat diameter in inches.
        characteristic_length_inch (float): The characteristic length
            in inches.
    Returns:
        float: The two-phase flow correction factor.
    """
    particle_size_um: float = _get_two_phase_phase_loss_particle_size(
        chamber_pressure_psi,
        mole_fraction_of_condensed_phase,
        throat_diameter_inch,
        characteristic_length_inch,
    )
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

    numerator = (xi**c_4) * (particle_size_um**c_5)
    denominator = (
        (chamber_pressure_psi**0.15)
        * (expansion_ratio**0.08)
        * (throat_diameter_inch**c_6)
    )

    return c_3 * numerator / denominator


@decorators.check_bounds(lower=0.0, upper=100.0)
def get_overall_nozzle_efficiency(
    eta_div: float,
    eta_kin: float,
    eta_bl: float,
    eta_2p: float,
    other_losses: float = OTHER_LOSSES_DEFAULT,
) -> float:
    """
    Overall nozzle efficiency is the sum of the individual correction
    factors.

    Args:
        eta_div (float): The divergent nozzle correction factor.
        eta_kin (float): The kinetics correction factor.
        eta_bl (float): The boundary layer correction factor.
        eta_2p (float): The two-phase flow correction factor.

    Returns:
        float: The overall nozzle efficiency.
    """
    return (100 - (eta_div + eta_kin + eta_bl + eta_2p + other_losses)) / 100
