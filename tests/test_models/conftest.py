from pathlib import Path

import pytest

import machwave.models.propellants.formulations as propellant_formulations

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
    return propellant_formulations.get_propellant_from_json(
        FORMULATIONS_DIR / "kndx.json"
    )


@pytest.fixture
def propellant_KNER():
    return propellant_formulations.get_propellant_from_json(
        FORMULATIONS_DIR / "kner.json"
    )


@pytest.fixture
def propellant_KNSB():
    return propellant_formulations.get_propellant_from_json(
        FORMULATIONS_DIR / "knsb.json"
    )


@pytest.fixture
def propellant_KNSB_NAKKA():
    return propellant_formulations.get_propellant_from_json(
        FORMULATIONS_DIR / "knsb_nakka.json"
    )


@pytest.fixture
def propellant_KNSU():
    return propellant_formulations.get_propellant_from_json(
        FORMULATIONS_DIR / "knsu.json"
    )
