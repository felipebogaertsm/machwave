import typing


def get_object_dict(obj: typing.Any) -> dict[str, typing.Any]:
    """
    Extract the attribute dictionary from an object.

    Args:
        obj: Any Python object to inspect.

    Returns:
        A dictionary mapping attribute names to their values, or an empty
        dictionary if the object has no __dict__.

    Examples:
        >>> class Example:
        ...     def __init__(self):
        ...         self.x = 1
        ...         self.y = 2
        >>> get_object_dict(Example())
        {'x': 1, 'y': 2}
    """
    try:
        return vars(obj)
    except TypeError:
        return {}
