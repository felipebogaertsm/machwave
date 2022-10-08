# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at me@felipebm.com.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import pytest

from rocketsolver.models.propulsion.grain.fmm.d_grain import DGrainSegment
from rocketsolver.models.propulsion.grain import GrainGeometryError


def test_dgrain_segment_geometry_validation():
    # Control group:
    _ = DGrainSegment(
        outer_diameter=100e-3,
        slot_offset=30e-3,
        length=120e-3,
        spacing=10e-3,
    )

    # Negative slot offset:
    with pytest.raises(GrainGeometryError):
        _ = DGrainSegment(
            outer_diameter=100e-3,
            slot_offset=-30e-3,
            length=120e-3,
            spacing=10e-3,
        )

    # Slot offset larget than segment radius:
    with pytest.raises(GrainGeometryError):
        _ = DGrainSegment(
            outer_diameter=100e-3,
            slot_offset=55e-3,
            length=120e-3,
            spacing=10e-3,
        )
