import numpy as np


def replace_array_values(
    arr: np.ndarray,
    to_replace: int | float,
    value: int | float,
) -> np.ndarray:
    """
    Replaces values in a NumPy array with another value.

    Args:
        arr (np.ndarray): The array in which to replace values.
        to_replace (int | float): The value to be replaced.
        value (int | float): The value to replace with.

    Returns:
        np.ndarray: A new array with the values replaced.
    """
    arr = arr.copy()  # Avoid modifying the original array
    arr[arr == to_replace] = value
    return arr
