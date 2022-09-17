# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import pytest

from rocketsolver.models.fuselage.components.fins.trapezoidal import (
    TrapezoidalFins,
)
from rocketsolver.models.materials.metals import Al6061T6


@pytest.fixture
def trapezoidal_fins_1():
    return TrapezoidalFins(
        material=Al6061T6(),
        center_of_gravity=0.5,
        mass=0.1,
        thickness=0.002,
        count=4,
        rugosity=10e-6,
        base_length=30e-3,
        tip_length=20e-3,
        average_span=15e-3,
        height=20e-3,
        body_diameter=117e-3,
    )


def test_trapezoidal_fins_1(trapezoidal_fins_1):
    assert trapezoidal_fins_1.get_area() == pytest.approx(0.0005, 1e-4)
