# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import pytest
import numpy as np

from rocketsolver.models.fuselage import Fuselage3D
from rocketsolver.models.fuselage.components.body import (
    BodySegment,
    CylindricalBody,
)
from rocketsolver.models.fuselage.components.fins import Fins
from rocketsolver.models.fuselage.components.fins.trapezoidal import (
    TrapezoidalFins,
)
from rocketsolver.models.fuselage.components.nosecones import NoseCone
from rocketsolver.models.fuselage.components.nosecones.haack import (
    HaackSeriesNoseCone,
)
from rocketsolver.models.materials.composites import Fiberglass
from rocketsolver.models.materials.metals import Al6061T6


@pytest.fixture
def concorde_nosecone() -> NoseCone:
    return HaackSeriesNoseCone(
        material=Fiberglass(),
        mass=1.147,
        center_of_gravity=0.3,
        length=0.5,
        base_diameter=164e-3,
        C=1 / 3,
    )


@pytest.fixture
def concorde_fins() -> Fins:
    return TrapezoidalFins(
        material=Al6061T6,
        mass=0.3,
        center_of_gravity=0.2,
        thickness=2,
        count=4,
        rugosity=60e-6,
        base_length=30e-3,
        tip_length=20e-3,
        average_span=25e-3,
        height=20e-3,
        body_diameter=164e-3,
    )


@pytest.fixture
def concorde_body(concorde_fins: Fins) -> BodySegment:
    return CylindricalBody(
        material=Fiberglass(),
        mass=10,
        center_of_gravity=0.2,
        length=3.1,
        outer_diameter=164e-3,
        rugosity=60e-6,
        constant_K=0,
        fins=concorde_fins,
    )


@pytest.fixture
def concorde_fuselage3d(
    concorde_nosecone: NoseCone, concorde_body: BodySegment
) -> Fuselage3D:
    fuselage = Fuselage3D(
        nose_cone=concorde_nosecone,
        mass_without_motor=28,
        inertia_tensor=np.array([[0, 0, 0], [0, 0, 0], [0, 0, 0]]),
    )

    fuselage.add_body_segment(concorde_body)

    return fuselage
