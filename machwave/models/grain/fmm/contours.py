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


def get_length(contour: np.ndarray) -> float:
    """
    Return the total length of a closed contour, in cells.

    Cells outside the casing are lifted above every iso level before tracing,
    so a contour follows the burning front only, right up to the casing.

    Args:
        contour: The contour array.

    Returns:
        The total length of the contour segments, in cells.
    """
    shifted_vertices = np.roll(contour.T, 1, axis=1)
    segment_lengths = np.linalg.norm(contour.T - shifted_vertices, axis=0)

    return float(np.sum(segment_lengths))
