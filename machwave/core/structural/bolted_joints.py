"""
Bolted joints stress and load calculations.
This module provides functions to calculate shear, bearing, and tensile stresses and
loads for bolted joints in plates and cylinders.
"""

import numpy as np

from ..geometric import get_circle_area


def _bolt_cross_sectional_area(screw_diameter: float) -> float:
    """Calculates the cross sectional area for a bolt or screw.

    Args:
        screw_diameter: Effective diameter of the screw. An M4 screw has a diameter of
        4mm, but the effective shaft diameter is 3.3mm.

    Returns:
        Shear area of the screw.
    """
    return get_circle_area(diameter=screw_diameter)


def _bearing_area_per_bolt(thickness: float, hole_diameter: float) -> float:
    """Projected bearing area between bolt shank and plate.

    Args:
        thickness: Thickness of the plate.
        hole_diameter: Diameter of the bolt hole.

    Returns:
        Projected bearing area.
    """
    return thickness * hole_diameter


def _tearout_area_per_bolt(edge_distance: float, thickness: float) -> float:
    """Gross shear area resisting tear-out toward a free edge.

    Args:
        edge_distance: Distance from the center of the bolt hole to the edge of the
            plate.
        thickness: Thickness of the plate.

    Returns:
        Gross shear area.
    """
    return 2.0 * edge_distance * thickness


def _net_section_area(
    pitch_distance: float, thickness: float, hole_diameter: float
) -> float:
    """Net tension area across the bolt line.

    Args:
        pitch_distance: Distance between bolt centers.
        thickness: Thickness of the plate.
        hole_diameter: Diameter of the bolt hole.

    Returns:
        Net tension area.
    """
    return (pitch_distance - hole_diameter) * thickness


def _arc_length(angle: float, diameter: float) -> float:
    """Calculate the arc length on a cylinder wall corresponding to an angle.

    Args:
        angle: Angle in degrees.
        diameter: Diameter of the cylinder.

    Returns:
        Arc length on the cylinder wall.
    """
    angle_radians = np.deg2rad(angle)
    radius = diameter / 2.0
    return radius * angle_radians


def get_shear_stress_per_bolt(
    load: float,
    shank_diameter: float,
    n_shear_planes: int = 1,
) -> float:
    """Transverse shear stress on a bolt.

    Args:
        load: Applied transverse shear load per bolt.
        shank_diameter: Diameter of the bolt shank.
        n_shear_planes: 1 for single shear, 2 for double shear, and so on.

    Returns:
        Shear stress on the bolt.
    """
    area_each = _bolt_cross_sectional_area(shank_diameter)
    return load / (n_shear_planes * area_each)


def get_bearing_stress(
    load: float,
    plate_thickness: float,
    hole_diameter: float,
) -> float:
    """Compressive (bearing) stress between bolt shank and plate.

    Args:
        load: Applied bearing load per bolt.
        plate_thickness: Thickness of the plate.
        hole_diameter: Diameter of the bolt hole (not the shank diameter, but the hole
            diameter which is typically larger to allow for clearance).

    Returns:
        Bearing stress on the plate at the bolt hole.
    """
    return load / _bearing_area_per_bolt(plate_thickness, hole_diameter)


def get_tearout_shear_stress_plate(
    load: float,
    edge_distance: float,
    plate_thickness: float,
) -> float:
    """Average shear stress along the tearout plane toward a free edge.

    Args:
        load: Applied shear load causing tearout.
        edge_distance: Distance from the center of the bolt hole to the edge of the
            plate.
        plate_thickness: Thickness of the plate.

    Returns:
        Average shear stress along the tearout plane.
    """
    return load / _tearout_area_per_bolt(edge_distance, plate_thickness)


def get_net_section_tension_stress_plate(
    load: float,
    pitch_distance: float,
    plate_thickness: float,
    hole_diameter: float,
    n_bolts_in_row: int = 1,
) -> float:
    """Tensile stress across the reduced net section of a bolted plate row.

    Args:
        load: Applied axial load across the bolt row.
        pitch_distance: Distance between bolt centers.
        plate_thickness: Thickness of the plate.
        hole_diameter: Diameter of the bolt hole.
        n_bolts_in_row: Number of bolts in the row.

    Returns:
        Tensile stress across the net section.
    """
    area_each = _net_section_area(pitch_distance, plate_thickness, hole_diameter)
    return load / (n_bolts_in_row * area_each)


def get_tearout_shear_stress_cylinder(
    load: float,
    edge_angle: float,
    wall_thickness: float,
    outer_diameter: float,
) -> float:
    """Average shear stress along the tearout plane toward crown/root of a cylinder.

    Args:
        load: Applied shear load causing tearout.
        edge_angle: Angle from the hole to the free edge (crown or root).
        wall_thickness: Thickness of the cylinder wall.
        outer_diameter: Outer diameter of the cylinder.

    Returns:
        Average shear stress along the tearout plane.
    """
    edge_distance = _arc_length(edge_angle, outer_diameter)
    return get_tearout_shear_stress_plate(load, edge_distance, wall_thickness)


def get_net_section_tension_stress_cylinder(
    load: float,
    pitch_angle: float,
    wall_thickness: float,
    hole_diameter: float,
    outer_diameter: float,
    n_bolts_in_row: int = 1,
) -> float:
    """Tensile stress across the reduced net section of a bolted row on a cylinder wall.

    Args:
        load: Applied axial load across the bolt row.
        pitch_angle: Central angle between adjacent bolt centres along the same
            circumferential line.
        wall_thickness: Thickness of the cylinder wall.
        hole_diameter: Diameter of the bolt hole.
        outer_diameter: Outer diameter of the cylinder.
        n_bolts_in_row: Number of bolts in the row. Defaults to 1.

    Returns:
        Tensile stress across the net section.
    """
    pitch_distance = _arc_length(pitch_angle, outer_diameter)
    return get_net_section_tension_stress_plate(
        load,
        pitch_distance,
        wall_thickness,
        hole_diameter,
        n_bolts_in_row=n_bolts_in_row,
    )


def get_max_shear_load(
    shank_diameter: float,
    allowable_shear_stress: float,
    n_shear_planes: int = 1,
) -> float:
    """Return limiting transverse shear load on a bolt (single or double shear).

    Args:
        shank_diameter: Diameter of the bolt shank.
        allowable_shear_stress: Allowable shear stress for the material.
        n_shear_planes: Number of shear planes. Defaults to 1.

    Returns:
        Maximum shear load per bolt.
    """
    return (
        n_shear_planes
        * _bolt_cross_sectional_area(shank_diameter)
        * allowable_shear_stress
    )


def get_max_bearing_load(
    plate_thickness: float,
    hole_diameter: float,
    allowable_bearing_stress: float,
) -> float:
    """Return limiting compressive/bearing load before hole elongation failure.

    Args:
        plate_thickness: Thickness of the plate.
        hole_diameter: Diameter of the bolt hole.
        allowable_bearing_stress: Allowable bearing stress for the material.

    Returns:
        Maximum bearing load per bolt.
    """
    return (
        _bearing_area_per_bolt(plate_thickness, hole_diameter)
        * allowable_bearing_stress
    )


def get_max_tearout_load_plate(
    edge_distance: float,
    plate_thickness: float,
    allowable_shear_stress: float,
) -> float:
    """Return limiting load causing shear tear-out toward an edge.

    Args:
        edge_distance: Distance from the center of the bolt hole to the edge of the
            plate.
        plate_thickness: Thickness of the plate.
        allowable_shear_stress: Allowable shear stress for the material.

    Returns:
        Maximum tear-out load per bolt.
    """
    return (
        _tearout_area_per_bolt(edge_distance, plate_thickness) * allowable_shear_stress
    )


def get_max_net_tension_load_plate(
    pitch_distance: float,
    plate_thickness: float,
    hole_diameter: float,
    allowable_tensile_stress: float,
    n_bolts_in_row: int = 1,
) -> float:
    """Return limiting axial load across a bolt row before net-section tension failure.

    Args:
        pitch_distance: Distance between bolt centers.
        plate_thickness: Thickness of the plate.
        hole_diameter: Diameter of the bolt hole.
        allowable_tensile_stress: Allowable tensile stress for the material.
        n_bolts_in_row: Number of bolts in a row. Defaults to 1.

    Returns:
        Maximum net tension load.
    """
    area_each = _net_section_area(pitch_distance, plate_thickness, hole_diameter)
    return n_bolts_in_row * area_each * allowable_tensile_stress


def get_max_tearout_load_cylinder(
    edge_angle: float,
    wall_thickness: float,
    outer_diameter: float,
    allowable_shear_stress: float,
) -> float:
    """Edge tear-out toward crown/root of a thin-walled cylinder.

    Arguments:
        edge_angle: Angle from the hole to the free edge.
        wall_thickness: Thickness of the cylinder wall.
        outer_diameter: Outer diameter of the cylinder.
        allowable_shear_stress: Allowable shear stress for the material.

    Returns:
        Maximum tear-out load per bolt.
    """
    edge_distance = _arc_length(edge_angle, outer_diameter)
    return get_max_tearout_load_plate(
        edge_distance, wall_thickness, allowable_shear_stress
    )


def get_max_net_tension_load_cylinder(
    pitch_angle: float,
    wall_thickness: float,
    hole_diameter: float,
    allowable_tensile_stress: float,
    outer_diameter: float,
    n_bolts_in_row: int = 1,
) -> float:
    """Net-section tension rupture across a bolt row on a cylinder wall.

    Args:
        pitch_angle: Central angle between adjacent bolt centres along the same
            circumferential line.
        wall_thickness: Thickness of the cylinder wall.
        hole_diameter: Diameter of the bolt hole.
        allowable_tensile_stress: Allowable tensile stress for the material.
        outer_diameter: Outer diameter of the cylinder.
        n_bolts_in_row: Number of bolts in a row. Defaults to 1.

    Returns:
        Maximum net tension load.
    """
    pitch_distance = _arc_length(pitch_angle, outer_diameter)
    return get_max_net_tension_load_plate(
        pitch_distance,
        wall_thickness,
        hole_diameter,
        allowable_tensile_stress,
        n_bolts_in_row=n_bolts_in_row,
    )
