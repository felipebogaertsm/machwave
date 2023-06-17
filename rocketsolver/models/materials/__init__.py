from dataclasses import dataclass


@dataclass
class Material:
    """
    Base class representing a generic material.

    Attributes:
        density (float): Density of the material.
        yield_strength (float): Yield strength of the material.
        ultimate_strength (float): Ultimate strength of the material.
    """

    density: float
    yield_strength: float
    ultimate_strength: float


@dataclass
class NozzleMaterial(Material):
    """
    Base class for a Nozzle material.

    Contains all attributes from the Material class, adding special info for
    parameters that need to be used when calculating isentropic flow correction
    factors.

    These special parameters are C1 and C2, referenced in the a015140 paper.

    Attributes:
        C1 (float): Parameter used in isentropic flow correction factor
            calculations.
        C2 (float): Parameter used in isentropic flow correction factor
            calculations.
    """

    C1: float
    C2: float
