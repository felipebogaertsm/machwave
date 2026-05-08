import numpy as np
from skimage import measure


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
