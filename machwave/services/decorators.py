import time
from typing import Callable, Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def validate_assertions(exception: Exception) -> Callable:
    """
    Decorator that validates assertions in a function and raises a specified
    exception if an assertion fails.

    Args:
        exception (Exception): The exception to raise if an assertion fails.

    Returns:
        Callable: The decorated function.
    """

    def decorator(function: Callable[..., None]) -> Callable[..., None]:
        """
        Inner decorator function that wraps the input function and performs
        the assertion validation.

        Args:
            function (Callable): The function to decorate.

        Returns:
            Callable: The wrapped function.
        """

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

    def wrap(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        result = f(*args, **kwargs)
        end_time = time.time()
        print(f"\nExecution time: {end_time - start_time:.4f} seconds")
        return result

    return wrap
