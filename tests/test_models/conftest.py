import pytest

from rocketsolver.models.atmosphere import Atmosphere1976
from rocketsolver.models.materials.elastics import EPDM
from rocketsolver.models.materials.metals import Al6063T5, Steel
from rocketsolver.models.propulsion.propellants.solid import (
    KNSB,
    KNSB_NAKKA,
    KNDX,
    KNER,
    KNSU,
)
from rocketsolver.models.propulsion.structure.chamber import (
    CombustionChamber,
    BoltedCombustionChamber,
)
from rocketsolver.models.propulsion.thermals import ThermalLiner


@pytest.fixture
def propellant_KNDX():
    return KNDX


@pytest.fixture
def propellant_KNER():
    return KNER


@pytest.fixture
def propellant_KNSB():
    return KNSB


@pytest.fixture
def propellant_KNSB_NAKKA():
    return KNSB_NAKKA


@pytest.fixture
def propellant_KNSU():
    return KNSU


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
