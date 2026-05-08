from pathlib import Path

import pytest

from machwave.models.propellants.formulations import get_propellant_from_json

from tests.factories import CombustionChamberFactory

FORMULATIONS_DIR = (
    Path(__file__).parent.parent.parent
    / "machwave"
    / "models"
    / "propulsion"
    / "propellants"
    / "formulations"
    / "solid"
)


@pytest.fixture
def propellant_KNDX():
    return get_propellant_from_json(FORMULATIONS_DIR / "kndx.json")


@pytest.fixture
def propellant_KNER():
    return get_propellant_from_json(FORMULATIONS_DIR / "kner.json")


@pytest.fixture
def propellant_KNSB():
    return get_propellant_from_json(FORMULATIONS_DIR / "knsb.json")


@pytest.fixture
def propellant_KNSB_NAKKA():
    return get_propellant_from_json(FORMULATIONS_DIR / "knsb_nakka.json")


@pytest.fixture
def propellant_KNSU():
    return get_propellant_from_json(FORMULATIONS_DIR / "knsu.json")


@pytest.fixture
def combustion_chamber_olympus():
    return CombustionChamberFactory.build(
        casing_inner_diameter=128.2e-3,
        casing_outer_diameter=141.3e-3,
        thermal_liner_thickness=3e-3,
        internal_length=1500e-3,
    )
