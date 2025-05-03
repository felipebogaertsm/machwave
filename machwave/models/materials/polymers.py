from dataclasses import dataclass

from .base import Material


@dataclass
class EPDM(Material):
    """
    EPDM (Ethylene Propylene Diene Monomer) material class.

    Source:
    https://www.matweb.com/search/datasheet.aspx?matguid=f8e3355cc2c541fbb0174960466819c0&ckck=1
    """

    density: float = 1500
    yield_strength: float = 0
    ultimate_strength: float = 17e6


class EpoxiResin(Material):
    """
    EpoxiResin material class.
    """

    def __init__(self) -> None:
        """
        Initialize an EpoxiResin object.

        This constructor sets the default values for the density, yield
        strength, and ultimate strength of EpoxiResin.
        """
        super().__init__(density=1100, yield_strength=60e6, ultimate_strength=60e6)
