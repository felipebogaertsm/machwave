import numpy as np
import numpy.typing as npt


def interpolate_with_time(
    time: npt.NDArray[np.number],
    values: npt.NDArray[np.number],
    new_time: float | npt.NDArray[np.number],
) -> float | npt.NDArray[np.number]:
    """Interpolate values at new time points.

    Args:
        time: Original time points.
        values: Values corresponding to original time points.
        new_time: New time points for interpolation.

    Returns:
        A scalar if new_time is of type float, or an array if new_time is an array.
    """
    result = np.interp(new_time, time, values)

    if isinstance(new_time, (int, float)):
        return float(result)

    return result
