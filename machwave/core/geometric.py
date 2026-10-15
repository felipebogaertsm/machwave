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
