"""
The models.propulsion.propellants module contains classes that allow the user to
represent a chemical propellant. There are three main components in it, from least
to most primitive:

- Properties: classes that contain different propellant thermochemical properties.
These do not contain operational attributes, such as chamber pressure or instant
burn rate, but rather contain propellant attributes from those states.
- Categories: classes that represent different physical states of chemical propellants.
They can be solid, biliquid, monoliquid, or hybrid.
- Formulations: ready-made objects that represent a propellant combination. For example
the solid propellant KNSB, or the liquid propellants LH2/LOX.
"""

from machwave.models.propulsion.propellants.categories import (
    BiliquidPropellant,
    BurnRateOutOfBoundsError,
    FixedSolidPropellant,
    FormulationBasedSolidPropellant,
    Propellant,
    SolidPropellant,
)
from machwave.models.propulsion.propellants.properties import (
    ThermochemicalProperties,
)

__all__ = [
    # Base classes
    "Propellant",
    "BurnRateOutOfBoundsError",
    # Properties
    "ThermochemicalProperties",
    # Categories
    "BiliquidPropellant",
    "SolidPropellant",
    "FixedSolidPropellant",
    "FormulationBasedSolidPropellant",
]
