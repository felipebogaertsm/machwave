# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import pytest

from models.atmosphere import Atmosphere1976
from models.materials.elastics import EPDM
from models.materials.metals import Al6063T5, Steel
from models.propellants.solid import get_solid_propellant_from_name
from models.propulsion.structure.chamber import (
    CombustionChamber,
    BoltedCombustionChamber,
)
from models.propulsion.thermals import ThermalLiner


@pytest.fixture
def propellant_KNDX():
    return get_solid_propellant_from_name("kndx")


@pytest.fixture
def propellant_KNER():
    return get_solid_propellant_from_name("kner")


@pytest.fixture
def propellant_KNSB():
    return get_solid_propellant_from_name("knsb")


@pytest.fixture
def propellant_KNSB_NAKKA():
    return get_solid_propellant_from_name("knsb-nakka")


@pytest.fixture
def propellant_KNSU():
    return get_solid_propellant_from_name("knsu")


@pytest.fixture
def atmosphere_1976():
    return Atmosphere1976()


@pytest.fixture
def thermal_liner_olympus():
    return ThermalLiner(thickness=3e-3, material=EPDM)


@pytest.fixture
def combustion_chamber_olympus(thermal_liner_olympus):
    return CombustionChamber(
        casing_inner_diameter=128.2e-3,
        outer_diameter=141.3e-3,
        liner=thermal_liner_olympus,
        length=1500e-3,
        casing_material=Al6063T5(),
        bulkhead_material=Al6063T5(),
    )


@pytest.fixture
def bolted_combustion_chamber_olympus(thermal_liner_olympus):
    return BoltedCombustionChamber(
        casing_inner_diameter=128.2e-3,
        outer_diameter=141.3e-3,
        liner=thermal_liner_olympus,
        length=1500e-3,
        casing_material=Al6063T5(),
        bulkhead_material=Al6063T5(),
        screw_material=Steel(),
        max_screw_count=30,
        screw_clearance_diameter=9e-3,
        screw_diameter=6.75e-3,
    )
