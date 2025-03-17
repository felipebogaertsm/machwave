import numpy as np
from skimage import measure


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


def get_contours(
    map: np.typing.NDArray[np.float64], map_dist: float, *args, **kwargs
) -> list[np.typing.NDArray[np.float64]]:
    """
    Finds contours in a 2D array at a specified iso-value (map_dist).

    Args:
        map: The 2D NumPy array (float64) from which to extract contours.
        map_dist: The iso-value level at which to trace contours.
        *args: Additional positional arguments passed to skimage.measure.find_contours.
        **kwargs: Additional keyword arguments passed to skimage.measure.find_contours.

    Returns:
        A list of float64 arrays, where each array represents a contour.
        Each contour array is typically shaped (N, 2) with (row, col) coordinates.
    """
    return measure.find_contours(map, map_dist, fully_connected="low", *args, **kwargs)


def get_length(contour: np.ndarray, map_size: int, tolerance: float = 3.0) -> float:
    """
    Returns the total length of all segments in a contour that aren't within
    'tolerance' of the edge of a circle with diameter 'map_size'.

    Args:
        contour: The contour array.
        map_size: The size of the map.
        tolerance: The tolerance value. Defaults to 3.0.

    Returns:
        The total length of the segments.
    """
    offset = np.roll(contour.T, 1, axis=1)
    lengths = np.linalg.norm(contour.T - offset, axis=0)

    center_offset = np.array([[map_size / 2, map_size / 2]])
    radius = np.linalg.norm(contour - center_offset, axis=1)

    valid = radius < (map_size / 2) - tolerance

    return np.sum(lengths[valid])
