"""
Pressure vessel burst-pressure calculations.

Provides functions for burst pressure of closed-end thick-walled cylindrical
vessels and flat plates, based on the Von Mises equivalent stress theory.

References:
    Shigley, J.E., Mischke, C.R., & Budynas, R.G. (2015). Mechanical
    Engineering Design (10th ed.). McGraw-Hill.
"""

import numpy as np


def _get_cylindrical_vessel_hoop_stress(
    pressure: float,
    inner_radius: float,
    outer_radius: float,
) -> float:
    """
    Return the hoop stress at the inner wall of a thick-walled cylinder.

    Hoop (circumferential) stress acts tangentially around the circumference,
    "trying to split" a closed-end cylinder along its length under internal
    pressure. Formula from Shigley et al. (2015), Eq. (3-50).

    Args:
        pressure: Internal pressure [Pa].
        inner_radius: Inner radius of the cylinder [m].
        outer_radius: Outer radius of the cylinder [m].

    Returns:
        Hoop stress at the inner wall [Pa].
    """
    a = inner_radius
    b = outer_radius
    return pressure * a**2 / (b**2 - a**2) * (1 + b**2 / a**2)


def _get_cylindrical_vessel_radial_stress(
    pressure: float,
    inner_radius: float,
    outer_radius: float,
) -> float:
    """
    Return the radial stress at the inner wall of a thick-walled cylinder.

    Radial stress acts along the radius, pushing inward or outward for a
    closed-end cylinder under internal pressure. Formula from Shigley et al.
    (2015), Eq. (3-50).

    Args:
        pressure: Internal pressure [Pa].
        inner_radius: Inner radius of the cylinder [m].
        outer_radius: Outer radius of the cylinder [m].

    Returns:
        Radial stress at the inner wall [Pa].
    """
    a = inner_radius
    b = outer_radius
    return pressure * a**2 / (b**2 - a**2) * (1 - b**2 / a**2)


def _get_cylindrical_vessel_logitudinal_stress(
    pressure: float,
    inner_radius: float,
    outer_radius: float,
) -> float:
    """
    Return the longitudinal stress at the inner wall of a thick-walled cylinder.

    Longitudinal stress acts along the cylinder's axis, trying to pull the end
    caps off, for a closed-end cylinder under internal pressure.

    Args:
        pressure: Internal pressure [Pa].
        inner_radius: Inner radius of the cylinder [m].
        outer_radius: Outer radius of the cylinder [m].

    Returns:
        Longitudinal stress at the inner wall [Pa].
    """
    a = inner_radius
    b = outer_radius
    return 2 * pressure * a**2 / (b**2 - a**2)


def get_cylindrical_vessel_von_mises_stress(
    pressure: float,
    inner_radius: float,
    outer_radius: float,
) -> float:
    """
    Return the Von Mises equivalent stress for a thick-walled cylinder.

    Applies to a closed-end thick-walled cylindrical vessel under internal
    pressure.

    Args:
        pressure: Internal pressure [Pa].
        inner_radius: Inner radius of the cylinder [m].
        outer_radius: Outer radius of the cylinder [m].

    Returns:
        Von Mises equivalent stress [Pa].
    """
    sigma_t = _get_cylindrical_vessel_hoop_stress(pressure, inner_radius, outer_radius)
    sigma_r = _get_cylindrical_vessel_radial_stress(
        pressure, inner_radius, outer_radius
    )
    sigma_l = _get_cylindrical_vessel_logitudinal_stress(
        pressure, inner_radius, outer_radius
    )

    sigma_eq = np.sqrt(
        ((sigma_l - sigma_r) ** 2 + (sigma_r - sigma_t) ** 2 + (sigma_t - sigma_l) ** 2)
        / 2.0
    )

    return sigma_eq


def get_flat_plate_stress(pressure: float, diameter: float, thickness: float) -> float:
    """
    Return the membrane (tensile) stress in a uniformly loaded flat plate.

    Applies to a simply supported circular plate loaded by uniform internal
    pressure. Conservative for real end caps, which often include edge bending
    restraint or doming.

    Args:
        pressure: Internal pressure [Pa].
        diameter: Plate diameter [m].
        thickness: Plate thickness [m].

    Returns:
        Membrane stress [Pa].
    """
    return pressure * diameter / (2.0 * thickness)


def get_cylindrical_vessel_burst_pressure(
    inner_radius: float,
    outer_radius: float,
    material_yield_strength: float,
) -> float:
    """
    Return the burst pressure for a thick-walled cylindrical vessel.

    Defined as the internal pressure at which the Von Mises equivalent stress
    reaches the material's yield strength.

    Args:
        inner_radius: Inner radius of the vessel [m].
        outer_radius: Outer radius of the vessel [m].
        material_yield_strength: Material yield strength [Pa].

    Returns:
        Burst pressure [Pa].
    """
    # Von Mises stress per unit internal pressure.
    equiv_per_unit = get_cylindrical_vessel_von_mises_stress(
        1.0, inner_radius, outer_radius
    )

    return material_yield_strength / equiv_per_unit


def get_flat_plate_burst_pressure(
    diameter: float,
    thickness: float,
    material_yield_strength: float,
) -> float:
    """
    Return the burst pressure for a flat plate.

    Defined as the internal pressure at which the membrane stress reaches the
    material's yield strength.

    Args:
        diameter: Plate diameter [m].
        thickness: Plate thickness [m].
        material_yield_strength: Material yield strength [Pa].

    Returns:
        Burst pressure [Pa].
    """
    return 2 * material_yield_strength * thickness / diameter
