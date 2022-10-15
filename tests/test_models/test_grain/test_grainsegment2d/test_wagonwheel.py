# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at me@felipebm.com.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import pytest

from rocketsolver.models.propulsion.grain import GrainGeometryError
from rocketsolver.models.propulsion.grain.geometries import (
    WagonWheelGrainSegment,
)


def test_star_segment_geometry_validation():
    # Control group:
    _ = WagonWheelGrainSegment(
        outer_diameter=41e-3,
        length=0.5,
        core_diameter=8e-3,
        number_of_ports=6,
        port_inner_diameter=15e-3,
        port_outer_diameter=35e-3,
        port_angular_width=45,
        spacing=10e-3,
    )

    # Negative core diameter:
    with pytest.raises(GrainGeometryError):
        _ = WagonWheelGrainSegment(
            outer_diameter=41e-3,
            length=0.5,
            core_diameter=-8e-3,
            number_of_ports=-1,
            port_inner_diameter=15e-3,
            port_outer_diameter=35e-3,
            port_angular_width=45,
            spacing=10e-3,
        )

    # Port inner diameter smaller than core diameter:
    with pytest.raises(GrainGeometryError):
        _ = WagonWheelGrainSegment(
            outer_diameter=41e-3,
            length=0.5,
            core_diameter=8e-3,
            number_of_ports=-1,
            port_inner_diameter=7e-3,
            port_outer_diameter=35e-3,
            port_angular_width=45,
            spacing=10e-3,
        )

    # Port outer diameter smaller than inner diameter:
    with pytest.raises(GrainGeometryError):
        _ = WagonWheelGrainSegment(
            outer_diameter=41e-3,
            length=0.5,
            core_diameter=8e-3,
            number_of_ports=-1,
            port_inner_diameter=15e-3,
            port_outer_diameter=12e-3,
            port_angular_width=45,
            spacing=10e-3,
        )

    # Negative number of ports:
    with pytest.raises(GrainGeometryError):
        _ = WagonWheelGrainSegment(
            outer_diameter=41e-3,
            length=0.5,
            core_diameter=8e-3,
            number_of_ports=-1,
            port_inner_diameter=15e-3,
            port_outer_diameter=35e-3,
            port_angular_width=45,
            spacing=10e-3,
        )

    # Too many points:
    with pytest.raises(GrainGeometryError):
        _ = WagonWheelGrainSegment(
            outer_diameter=41e-3,
            length=0.5,
            core_diameter=8e-3,
            number_of_ports=13,
            port_inner_diameter=15e-3,
            port_outer_diameter=35e-3,
            port_angular_width=45,
            spacing=10e-3,
        )

    # Negative port angle:
    with pytest.raises(GrainGeometryError):
        _ = WagonWheelGrainSegment(
            outer_diameter=41e-3,
            length=0.5,
            core_diameter=8e-3,
            number_of_ports=6,
            port_inner_diameter=15e-3,
            port_outer_diameter=35e-3,
            port_angular_width=-1,
            spacing=10e-3,
        )

    # Port angle too large:
    with pytest.raises(GrainGeometryError):
        _ = WagonWheelGrainSegment(
            outer_diameter=41e-3,
            length=0.5,
            core_diameter=8e-3,
            number_of_ports=6,
            port_inner_diameter=15e-3,
            port_outer_diameter=35e-3,
            port_angular_width=61,
            spacing=10e-3,
        )
