from dataclasses import dataclass

from . import Material


@dataclass
class Fiberglass(Material):
    """
    Inherits:
        Material: Base class representing a generic material.

    Attributes:
        None
    """

    density: float = 1700
    yield_strength: float = 200e6
    ultimate_strength: float = 210e6
