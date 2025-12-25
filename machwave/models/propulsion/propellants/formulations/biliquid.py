"""Biliquid propellant formulation instances."""

from pathlib import Path

from .base import get_propellant_from_json

_FORMULATIONS_DIR = Path(__file__).parent / "biliquid"

LOX_LH2_6_0 = get_propellant_from_json(_FORMULATIONS_DIR / "lox_lh2_6_0.json")
