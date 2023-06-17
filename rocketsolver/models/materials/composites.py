from dataclasses import dataclass

from . import Material


@dataclass
class Fiberglass(Material):
    """
    Fiberglass material class derived from the Material base class.

    This class represents a specific type of material, Fiberglass, which
    inherits properties from the Material base class. It provides default
    values for the density, yield strength, and ultimate strength specific to
    Fiberglass.

    Inherits:
        Material: Base class representing a generic material.

    Attributes:
        None
    """

    density: float = 1700
    yield_strength: float = 200e6
    ultimate_strength: float = 210e6
