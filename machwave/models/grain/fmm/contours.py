from collections.abc import Callable

import numpy as np
from numpy.typing import NDArray
from scipy.ndimage import distance_transform_edt

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


def extrapolate_past_wall(
    regression_values: NDArray[np.float64],
    excluded_mask: NDArray[np.bool_],
    grid_spacing: tuple[float, ...],
) -> NDArray[np.float64]:
    """Continue the regression slope past the wall so no iso level lands on it."""
    excluded_cells = np.nonzero(excluded_mask)
    nearest_cell_map = np.asarray(
        distance_transform_edt(
            excluded_mask,
            sampling=grid_spacing,
            return_distances=False,
            return_indices=True,
        )
    )
    nearest_cell = nearest_cell_map[:, excluded_mask]
    offset = np.stack(excluded_cells) - nearest_cell
    step = np.sign(offset)
    shape = np.asarray(excluded_mask.shape)[:, np.newaxis]
    behind_cell = nearest_cell - step
    has_behind_cell = np.all((behind_cell >= 0) & (behind_cell < shape), axis=0)
    behind_cell = np.clip(behind_cell, 0, shape - 1)
    has_behind_cell &= ~excluded_mask[tuple(behind_cell)]

    nearest_value = regression_values[tuple(nearest_cell)]
    behind_value = np.where(
        has_behind_cell, regression_values[tuple(behind_cell)], nearest_value
    )
    spacing = np.asarray(grid_spacing)[:, np.newaxis]
    slope = (nearest_value - behind_value) / np.linalg.norm(step * spacing, axis=0)

    extrapolated = regression_values.copy()
    extrapolated[excluded_cells] = nearest_value + slope * np.linalg.norm(
        offset * spacing, axis=0
    )
    return extrapolated


def get_burning_front_contours(
    extrapolated_field: NDArray[np.float64],
    iso_level: float,
    is_on_burning_propellant: Callable[[NDArray[np.float64]], NDArray[np.bool_]],
) -> list[NDArray[np.float64]]:
    """
    Trace an iso level and keep only the pieces that run over burning propellant.

    The field must already be extrapolated past the excluded cells (see
    `extrapolate_past_wall`), so the front crosses an inhibited wall instead of
    being traced along it. Each traced contour is then cut wherever a segment
    midpoint leaves the burning propellant, leaving the front up to the wall and
    nothing past it.

    Args:
        extrapolated_field: 2D regression field with no artificial step at the
            excluded cells.
        iso_level: The iso-value level at which to trace contours.
        is_on_burning_propellant: Maps `(N, 2)` `(row, col)` points to a boolean
            array, True where the propellant can burn.

    Returns:
        Open or closed `(N, 2)` polylines in `(row, col)` cell coordinates.

    Raises:
        MissingOptionalDependencyError: If the `fmm` extra is not installed.
    """
    measure = extras.require("skimage.measure", extras.FMM)

    burning_pieces = []
    for contour in measure.find_contours(
        extrapolated_field, iso_level, fully_connected="low"
    ):
        segment_midpoints = (contour[1:] + contour[:-1]) / 2
        segment_is_burning = is_on_burning_propellant(segment_midpoints)

        run_edges = np.flatnonzero(np.diff(np.r_[0, segment_is_burning, 0]))
        for first_segment, end_segment in zip(run_edges[::2], run_edges[1::2]):
            burning_pieces.append(contour[first_segment : end_segment + 1])
    return burning_pieces


def get_length(contour: np.ndarray) -> float:
    """
    Return the length of a contour polyline, in cells.

    A closed contour repeats its first vertex at the end, so its length includes
    the closing segment. An open contour is not closed with a chord.

    Args:
        contour: The `(N, 2)` contour array.

    Returns:
        The total length of the contour segments, in cells.
    """
    return float(np.sum(np.linalg.norm(np.diff(contour, axis=0), axis=1)))
