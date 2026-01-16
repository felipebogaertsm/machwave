import numpy as np
import numpy.typing as npt


def replace_array_values(
    arr: npt.NDArray[np.float_ | np.int_],
    to_replace: int | float,
    value: int | float,
) -> npt.NDArray[np.float_ | np.int_]:
    """
    Replaces values in a NumPy array with another value.

    Args:
        arr: The array in which to replace values.
        to_replace: The value to be replaced.
        value: The value to replace with.

    Returns:
        A new array with the values replaced.
    """
    arr = arr.copy()
    arr[arr == to_replace] = value
    return arr
