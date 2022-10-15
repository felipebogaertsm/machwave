# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at me@felipebm.com.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import pytest

from rocketsolver.models.propulsion.grain import GrainGeometryError
from rocketsolver.models.propulsion.grain.geometries import StarGrainSegment


def test_star_segment_geometry_validation():
    # Control group:
    _ = StarGrainSegment(
        outer_diameter=41e-3,
        length=0.5,
        number_of_points=5,
        point_length=15e-3,
        point_width=10e-3,
        spacing=10e-3,
    )

    # Negative number of points:
    with pytest.raises(GrainGeometryError):
        _ = StarGrainSegment(
            outer_diameter=41e-3,
            length=0.5,
            number_of_points=-5,
            point_length=15e-3,
            point_width=10e-3,
            spacing=10e-3,
        )

    # Too many points:
    with pytest.raises(GrainGeometryError):
        _ = StarGrainSegment(
            outer_diameter=41e-3,
            length=0.5,
            number_of_points=13,
            point_length=15e-3,
            point_width=10e-3,
            spacing=10e-3,
        )

    # Negative point length:
    with pytest.raises(GrainGeometryError):
        _ = StarGrainSegment(
            outer_diameter=41e-3,
            length=0.5,
            number_of_points=5,
            point_length=-15e-3,
            point_width=10e-3,
            spacing=10e-3,
        )

    # Negative point width:
    with pytest.raises(GrainGeometryError):
        _ = StarGrainSegment(
            outer_diameter=41e-3,
            length=0.5,
            number_of_points=5,
            point_length=15e-3,
            point_width=-10e-3,
            spacing=10e-3,
        )
