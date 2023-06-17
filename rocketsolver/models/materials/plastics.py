from . import Material


class EpoxiResin(Material):
    """
    EpoxiResin material class derived from the Material base class.

    This class represents a specific type of material, EpoxiResin, which
    inherits properties from the Material base class. It provides default
    values for the density, yield strength, and ultimate strength specific to
    EpoxiResin.

    Inherits:
        Material: Base class representing a generic material.

    Attributes:
        None
    """

    def __init__(self) -> None:
        """
        Initialize an EpoxiResin object.

        This constructor sets the default values for the density, yield
        strength, and ultimate strength of EpoxiResin.

        Args:
            None

        Returns:
            None
        """
        super().__init__(
            density=1100, yield_strength=60e6, ultimate_strength=60e6
        )
