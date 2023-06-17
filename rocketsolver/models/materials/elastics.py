from dataclasses import dataclass

from . import Material


@dataclass
class EPDM(Material):
    """
    EPDM (Ethylene Propylene Diene Monomer) material class derived from the
    Material base class.

    Data obtained from:
    https://www.matweb.com/search/datasheet.aspx?matguid=f8e3355cc2c541fbb0174960466819c0&ckck=1

    Inherits:
        Material: Base class representing a generic material.

    Attributes:
        None
    """

    density: float = 1500
    yield_strength: float = None
    ultimate_strength: float = 17e6
