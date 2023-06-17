from typing import Callable


def validate_assertions(exception: Exception) -> Callable:
    def decorator(function: Callable[[], None]) -> Callable:
        def wrapper(*args, **kwargs):
            try:
                function(*args, **kwargs)
            except AssertionError as e:
                print(e)
                print("\n\n\n")
                raise exception("Error")

        return wrapper

    return decorator
