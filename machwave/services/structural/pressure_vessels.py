"""
This module provides functions to calculate the burst pressure of pressure vessels,
specifically closed-end thick-walled cylindrical vessels and flat plates, based on
the Von Mises equivalent stress theory.


References:
    Shigley, J.E., Mischke, C.R., & Budynas, R.G., "Mechanical Engineering
    Design", 10th ed., McGraw-Hill, 2015.
"""

import numpy as np

"""
Individual stress calculations for a closed-end thick-walled cylindrical vessel
under internal pressure.
"""


def _get_cylindrical_vessel_hoop_stress(
    pressure: float,
    inner_radius: float,
    outer_radius: float,
) -> float:
    """
    Hoop (circumferential) stress at the inner wall for a closed-end
    thick-walled cylindrical vessel under internal pressure.

    Acts tangentially around the circumference, “trying to split” the cylinder
    along its length.

    Formula from Shigley et al. (2015), Eq. (3-50).

    Args:
        pressure (float): Internal pressure.
        inner_radius (float): Inner radius of the cylinder.
        outer_radius (float): Outer radius of the cylinder.
    Returns:
        float: Hoop stress at the inner wall.
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
    Radial stress at the inner wall for a closed-end thick-walled cylindrical
    vessel under internal pressure.

    Acts along the radius, pushing inward or outward.

    Formula from Shigley et al. (2015), Eq. (3-50).

    Args:
        pressure (float): Internal pressure.
        inner_radius (float): Inner radius of the cylinder.
        outer_radius (float): Outer radius of the cylinder.
    Returns:
        float: Radial stress at the inner wall.
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
    Longitudinal stress at the inner wall of a thick-walled closed-end cylinder
    under internal pressure.

    Acts along the cylinder's axis, trying to pull the end caps off.

    Args:
        pressure (float): Internal pressure.
        inner_radius (float): Inner radius of the cylinder.
        outer_radius (float): Outer radius of the cylinder.
    Returns:
        float: Longitudinal stress at the inner wall.
    """
    a = inner_radius
    b = outer_radius
    return 2 * pressure * a**2 / (b**2 - a**2)


"""
Stress calculations:
"""


def get_cylindrical_vessel_von_mises_stress(
    pressure: float,
    inner_radius: float,
    outer_radius: float,
) -> float:
    """
    Calculate the Von Mises equivalent stress for a closed-end thick-walled
    cylindrical vessel under internal pressure.

    Args:
        pressure (float): Internal pressure.
        inner_radius (float): Inner radius of the cylinder.
        outer_radius (float): Outer radius of the cylinder.
    Returns:
        float: Von Mises equivalent stress (same units as pressure).
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
    Membrane (tensile) stress in a flat, simply supported circular plate
    loaded by uniform internal pressure.

    This is conservative for real end caps, which often include edge
    bending restraint or doming.
    """
    return pressure * diameter / (2.0 * thickness)


"""
Burst pressure calculations:
"""


def get_cylindrical_vessel_burst_pressure(
    inner_radius: float,
    outer_radius: float,
    material_yield_strength: float,
) -> float:
    """
    Calculate the internal burst pressure at which the Von Mises equivalent
    stress reaches the material's yield strength.

    Args:
        inner_radius (float): Inner radius of the vessel.
        outer_radius (float): Outer radius of the vessel.
        material_yield_strength (float): Yield strength of the material.

    Returns:
        float: Burst pressure (same units as yield strength).
    """
    # Von Mises stress per unit internal pressure
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
    Calculate the internal burst pressure at which the Von Mises equivalent
    stress reaches the material's yield strength.

    Args:
        diameter (float): Diameter of the plate.
        thickness (float): Thickness of the plate.
        material_yield_strength (float): Yield strength of the material.

    Returns:
        float: Burst pressure (same units as yield strength).
    """
    return 2 * material_yield_strength * thickness / diameter
