from dataclasses import dataclass

from .base import NozzleMaterial


@dataclass
class Steel(NozzleMaterial):
    """
    Steel material class derived from the NozzleMaterial base class.

    This class represents a specific type of material, Steel, which inherits
    properties from the NozzleMaterial base class. It provides default values
    for the density, yield strength, ultimate strength, c_1, and c_2 specific to
    Steel.

    Source:
    https://www.thyssenkrupp-materials.co.uk/stainless-steel-304-14301.html
    """

    density: float = 8000
    yield_strength: float = 210e6
    ultimate_strength: float = 520e6
    c_1: float = 0.00506
    c_2: float = 0.0


@dataclass
class Al6063T5(NozzleMaterial):
    """
    Al6063T5 (Aluminum) material class derived from the NozzleMaterial base
    class.

    This class represents a specific type of material, Al6063T5 (Aluminum),
    which inherits properties from the NozzleMaterial base class. It provides
    default values for the density, yield strength, ultimate strength, c_1, and
    c_2 specific to Al6063T5.

    Source:
    https://www.makeitfrom.com/material-properties/6063-T5-Aluminum
    """

    density: float = 2700
    yield_strength: float = 145e6
    ultimate_strength: float = 185e6
    c_1: float = 0.00506
    c_2: float = 0.0


@dataclass
class Al6061T6(NozzleMaterial):
    """
    Al6061T6 (Aluminum) material class derived from the NozzleMaterial base
    class.

    This class represents a specific type of material, Al6061T6 (Aluminum),
    which inherits properties from the NozzleMaterial base class. It provides
    default values for the density, yield strength, ultimate strength, c_1, and
    c_2 specific to Al6061T6.

    Source:
    https://matweb.com/search/DataSheet.aspx?MatGUID=b8d536e0b9b54bd7b69e4124d8f1d20a&ckck=1
    """

    density: float = 2700
    yield_strength: float = 262e6
    ultimate_strength: float = 290e6
    c_1: float = 0.00506
    c_2: float = 0.0
