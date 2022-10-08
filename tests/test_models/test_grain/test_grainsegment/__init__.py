# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at me@felipebm.com.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import pytest

from rocketsolver.models.propulsion.grain import GrainGeometryError
from rocketsolver.models.propulsion.grain import GrainSegment


def test_grain_segment_geometry_validation():
    # Control group:
    _ = GrainSegment(
        spacing=10e-3,
        inhibited_ends=0,
    )

    _ = GrainSegment(
        spacing=10e-3,
        inhibited_ends=1,
    )

    _ = GrainSegment(
        spacing=10e-3,
        inhibited_ends=2,
    )

    # Invalid inhibited ends:
    with pytest.raises(GrainGeometryError):
        _ = GrainSegment(
            spacing=10e-3,
            inhibited_ends=3,
        )

    # Negative spacing:
    with pytest.raises(GrainGeometryError):
        _ = GrainSegment(
            spacing=-10e-3,
            inhibited_ends=0,
        )
