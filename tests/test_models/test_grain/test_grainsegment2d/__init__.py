# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at me@felipebm.com.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import pytest

from rocketsolver.models.propulsion.grain import GrainGeometryError
from rocketsolver.models.propulsion.grain import GrainSegment2D


def test_grain_segment_2d_geometry_validation():
    # Control group:
    _ = GrainSegment2D(
        outer_diameter=100e-3,
        length=120e-3,
        spacing=10e-3,
    )

    # Negative outer diameter:
    with pytest.raises(GrainGeometryError):
        _ = GrainSegment2D(
            outer_diameter=-100e-3,
            length=120e-3,
            spacing=10e-3,
        )

    # Negative length:
    with pytest.raises(GrainGeometryError):
        _ = GrainSegment2D(
            outer_diameter=100e-3,
            length=-120e-3,
            spacing=10e-3,
        )

    # Negative spacing:
    with pytest.raises(GrainGeometryError):
        _ = GrainSegment2D(
            outer_diameter=100e-3,
            length=120e-3,
            spacing=-10e-3,
        )
