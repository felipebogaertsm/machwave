# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at me@felipebm.com.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import pytest

from rocketsolver.models.propulsion.grain.fmm.rod_and_tube import (
    RodAndTubeGrainSegment,
)
from rocketsolver.models.propulsion.grain import GrainGeometryError


def test_rodandtube_segment_geometry_validation():
    # Control group:
    _ = RodAndTubeGrainSegment(
        outer_diameter=100e-3,
        rod_outer_diameter=30e-3,
        tube_inner_diameter=40e-3,
        length=120e-3,
        spacing=10e-3,
    )

    # Negative rod outer diameter:
    with pytest.raises(GrainGeometryError):
        _ = RodAndTubeGrainSegment(
            outer_diameter=100e-3,
            rod_outer_diameter=-30e-3,
            tube_inner_diameter=40e-3,
            length=120e-3,
            spacing=10e-3,
        )

    # Negative tube inner diameter:
    with pytest.raises(GrainGeometryError):
        _ = RodAndTubeGrainSegment(
            outer_diameter=100e-3,
            rod_outer_diameter=30e-3,
            tube_inner_diameter=-40e-3,
            length=120e-3,
            spacing=10e-3,
        )

    # Rod outer diameter larger than tube inner diameter:
    with pytest.raises(GrainGeometryError):
        _ = RodAndTubeGrainSegment(
            outer_diameter=100e-3,
            rod_outer_diameter=50e-3,
            tube_inner_diameter=40e-3,
            length=120e-3,
            spacing=10e-3,
        )
