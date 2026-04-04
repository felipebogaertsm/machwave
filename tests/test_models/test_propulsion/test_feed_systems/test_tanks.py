# test_tank.py
import CoolProp.CoolProp as CP
import pytest
import scipy.constants

from machwave.models.feed_systems.tanks import Tank

# A few (fluid, temperature) pairs for running tests.
# Adjust temperatures to ensure we stay within valid ranges for each fluid in CoolProp.
# Temperatures are in Kelvin.
TEST_FLUIDS = [
    ("Water", 373.15),
    ("N2O", 298.0),
    ("Oxygen", 90.0),
    ("Hydrogen", 25.0),
    ("Ethanol", 350.0),
]


@pytest.mark.parametrize("fluid_name, temperature", TEST_FLUIDS)
def test_saturated_condition(fluid_name, temperature):
    """
    If the tank has enough mass to form liquid, pressure should match saturation.
    We pick a fluid/temperature pair from TEST_FLUIDS, compute the saturation pressure,
    and then give enough mass so that some liquid must be present.
    """
    volume = 0.01  # m^3

    # 1) Get saturation pressure at the chosen T.
    #    This might fail if T is out of range for the fluid.
    p_sat = CP.PropsSI("P", "T", temperature, "Q", 0, fluid_name)

    # 2) Calculate how much mass is vapor only at p_sat.
    molar_mass = CP.PropsSI("M", fluid_name)  # kg/mol
    R_universal = scipy.constants.R
    m_vap = (p_sat * volume * molar_mass) / (R_universal * temperature)

    # 3) Put more mass than m_vap => ensures there's liquid
    tank = Tank(
        fluid_name=fluid_name,
        volume=volume,
        temperature=temperature,
        initial_fluid_mass=2.0 * m_vap,  # definitely more than needed for vapor only
    )

    # 4) Check the tank pressure ~ saturation
    assert tank.get_pressure() == pytest.approx(p_sat, rel=1e-3), (
        f"Expected saturation pressure for {fluid_name} at T={temperature} K."
    )


@pytest.mark.parametrize("fluid_name, temperature", TEST_FLUIDS)
def test_all_vapor_condition(fluid_name, temperature):
    """
    If the tank doesn't have enough mass to sustain liquid, it should be all vapor
    and the pressure should follow the ideal gas law.
    """
    volume = 0.01  # m^3
    p_sat = CP.PropsSI("P", "T", temperature, "Q", 0, fluid_name)
    molar_mass = CP.PropsSI("M", fluid_name)
    R_universal = scipy.constants.R

    # m_vap_sat = mass of vapor at p_sat (all vapor)
    m_vap_sat = (p_sat * volume * molar_mass) / (R_universal * temperature)

    # Put slightly less than that => ensures no liquid
    mass = 0.5 * m_vap_sat
    tank = Tank(
        fluid_name=fluid_name,
        volume=volume,
        temperature=temperature,
        initial_fluid_mass=mass,
    )

    # Ideal gas law pressure => P_ideal = (n * R * T)/V
    n_moles = mass / molar_mass
    p_ideal = (n_moles * R_universal * temperature) / volume

    assert tank.get_pressure() == pytest.approx(p_ideal, rel=1e-3), (
        f"Expected ideal-gas pressure for {fluid_name} at T={temperature} K with insufficient mass."
    )


@pytest.mark.parametrize("fluid_name, temperature", TEST_FLUIDS)
def test_remove_propellant(fluid_name, temperature):
    """
    Removing propellant should decrease fluid_mass and thus reduce density.
    We also verify that removing more fluid than present empties the tank.
    """
    volume = 0.02
    initial_mass = 1.0

    tank = Tank(
        fluid_name=fluid_name,
        volume=volume,
        temperature=temperature,
        initial_fluid_mass=initial_mass,
    )
    original_density = tank.get_density()

    # 1) Remove some fraction of fluid
    remove_mass_1 = 0.2
    tank.remove_propellant(remove_mass_1)

    assert tank.fluid_mass == pytest.approx(initial_mass - remove_mass_1, abs=1e-9)
    new_density = tank.get_density()
    assert new_density < original_density, (
        "Density should decrease after removing mass."
    )

    # 2) Remove more mass than is left => tank empties
    tank.remove_propellant(5.0)  # definitely more than remains
    assert tank.fluid_mass == 0.0, "Tank should be fully emptied."
    assert tank.get_density() == 0.0, "Density should be zero when empty."

    # Depending on your model, if fluid_mass=0 => get_pressure() might be 0 or very small
    empty_pressure = tank.get_pressure()
    assert empty_pressure == pytest.approx(0.0, abs=1e-9), (
        f"Pressure should be ~0 for an empty tank of {fluid_name}."
    )


def test_remove_negative_mass():
    """
    Removing negative mass should raise ValueError.
    """
    tank = Tank("Water", 0.01, 300.0, 1.0)
    with pytest.raises(ValueError):
        tank.remove_propellant(-0.5)
