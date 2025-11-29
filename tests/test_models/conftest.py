import pytest

from machwave.models.atmosphere import Atmosphere1976
from machwave.models.propulsion.propellants import (
    KNDX,
    KNER,
    KNSB,
    KNSB_NAKKA,
    KNSU,
)
from machwave.models.propulsion.thrust_chamber import (
    CombustionChamber,
)


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
def combustion_chamber_olympus():
    return CombustionChamber(
        casing_inner_diameter=128.2e-3,
        casing_outer_diameter=141.3e-3,
        thermal_liner_thickness=3e-3,
        internal_length=1500e-3,
    )
