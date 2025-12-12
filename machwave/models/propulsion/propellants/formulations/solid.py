"""Solid propellant formulation instances."""

from ..categories import CEASolidPropellant, FixedSolidPropellant
from ..properties import SolidPropellantProperties

KNDX = FixedSolidPropellant(
    name="KN-Dextrose",
    burn_rate=[
        {"min": 0, "max": 0.779e6, "a": 8.875, "n": 0.619},
        {"min": 0.779e6, "max": 2.572e6, "a": 7.553, "n": -0.009},
        {"min": 2.572e6, "max": 5.930e6, "a": 3.841, "n": 0.688},
        {"min": 5.930e6, "max": 8.502e6, "a": 17.20, "n": -0.148},
        {"min": 8.502e6, "max": 11.20e6, "a": 4.775, "n": 0.442},
    ],
    properties=SolidPropellantProperties(
        gamma_chamber=1.1308,
        gamma_exhaust=1.0430,
        adiabatic_flame_temperature=1712 * 0.95,
        adiabatic_flame_temperature_ideal=1712,
        molecular_weight_chamber=42.391 * 1e-3,
        molecular_weight_exhaust=42.882 * 1e-3,
        i_sp_frozen=152.4,
        i_sp_shifting=154.1,
        density=1795.0,
        qsi_chamber=0.307,
        qsi_exhaust=0.321,
    ),
)

KNSB = FixedSolidPropellant(
    name="KN-Sorbitol",
    burn_rate=[
        {"min": 0, "max": 11e6, "a": 5.13, "n": 0.222},
    ],
    properties=SolidPropellantProperties(
        gamma_chamber=1.1361,
        gamma_exhaust=1.0420,
        adiabatic_flame_temperature=1603 * 0.95,
        adiabatic_flame_temperature_ideal=1603,
        molecular_weight_chamber=39.857 * 1e-3,
        molecular_weight_exhaust=40.048 * 1e-3,
        i_sp_frozen=151.4,
        i_sp_shifting=153.5,
        density=1837.3 * 0.95,
        qsi_chamber=0.316,
        qsi_exhaust=0.321,
    ),
)

KNSB_NAKKA = FixedSolidPropellant(
    name="KN-Sorbitol (Nakka)",
    burn_rate=[
        {"min": 0, "max": 0.807e6, "a": 10.708, "n": 0.625},
        {"min": 0.807e6, "max": 1.503e6, "a": 8.763, "n": -0.314},
        {"min": 1.503e6, "max": 3.792e6, "a": 7.852, "n": -0.013},
        {"min": 3.792e6, "max": 7.033e6, "a": 3.907, "n": 0.535},
        {"min": 7.033e6, "max": 10.67e6, "a": 9.653, "n": 0.064},
    ],
    properties=SolidPropellantProperties(
        gamma_chamber=1.1361,
        gamma_exhaust=1.0420,
        adiabatic_flame_temperature=1603 * 0.95,
        adiabatic_flame_temperature_ideal=1603,
        molecular_weight_chamber=39.857 * 1e-3,
        molecular_weight_exhaust=40.048 * 1e-3,
        i_sp_frozen=151.4,
        i_sp_shifting=153.5,
        density=1837.3 * 0.95,
        qsi_chamber=0.316,
        qsi_exhaust=0.321,
    ),
)

KNSU = FixedSolidPropellant(
    name="KN-Sucrose",
    burn_rate=[{"min": 0, "max": 100e6, "a": 8.260, "n": 0.319}],
    properties=SolidPropellantProperties(
        gamma_chamber=1.1330,
        gamma_exhaust=1.1044,
        adiabatic_flame_temperature=1722 * 0.95,
        adiabatic_flame_temperature_ideal=1722,
        molecular_weight_chamber=41.964 * 1e-3,
        molecular_weight_exhaust=41.517 * 1e-3,
        i_sp_frozen=153.3,
        i_sp_shifting=155.1,
        density=1899.5 * 0.95,
        qsi_chamber=0.306,
        qsi_exhaust=0.321,
    ),
)

KNER = FixedSolidPropellant(
    name="KN-Erythritol",
    burn_rate=[{"min": 0, "max": 100e6, "a": 2.903, "n": 0.395}],
    properties=SolidPropellantProperties(
        gamma_chamber=1.1390,
        gamma_exhaust=1.0426,
        adiabatic_flame_temperature=1608 * 0.94,
        adiabatic_flame_temperature_ideal=1608,
        molecular_weight_chamber=38.570 * 1e-3,
        molecular_weight_exhaust=38.779 * 1e-3,
        i_sp_frozen=153.8,
        i_sp_shifting=156.0,
        density=1820.0 * 0.95,
        qsi_chamber=0.315,
        qsi_exhaust=0.321,
    ),
)

# NOTE: Data for both RNXs still needs to be revised and updated according
# to ProPEP3.

RNX_57 = FixedSolidPropellant(
    name="RNX-57",
    burn_rate=[{"min": 0, "max": 100e6, "a": 1.95, "n": 0.477}],
    properties=SolidPropellantProperties(
        gamma_chamber=1.159,
        gamma_exhaust=1.026,
        adiabatic_flame_temperature=1644 * 0.95,
        adiabatic_flame_temperature_ideal=1644,
        molecular_weight_chamber=45.19 * 1e-3,
        molecular_weight_exhaust=45.19 * 1e-3,
        i_sp_frozen=158.1,
        i_sp_shifting=158.1,
        density=1844.5 * 0.95,
        qsi_chamber=0.306,
        qsi_exhaust=0.321,
    ),
)

RNX_71V = FixedSolidPropellant(
    name="RNX-71",
    burn_rate=[{"min": 0, "max": 100e6, "a": 2.57, "n": 0.371}],
    properties=SolidPropellantProperties(
        gamma_chamber=1.180,
        gamma_exhaust=1.027,
        adiabatic_flame_temperature=1434 * 0.95,
        adiabatic_flame_temperature_ideal=1434,
        molecular_weight_chamber=41.83 * 1e-3,
        molecular_weight_exhaust=41.83 * 1e-3,
        i_sp_frozen=153.6,
        i_sp_shifting=153.6,
        density=1816.1 * 0.95,
        qsi_chamber=0.306,
        qsi_exhaust=0.321,
    ),
)

MIT_CHERRY_LIMEADE = FixedSolidPropellant(
    name="MIT Cherry Limeade",
    burn_rate=[{"min": 0, "max": 6.35e6, "a": 3.2373, "n": 0.3273}],
    properties=SolidPropellantProperties(
        gamma_chamber=1.2100,
        gamma_exhaust=1.2501,
        adiabatic_flame_temperature=2800 * 0.95,
        adiabatic_flame_temperature_ideal=2800,
        molecular_weight_chamber=23.724 * 1e-3,
        molecular_weight_exhaust=23.811 * 1e-3,
        i_sp_frozen=241.3,
        i_sp_shifting=245.1,
        density=1670.0,
        qsi_chamber=0.138,
        qsi_exhaust=0.139,
    ),
)

# APCP - Ammonium Perchlorate Composite Propellant
# Generic HTPB/AP formulation with typical burn rate
APCP_GENERIC = CEASolidPropellant(
    cea_name="HTPB",
    burn_rate=[{"min": 0, "max": 20e6, "a": 4.0, "n": 0.35}],
    ideal_density=1750.0,
    density_percentage=98.0,
    combustion_efficiency=0.96,
)
