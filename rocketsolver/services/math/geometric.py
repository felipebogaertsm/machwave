from typing import Optional
import numpy as np
from skimage import measure


def get_circle_area(diameter: float) -> float:
    """
    Returns the area of a circle based on the circle's diameter.

    Args:
        diameter (float): The diameter of the circle.

    Returns:
        float: The area of the circle.
    """
    return np.pi * 0.25 * diameter**2


def get_torus_area(major_radius: float, minor_radius: float) -> float:
    """
    Calculates the surface area of a torus.

    Args:
        major_radius (float): The major radius of the torus.
        minor_radius (float): The minor radius of the torus.

    Returns:
        float: The surface area of the torus.
    """
    return 4 * np.pi**2 * major_radius * minor_radius


def get_trapezoidal_area(
    base_length: float, tip_length: float, height: float
) -> float:
    """
    Calculates the area of a trapezoid.

    Args:
        base_length (float): The length of the base of the trapezoid.
        tip_length (float): The length of the tip of the trapezoid.
        height (float): The height of the trapezoid.

    Returns:
        float: The area of the trapezoid.
    """
    return (base_length + tip_length) * height / 2


def get_cylinder_surface_area(length: float, diameter: float) -> float:
    """
    Returns the surface area of a cylinder.

    Args:
        length (float): The length of the cylinder.
        diameter (float): The diameter of the cylinder.

    Returns:
        float: The surface area of the cylinder.
    """
    return np.pi * length * diameter


def get_cylinder_volume(diameter: float, length: float) -> float:
    """
    Returns the volume of a cylinder.

    Args:
        diameter (float): The diameter of the cylinder.
        length (float): The length of the cylinder.

    Returns:
        float: The volume of the cylinder.
    """
    return np.pi * length * (diameter**2) / 4


def get_contours(
    map: np.ndarray, map_dist: float, *args, **kwargs
) -> np.ndarray:
    """
    Finds contours in an image.

    Args:
        map (np.ndarray): The input image.
        map_dist (float): The map distance.
        *args: Additional arguments to be passed to the find_contours function.
        **kwargs: Additional keyword arguments to be passed to the find_contours function.

    Returns:
        np.ndarray: An array of contours.
    """
    return measure.find_contours(
        map, map_dist, fully_connected="low", *args, **kwargs
    )


def get_length(
    contour: np.ndarray, map_size: int, tolerance: Optional[float] = 3.0
) -> float:
    """
    Returns the total length of all segments in a contour that aren't within
    'tolerance' of the edge of a circle with diameter 'map_size'.

    Args:
        contour (np.ndarray): The contour array.
        map_size (int): The size of the map.
        tolerance (float, optional): The tolerance value. Defaults to 3.0.

    Returns:
        float: The total length of the segments.
    """
    offset = np.roll(contour.T, 1, axis=1)
    lengths = np.linalg.norm(contour.T - offset, axis=0)

    center_offset = np.array([[map_size / 2, map_size / 2]])
    radius = np.linalg.norm(contour - center_offset, axis=1)

    valid = radius < (map_size / 2) - tolerance

    return np.sum(lengths[valid])
