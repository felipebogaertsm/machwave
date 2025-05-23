import functools
import time
import warnings
from typing import Any, Callable, Type, TypeVar

F = TypeVar("F", bound=Callable[..., Any])
Number = int | float


def validate_assertions(
    exception: Type[Exception],
) -> Callable[[Callable[..., None]], Callable[..., None]]:
    """
    Decorator that validates assertions in a function and raises a specified
    exception if an assertion fails.

    Args:
        exception (Type[Exception]): The exception class to raise if an assertion fails.

    Returns:
        Callable: The decorated function.
    """

    def decorator(function: Callable[..., None]) -> Callable[..., None]:
        @functools.wraps(function)
        def wrapper(*args, **kwargs) -> None:
            try:
                function(*args, **kwargs)
            except AssertionError as e:
                print(e)
                print("\n\n\n")
                raise exception("Error") from e

        return wrapper

    return decorator


def timing(f: F) -> F:
    """
    Decorator to print the execution time of a function.

    Args:
        f (Callable): The function to be timed.

    Returns:
        Callable: The wrapped function with added timing functionality.
    """

    @functools.wraps(f)
    def wrap(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        result = f(*args, **kwargs)
        end_time = time.time()
        print(f"\nExecution time: {end_time - start_time:.4f} seconds")
        return result

    return wrap  # type: ignore


def check_bounds(lower: Number = 0.0, upper: Number = 1.0) -> Callable:
    """
    Ensure a correction-factor routine returns a single number in
    [lower, upper].

    Args:
        lower (Number): Inclusive lower bound (default 0.0).
        upper (Number): Inclusive upper bound (default 1.0).

    Raises:
        TypeError: If the decorated function returns a non-numeric value.
        ValueError: If the numeric result lies outside ``[lower, upper]``.
    """
    if lower > upper:
        raise ValueError("lower bound must be ≤ upper bound")

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # Type check:
            if not isinstance(result, Number):
                raise TypeError(
                    f"{func.__name__} should return a real number; "
                    f"got {type(result).__name__!s}"
                )

            # Range check:
            if not (lower <= result <= upper):
                raise ValueError(
                    f"{func.__name__} returned {result}, "
                    f"which is outside [{lower}, {upper}]"
                )
            return result

        return wrapper

    return decorator


def warn_if_outside_range(lower: float, upper: float):
    def _decorator(f):
        @functools.wraps(f)
        def _wrapper(*args, **kw):
            value = f(*args, **kw)
            if not lower <= value <= upper:
                warnings.warn(f"{f.__name__} result {value} outside [{lower}, {upper}]")
            return value

        return _wrapper

    return _decorator
