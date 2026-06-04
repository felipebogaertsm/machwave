import numpy as np
from numpy.typing import NDArray
from scipy.signal import savgol_filter


def smooth_savitzky_golay(
    values: NDArray[np.float64],
    window_length: int = 31,
    polyorder: int = 5,
) -> NDArray[np.float64]:
    """
    Smooths a one-dimensional array with a Savitzky-Golay filter.

    Args:
        values: One-dimensional array to smooth.
        window_length: Maximum length of the filter window.
        polyorder: Maximum order of the polynomial fitted to each window.

    Returns:
        The smoothed array, or the input unchanged when it is too short to filter.
    """
    values = np.asarray(values, dtype=np.float64)
    if values.size < polyorder + 2:
        return values

    window_length = min(window_length, values.size)
    if window_length % 2 == 0:
        window_length -= 1
    polyorder = min(polyorder, window_length - 2)

    return np.asarray(savgol_filter(values, window_length, polyorder), dtype=np.float64)
