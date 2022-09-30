# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at me@felipebm.com.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import pytest

from rocketsolver.models.fuselage.components.nosecones.haack import (
    HaackSeriesNoseCone,
)
from rocketsolver.models.materials.metals import Al6061T6


@pytest.fixture
def haack_nosecone_1():
    return HaackSeriesNoseCone(
        material=Al6061T6(),
        center_of_gravity=0.0,
        mass=1,
        length=0.5,
        base_diameter=117e-3,
        C=1 / 3,
    )


def test_haackseriesnosecone_no_surface_area_given(
    haack_nosecone_1: HaackSeriesNoseCone,
):
    """
    Tests methods of HaackSeriesNoseCone class when no surface area is given.
    The class should be able to calculate the surface area.
    """
    nosecone = haack_nosecone_1

    assert nosecone is not None

    # Verifying surface area calculation:
    nosecone_surface_area = nosecone.surface_area
    assert nosecone_surface_area > 0
