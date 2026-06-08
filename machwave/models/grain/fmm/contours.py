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
    if np.ma.isMaskedArray(map):
        # Outside-casing cells read as 0, tracing a spurious contour along the
        # wall; lift them above every iso level so only real fronts are traced.
        map = np.ma.filled(map, float(map.max()) + 1.0)
    return measure.find_contours(map, map_dist, fully_connected="low", *args, **kwargs)


def get_length(contour: np.ndarray, map_size: int, tolerance: float = 1.0) -> float:
    """
    Return the total length of contour segments away from the disc edge.

    Segments within `tolerance` of the edge of a circle of diameter `map_size`
    are excluded, dropping the casing wall while keeping a burning front that
    has regressed close to it.

    Args:
        contour: The contour array.
        map_size: The size of the map.
        tolerance: The tolerance value. Defaults to 1.0.

    Returns:
        The total length of the segments.
    """
    offset = np.roll(contour.T, 1, axis=1)
    lengths = np.linalg.norm(contour.T - offset, axis=0)

    center_offset = np.array([[map_size / 2, map_size / 2]])
    radius = np.linalg.norm(contour - center_offset, axis=1)

    valid = radius < (map_size / 2) - tolerance

    return np.sum(lengths[valid])
