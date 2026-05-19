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
    Removing propellant must decrement fluid_mass, and removing more than
    is present must empty the tank cleanly.
    """
    volume = 0.02
    initial_mass = 1.0

    tank = Tank(
        fluid_name=fluid_name,
        volume=volume,
        temperature=temperature,
        initial_fluid_mass=initial_mass,
    )

    # 1) Remove some fraction of fluid
    remove_mass_1 = 0.2
    tank.remove_propellant(remove_mass_1)

    assert tank.fluid_mass == pytest.approx(initial_mass - remove_mass_1, abs=1e-9)

    # 2) Remove more mass than is left => tank empties
    tank.remove_propellant(5.0)  # definitely more than remains
    assert tank.fluid_mass == 0.0, "Tank should be fully emptied."
    assert tank.get_density() == 0.0, "Density should be zero when empty."

    # Depending on your model, if fluid_mass=0 => get_pressure() might be 0 or very small
    empty_pressure = tank.get_pressure()
    assert empty_pressure == pytest.approx(0.0, abs=1e-9), (
        f"Pressure should be ~0 for an empty tank of {fluid_name}."
    )


@pytest.mark.parametrize("fluid_name, temperature", TEST_FLUIDS)
def test_two_phase_density_returns_saturated_liquid(fluid_name, temperature):
    """
    In the two-phase regime, ``get_density()`` must return the saturated
    *liquid* density. Real feed systems pull liquid through a dip tube, so
    the orifice equation downstream needs ρ_liquid — returning a mixture
    density under-predicts ṁ as the tank empties.
    """
    volume = 0.01
    p_sat = CP.PropsSI("P", "T", temperature, "Q", 0, fluid_name)
    molar_mass = CP.PropsSI("M", fluid_name)
    R_universal = scipy.constants.R
    m_vap_sat = (p_sat * volume * molar_mass) / (R_universal * temperature)

    tank = Tank(
        fluid_name=fluid_name,
        volume=volume,
        temperature=temperature,
        initial_fluid_mass=2.0 * m_vap_sat,
    )

    rho_liquid = CP.PropsSI("D", "T", temperature, "Q", 0, fluid_name)
    assert tank.get_density() == pytest.approx(rho_liquid, rel=1e-3)


@pytest.mark.parametrize("fluid_name, temperature", TEST_FLUIDS)
def test_two_phase_density_constant_while_two_phase(fluid_name, temperature):
    """
    While the tank remains two-phase, ``get_density()`` must be invariant
    under mass removal — it tracks the saturated liquid density, not the
    bulk mixture.
    """
    volume = 0.01
    p_sat = CP.PropsSI("P", "T", temperature, "Q", 0, fluid_name)
    molar_mass = CP.PropsSI("M", fluid_name)
    R_universal = scipy.constants.R
    m_vap_sat = (p_sat * volume * molar_mass) / (R_universal * temperature)

    tank = Tank(
        fluid_name=fluid_name,
        volume=volume,
        temperature=temperature,
        initial_fluid_mass=5.0 * m_vap_sat,
    )

    density_before = tank.get_density()
    tank.remove_propellant(m_vap_sat)  # still leaves > m_vap_sat in the tank
    assert tank.fluid_mass > m_vap_sat
    assert tank.get_density() == pytest.approx(density_before, rel=1e-6)


def test_remove_negative_mass():
    """Removing negative mass should raise ValueError."""
    tank = Tank("Water", 0.01, 300.0, 1.0)
    with pytest.raises(ValueError):
        tank.remove_propellant(-0.5)


@pytest.mark.parametrize("fluid_name, temperature", TEST_FLUIDS)
def test_check_not_overfilled_rejects_overfill(fluid_name, temperature):
    """
    Bulk density exceeding the saturated-liquid density (beyond tolerance)
    must be rejected — no physical fluid state exists in this regime.
    """
    rho_liquid = CP.PropsSI("D", "T", temperature, "Q", 0, fluid_name)
    volume = 1e-3
    overfill_mass = 2.0 * rho_liquid * volume

    with pytest.raises(ValueError, match="overfilled"):
        Tank._check_not_overfilled(fluid_name, volume, temperature, overfill_mass)


@pytest.mark.parametrize("fluid_name, temperature", TEST_FLUIDS)
def test_check_not_overfilled_accepts_fill_just_under_liquid(fluid_name, temperature):
    """
    Filling close to (but under) the saturated-liquid density must pass —
    this is the limiting physical case.
    """
    rho_liquid = CP.PropsSI("D", "T", temperature, "Q", 0, fluid_name)
    volume = 1e-3
    mass = rho_liquid * volume * 0.99

    Tank._check_not_overfilled(fluid_name, volume, temperature, mass)


@pytest.mark.parametrize("fluid_name, temperature", TEST_FLUIDS)
def test_check_not_overfilled_accepts_within_tolerance(fluid_name, temperature):
    """
    Bulk density slightly above liquid density but within the configured
    tolerance must pass — the tolerance absorbs property-table noise.
    """
    rho_liquid = CP.PropsSI("D", "T", temperature, "Q", 0, fluid_name)
    volume = 1e-3
    mass = rho_liquid * volume * (1 + Tank.OVERFILL_TOLERANCE / 2)

    Tank._check_not_overfilled(fluid_name, volume, temperature, mass)


@pytest.mark.parametrize("fluid_name, temperature", TEST_FLUIDS)
def test_check_not_overfilled_rejects_just_outside_tolerance(fluid_name, temperature):
    """
    Bulk density above liquid density by more than the tolerance must be
    rejected — the tolerance does not extend to arbitrary overfill.
    """
    rho_liquid = CP.PropsSI("D", "T", temperature, "Q", 0, fluid_name)
    volume = 1e-3
    mass = rho_liquid * volume * (1 + Tank.OVERFILL_TOLERANCE * 2)

    with pytest.raises(ValueError, match="overfilled"):
        Tank._check_not_overfilled(fluid_name, volume, temperature, mass)


def test_init_invokes_overfill_check():
    """
    The constructor must call :meth:`Tank._check_not_overfilled` so an
    overfilled tank fails fast at API boundaries rather than silently
    producing nonsensical pressure / density results downstream.
    """
    with pytest.raises(ValueError, match="overfilled"):
        Tank(
            fluid_name="Water",
            volume=1e-3,
            temperature=300.0,
            initial_fluid_mass=10.0,  # 10000 kg/m^3, liquid water ~997 kg/m^3
        )
