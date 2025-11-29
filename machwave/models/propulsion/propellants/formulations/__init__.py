"""
This module contains preset propellant formulations for solid and liquid propellants.

Each formulation represents a specific propellant type that can dynamically generate
CEA objects by calling the evaluate() method with chamber conditions.
"""

from .biliquid import (
    LOX_LH2_5_5,
    LOX_LH2_6_0,
    LOX_RP1_2_5,
    LOX_RP1_2_7,
    N2O4_MMH_1_65,
    N2O4_UDMH_2_0,
)
from .solid import (
    APCP_GENERIC,
    KNDX,
    KNER,
    KNSB,
    KNSB_NAKKA,
    KNSU,
    MIT_CHERRY_LIMEADE,
    RNX_57,
    RNX_71V,
)

__all__ = [
    # Empirical solid propellants
    "KNDX",
    "KNSB",
    "KNSB_NAKKA",
    "KNSU",
    "KNER",
    "RNX_57",
    "RNX_71V",
    "MIT_CHERRY_LIMEADE",
    # CEA-based solid propellants
    "APCP_GENERIC",
    # Liquid propellants
    "LOX_RP1_2_5",
    "LOX_RP1_2_7",
    "LOX_LH2_5_5",
    "LOX_LH2_6_0",
    "N2O4_MMH_1_65",
    "N2O4_UDMH_2_0",
]
