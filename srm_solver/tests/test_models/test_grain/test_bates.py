# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.


import pytest

from models.motor.grain.bates import BatesSegment
from models.motor.grain import GrainGeometryError, Grain


def test_bates_grains_with_different_outer_diameters():
    segment_1 = BatesSegment(
        outer_diameter=100e-3,
        core_diameter=30e-3,
        length=120e-3,
        spacing=10e-3,
    )

    segment_2 = BatesSegment(
        outer_diameter=101e-3,
        core_diameter=30e-3,
        length=120e-3,
        spacing=10e-3,
    )

    grain = Grain()

    # Trying to add segments with diffetent ODs:
    grain.add_segment(segment_1)
    with pytest.raises(GrainGeometryError):
        grain.add_segment(segment_2)

    # Changing ODs and checking if it works:
    segment_2.outer_diameter = segment_1.outer_diameter
    grain.add_segment(segment_2)


def test_grain_total_length_property(bates_grain_olympus):
    grain = bates_grain_olympus
    total_length = 0

    for segment in grain.segments:
        total_length += segment.length + segment.spacing

    assert grain.total_length == total_length
