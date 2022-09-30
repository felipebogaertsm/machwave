# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at me@felipebm.com.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from rocketsolver.models.fuselage import Fuselage3D


def test_fuselage_3d_concorde(concorde_fuselage3d: Fuselage3D) -> None:
    concorde_fuselage3d.is_valid
