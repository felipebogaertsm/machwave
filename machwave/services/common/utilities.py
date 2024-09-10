import time
from typing import Callable, Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def obtain_attributes_from_object(obj) -> dict:
    try:
        return vars(obj)
    except TypeError:  # if does not have __dict__ method
        return {}


def timing(f: F) -> F:
    """
    Decorator to print the execution time of a function.

    Args:
        f (Callable): The function to be timed.

    Returns:
        Callable: The wrapped function with added timing functionality.
    """

    def wrap(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        result = f(*args, **kwargs)
        end_time = time.time()
        print(f"\nExecution time: {end_time - start_time:.4f} seconds")
        return result

    return wrap
