class Material:
    def __init__(
        self,
        density: float,
        yield_strength: float,
        ultimate_strength: float,
    ) -> None:
        self.density = density
        self.yield_strength = yield_strength
        self.ultimate_strength = ultimate_strength


class NozzleMaterial(Material):
    """
    Base class for a Nozzle material.

    Contains all attributes from the Material class, adding special info for
    parameters that need to be used when calculating isentropic flow correction
    factors.

    These special parameters are C1 and C2, referenced in a015140 paper.
    """

    def __init__(
        self,
        density: float,
        yield_strength: float,
        ultimate_strength: float,
        C1: float,
        C2: float,
    ) -> None:
        self.C1 = C1
        self.C2 = C2

        super().__init__(density, yield_strength, ultimate_strength)
