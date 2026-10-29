import numpy as np

import machwave.common.extras as extras


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

    Raises:
        MissingOptionalDependencyError: If the `fmm` extra is not installed.
    """
    measure = extras.require("skimage.measure", extras.FMM)

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
    Return the length of a contour polyline, in cells.

    A closed contour repeats its first point at the end, so open pieces are not
    closed with a chord.

    Args:
        contour: The contour array.

    Returns:
        The total length of the contour segments, in cells.
    """
    return float(np.sum(np.linalg.norm(np.diff(contour, axis=0), axis=1)))
