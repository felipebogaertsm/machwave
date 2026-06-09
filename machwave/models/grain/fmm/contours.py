import numpy as np
from skimage import measure


def get_iso_contours(
    regression_field: np.typing.NDArray[np.float64], iso_level: float, *args, **kwargs
) -> list[np.typing.NDArray[np.float64]]:
    """
    Finds contours in a 2D array at a specified iso-value (iso_level).

    Args:
        regression_field: The 2D NumPy array (float64) from which to extract
            contours.
        iso_level: The iso-value level at which to trace contours.
        *args: Additional positional arguments passed to skimage.measure.find_contours.
        **kwargs: Additional keyword arguments passed to skimage.measure.find_contours.

    Returns:
        A list of float64 arrays, where each array represents a contour.
        Each contour array is typically shaped (N, 2) with (row, col) coordinates.
    """
    if np.ma.isMaskedArray(regression_field):
        # Outside-casing cells read as 0, tracing a spurious contour along the
        # wall; lift them above every iso level so only real fronts are traced.
        regression_field = np.ma.filled(
            regression_field, float(regression_field.max()) + 1.0
        )
    return measure.find_contours(
        regression_field, iso_level, fully_connected="low", *args, **kwargs
    )


def get_length(
    contour: np.ndarray, grid_resolution: int, tolerance: float = 1.0
) -> float:
    """
    Return the total length of contour segments away from the disc edge.

    Segments within `tolerance` of the edge of a circle of diameter
    `grid_resolution` are excluded, dropping the casing wall while keeping a
    burning front that has regressed close to it.

    Args:
        contour: The contour array.
        grid_resolution: Grid points per axis of the map.
        tolerance: The tolerance value. Defaults to 1.0.

    Returns:
        The total length of the segments.
    """
    shifted_vertices = np.roll(contour.T, 1, axis=1)
    segment_lengths = np.linalg.norm(contour.T - shifted_vertices, axis=0)

    center_position = np.array([[grid_resolution / 2, grid_resolution / 2]])
    distance_from_center = np.linalg.norm(contour - center_position, axis=1)

    is_interior_contour_segment = (
        distance_from_center < (grid_resolution / 2) - tolerance
    )

    return np.sum(segment_lengths[is_interior_contour_segment])
