# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at me@felipebm.com.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

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
