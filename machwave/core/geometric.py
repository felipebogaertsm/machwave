import numpy as np


def get_circle_area(diameter: float) -> float:
    """
    Returns the area of a circle based on the circle's diameter.

    Args:
        diameter: The diameter of the circle.

    Returns:
        float: The area of the circle.
    """
    return np.pi * 0.25 * diameter**2


def get_torus_area(major_radius: float, minor_radius: float) -> float:
    """
    Calculates the surface area of a torus.

    Args:
        major_radius: The major radius of the torus.
        minor_radius: The minor radius of the torus.

    Returns:
        float: The surface area of the torus.
    """
    return 4 * np.pi**2 * major_radius * minor_radius


def get_trapezoidal_area(base_length: float, tip_length: float, height: float) -> float:
    """
    Calculates the area of a trapezoid.

    Args:
        base_length: The length of the base of the trapezoid.
        tip_length: The length of the tip of the trapezoid.
        height: The height of the trapezoid.

    Returns:
        The area of the trapezoid.
    """
    return (base_length + tip_length) * height / 2


def get_cylinder_surface_area(length: float, diameter: float) -> float:
    """
    Returns the surface area of a cylinder.

    Args:
        length: The length of the cylinder.
        diameter: The diameter of the cylinder.

    Returns:
        float: The surface area of the cylinder.
    """
    return np.pi * length * diameter


def get_cylinder_volume(diameter: float, length: float) -> float:
    """
    Returns the volume of a cylinder.

    Args:
        diameter: The diameter of the cylinder.
        length: The length of the cylinder.

    Returns:
        The volume of the cylinder.
    """
    return np.pi * length * (diameter**2) / 4
