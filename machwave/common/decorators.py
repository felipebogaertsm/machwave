import functools
import time
import typing
import warnings

F = typing.TypeVar("F", bound=typing.Callable[..., typing.Any])


def validate_assertions(
    exception: typing.Type[Exception],
) -> typing.Callable[[typing.Callable[..., None]], typing.Callable[..., None]]:
    """
    Decorator that validates assertions in a function and raises a specified
    exception if an assertion fails.

    Args:
        exception: The exception class to raise if an assertion fails.

    Returns:
        The decorated function.
    """

    def decorator(function: typing.Callable[..., None]) -> typing.Callable[..., None]:
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
        f: The function to be timed.

    Returns:
        The wrapped function with added timing functionality.
    """

    @functools.wraps(f)
    def wrap(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        start_time = time.time()
        result = f(*args, **kwargs)
        end_time = time.time()
        print(f"\nExecution time: {end_time - start_time:.4f} seconds")
        return result

    return wrap


def check_bounds(lower: float = 0.0, upper: float = 1.0) -> typing.Callable:
    """
    Ensure a correction-factor routine returns a single number in
    [lower, upper].

    Args:
        lower: Inclusive lower bound (default 0.0).
        upper: Inclusive upper bound (default 1.0).

    Raises:
        TypeError: If the decorated function returns a non-float value.
        ValueError: If the result lies outside [lower, upper].
    """
    if lower > upper:
        raise ValueError("lower bound must be <= upper bound")

    def decorator(func: typing.Callable) -> typing.Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # Type check:
            if not isinstance(result, float):
                raise TypeError(
                    f"{func.__name__} should return a float but "
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
    """
    Throws a warning if the decorated function's return value is outside
    the specified range.

    Args:
        lower: The inclusive lower bound.
        upper: The inclusive upper bound.
    Returns:
        The decorated function.
    """

    def _decorator(f):
        @functools.wraps(f)
        def _wrapper(*args, **kw):
            value = f(*args, **kw)
            if not lower <= value <= upper:
                warnings.warn(f"{f.__name__} result {value} outside [{lower}, {upper}]")
            return value

        return _wrapper

    return _decorator
