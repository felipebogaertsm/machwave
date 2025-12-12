"""
Commonly used liquid propellant formulations with their characteristic
properties.
"""

from machwave.models.propulsion.propellants.categories import BiliquidPropellant

LOX_RP1_2_5 = BiliquidPropellant(
    oxidizer_name="LOX",
    fuel_name="RP1",
    of_ratio=2.5,
    combustion_efficiency=0.98,
)

LOX_RP1_2_7 = BiliquidPropellant(
    oxidizer_name="LOX",
    fuel_name="RP1",
    of_ratio=2.7,
    combustion_efficiency=0.98,
)

# LOX/LH2 propellant formulations
LOX_LH2_5_5 = BiliquidPropellant(
    oxidizer_name="LOX",
    fuel_name="LH2",
    of_ratio=5.5,
    combustion_efficiency=0.98,
)

LOX_LH2_6_0 = BiliquidPropellant(
    oxidizer_name="LOX",
    fuel_name="LH2",
    of_ratio=6.0,
    combustion_efficiency=0.98,
)

# N2O4/MMH (Aerozine 50 compatible)
N2O4_MMH_1_65 = BiliquidPropellant(
    oxidizer_name="N2O4",
    fuel_name="MMH",
    of_ratio=1.65,
    combustion_efficiency=0.98,
)

# N2O4/UDMH
N2O4_UDMH_2_0 = BiliquidPropellant(
    oxidizer_name="N2O4",
    fuel_name="UDMH",
    of_ratio=2.0,
    combustion_efficiency=0.98,
)
