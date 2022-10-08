# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at me@felipebm.com.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from typing import Callable

from rocketsolver.models.atmosphere import Atmosphere, Atmosphere1976


def test_atmosphere1976_up_to_karman_line(
    test_atmosphere_up_to_karman_line: Callable[[Atmosphere], None]
) -> None:
    test_atmosphere_up_to_karman_line(atmosphere=Atmosphere1976())
