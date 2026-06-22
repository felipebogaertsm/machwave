import functools
import time
import typing

F = typing.TypeVar("F", bound=typing.Callable[..., typing.Any])


def timing(f: F) -> F:
    """
    Decorator to print the execution time of a function.

    Args:
        f: The function to be timed.

    Returns:
        The wrapped function with added timing functionality.
    """

    @functools.wraps(f)
    def wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        start_time = time.time()
        result = f(*args, **kwargs)
        end_time = time.time()
        print(f"\nExecution time: {end_time - start_time:.4f} seconds")
        return result

    return typing.cast(F, wrapper)
