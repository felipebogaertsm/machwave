"""Solid propellant formulation instances."""

from pathlib import Path

from .base import get_propellant_from_json

_FORMULATIONS_DIR = Path(__file__).parent / "solid"

KNDX = get_propellant_from_json(_FORMULATIONS_DIR / "kndx.json")
KNSB = get_propellant_from_json(_FORMULATIONS_DIR / "knsb.json")
KNSB_NAKKA = get_propellant_from_json(_FORMULATIONS_DIR / "knsb_nakka.json")
KNSU = get_propellant_from_json(_FORMULATIONS_DIR / "knsu.json")
KNER = get_propellant_from_json(_FORMULATIONS_DIR / "kner.json")
RNX_57 = get_propellant_from_json(_FORMULATIONS_DIR / "rnx_57.json")
RNX_71V = get_propellant_from_json(_FORMULATIONS_DIR / "rnx_71v.json")
MIT_CHERRY_LIMEADE = get_propellant_from_json(
    _FORMULATIONS_DIR / "mit_cherry_limeade.json"
)
