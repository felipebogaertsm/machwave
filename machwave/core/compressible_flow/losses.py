"""
Losses and correction factors for rocket engines.
All functions return a fraction, between 0 and 1.

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

"""
AD-A015 140 cites typical ranges for the correction factors.
Some of these ranges were adjusted based on the experience of the authors and the
typical outcomes for validation cases. Ranges are expressed as fractions.
"""

TYPICAL_RANGES = {
    "divergent_loss": {"lower": 0.0075, "upper": 0.05},
    "kinetics_loss": {"lower": 0.001, "upper": 0.05},
    "boundary_layer_loss": {"lower": 0.001, "upper": 0.03},
    "two_phase_flow_loss": {"lower": 0.001, "upper": 0.05},
}


@decorators.check_bounds(lower=0.0, upper=1.0)
@decorators.warn_if_outside_range(**TYPICAL_RANGES["divergent_loss"])
def get_nozzle_divergent_loss_fraction(divergent_angle: float) -> float:
    """
    Calculates the divergent nozzle loss fraction given the half angle.
    NOTE: only applicable for a conical convergent-divergent nozzle.

    Args:
        divergent_angle: The half angle of the divergent nozzle [degrees].

    Returns:
        The divergent loss fraction in [0, 1].
    """
    return 0.5 * (1 - np.cos(np.deg2rad(divergent_angle)))


@decorators.check_bounds(lower=0.0, upper=1.0)
@decorators.warn_if_outside_range(**TYPICAL_RANGES["kinetics_loss"])
def get_kinetics_loss_fraction(
    i_sp_th_frozen: float, i_sp_th_shifting: float, chamber_pressure_psi: float
) -> float:
    """
    The kinetics loss accounts for the decrement in performance due to
    incomplete heat transfer of latent heat to sensible heat caused by the finite time
    required for the gas phase chemical reactions to occur.

    Valid for liquid, solid, and hybrid propellants.
    The expansion ratio of the i_sp_th_frozen and i_sp_th_shifting should be the same.

    Pressure correction is applied for chamber pressures above 1.379 MPa (200 psi), in
    order to dampen the effect of the kinetics loss.

    The source AFRPL-TR-75-36 calculates it as a percentage, here it is converted to a
    fraction [0, 1].

    Args:
        i_sp_th_frozen: The specific impulse of the frozen flow [s].
        i_sp_th_shifting: The specific impulse of the shifting flow [s].
        chamber_pressure_psi: The chamber pressure [psi].
    Returns:
        The kinetics loss fraction in [0, 1].
    """
    i_sp_th_ratio = i_sp_th_frozen / i_sp_th_shifting

    if chamber_pressure_psi < KINETICS_LOSS_PRESSURE_THRESHOLD_PSI:
        pressure_correction = 1.0
    else:
        pressure_correction = (
            KINETICS_LOSS_PRESSURE_THRESHOLD_PSI / chamber_pressure_psi
        )

    return 0.333 * (1 - i_sp_th_ratio) * pressure_correction


@decorators.check_bounds(lower=0.0, upper=1.0)
@decorators.warn_if_outside_range(**TYPICAL_RANGES["boundary_layer_loss"])
def get_boundary_layer_loss_fraction(
    chamber_pressure_psi: float,
    throat_diameter_inch: float,
    expansion_ratio: float,
    time: float,
    c_1: float,
    c_2: float,
) -> float:
    """
    Boundary layer loss accounts for the decrement in performance due to
    the viscous and heat transfer effects in the nozzle walls. It is time dependent.

    Valid for liquid, solid, and hybrid propellants.

    The time dependence is exponential due to the transient heat up, important in
    motors with short burn durations (less than 4 seconds). Dependence on expansion
    ratio represents the effect of a the amount of nozzle surface area.

    Time constant C2 comes from analysis of a the transient heating of a BATES motor.

    Time constant C1 was obtained from a direct measurement of the heat loss in a BATES
    motor, among other things.

    Ordinary nozzle:
    C1 = 0.003650
    C2 = 0.000937

    Solid steel nozzle with relatively thick walls:
    C1 = 0.005060
    C2 = 0.000000

    The source AFRPL-TR-75-36 calculates it as a percentage, here it is converted to a
    fraction [0, 1].

    Args:
        chamber_pressure_psi: The chamber pressure [psi].
        throat_diameter_inch: The throat diameter [in].
        expansion_ratio: The expansion ratio of the nozzle.
        time: The time in seconds [s].
        c_1: Coefficient for the boundary layer loss.
        c_2: Coefficient for the boundary layer loss.
    Returns:
        The boundary layer loss fraction in [0, 1].
    """
    term_1 = c_1 * (chamber_pressure_psi**0.8) / (throat_diameter_inch**0.2)
    term_2 = 1 + 2 * np.exp(
        (-c_2 * chamber_pressure_psi**0.8 * time) / (throat_diameter_inch**0.2)
    )
    term_3 = 1 + 0.016 * (expansion_ratio - 9)

    return 0.01 * term_1 * term_2 * term_3


def _get_two_phase_phase_loss_particle_size(
    chamber_pressure_psi: float,
    mass_fraction_of_condensed_phase: float,
    throat_diameter_inch: float,
    characteristic_length_inch: float,
) -> float:
    """
    Helper function to calculate the two-phase flow loss due to particle size.

    Combines theories of particle growth by condensation in the chamber and collisions
    in the nozzle.

    Args:
        chamber_pressure_psi: The chamber pressure [psi].
        mass_fraction_of_condensed_phase: The mass fraction of the condensed phase.
        throat_diameter_inch: The throat diameter [in].
        characteristic_length_inch: The characteristic length [in].

    Returns:
        The two-phase flow average particle size in micrometers.
    """
    return (
        0.454
        * chamber_pressure_psi ** (1 / 3)
        * mass_fraction_of_condensed_phase ** (1 / 3)
        * (1 - np.exp(-0.004 * characteristic_length_inch))
        * (1 + 0.045 * throat_diameter_inch)
    )


@decorators.check_bounds(lower=0.0, upper=1.0)
@decorators.warn_if_outside_range(**TYPICAL_RANGES["two_phase_flow_loss"])
def get_two_phase_flow_loss_fraction(
    chamber_pressure_psi: float,
    mass_fraction_of_condensed_phase: float,
    expansion_ratio: float,
    throat_diameter_inch: float,
    characteristic_length_inch: float,
) -> float:
    """
    Two-phase flow loss accounts for the decrement in performance due to
    the presence of a condensed phase in the combustion products.

    Valid for solid, and hybrid propellants.

    The source AFRPL-TR-75-36 calculates it as a percentage, here it is converted to a
    fraction [0, 1].

    Args:
        chamber_pressure_psi: The chamber pressure [psi].
        mass_fraction_of_condensed_phase: The mass fraction of the condensed phase.
        expansion_ratio: The expansion ratio of the nozzle.
        throat_diameter_inch: The throat diameter [in].
        characteristic_length_inch: The characteristic length [in].
    Returns:
        The two-phase flow loss fraction in [0, 1].
    """
    particle_size_um: float = _get_two_phase_phase_loss_particle_size(
        chamber_pressure_psi,
        mass_fraction_of_condensed_phase,
        throat_diameter_inch,
        characteristic_length_inch,
    )

    if mass_fraction_of_condensed_phase >= 0.09:
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
    else:  # mass_fraction_of_condensed_phase < 0.09
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

    numerator = (mass_fraction_of_condensed_phase**c_4) * (particle_size_um**c_5)
    denominator = (
        (chamber_pressure_psi**0.15)
        * (expansion_ratio**0.08)
        * (throat_diameter_inch**c_6)
    )

    return 0.01 * c_3 * numerator / denominator


@decorators.check_bounds(lower=0.0, upper=1.0)
def get_overall_nozzle_efficiency(
    divergent_loss: float,
    kinetics_loss: float,
    boundary_layer_loss: float,
    two_phase_loss: float,
    other_losses: float,
) -> float:
    """
    Calculates the overall nozzle efficiency by combining the loss fractions.

    All inputs are loss fractions in [0, 1] (not percentages).

    Args:
        divergent_loss: The divergent nozzle loss fraction.
        kinetics_loss: The kinetics loss fraction.
        boundary_layer_loss: The boundary layer loss fraction.
        two_phase_loss: The two-phase flow loss fraction.
        other_losses: Additional losses, as a fraction in [0, 1].

    Returns:
        The overall nozzle efficiency, as a fraction in [0, 1].
    """
    return 1.0 - (
        divergent_loss
        + kinetics_loss
        + boundary_layer_loss
        + two_phase_loss
        + other_losses
    )
