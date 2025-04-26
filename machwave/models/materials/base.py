from abc import ABC
from dataclasses import dataclass


@dataclass
class Material(ABC):
    """
    Base class representing a generic material.

    Attributes:
        density: Density of the material.
        yield_strength: Yield strength of the material.
        ultimate_strength: Ultimate strength of the material.
    """

    density: float
    yield_strength: float
    ultimate_strength: float


@dataclass
class NozzleMaterial(Material):
    """
    Base class for a Nozzle material.

    Contains all attributes from the Material class, adding c_1 and c_2 for
    calculating isentropic flow correction factors. These special parameters
    are referenced in the a015140 paper.

    Attributes:
        c_1: Coefficient related to heat transfer properties of a BATES
            motor.
        c_2: Time constant obtained from the analysis of the transient
            heating of a standard BATES motor.
    """

    c_1: float
    c_2: float
