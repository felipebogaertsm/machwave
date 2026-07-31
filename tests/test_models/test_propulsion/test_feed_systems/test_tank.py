# test_tank.py
import CoolProp.CoolProp as CP
import pytest
import scipy.constants

import machwave.models.feed_systems.tank as tank_models

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

    # 2) Mass of saturated vapor that just fills the tank.
    m_vap = CP.PropsSI("D", "T", temperature, "Q", 1, fluid_name) * volume

    # 3) Put more mass than m_vap => ensures there's liquid
    fluid_mass = 2.0 * m_vap  # definitely more than needed for vapor only
    tank = tank_models.Tank(
        fluid_name=fluid_name,
        volume=volume,
        temperature=temperature,
        initial_fluid_mass=fluid_mass,
    )

    # 4) Check the tank pressure ~ saturation
    assert tank.get_pressure(fluid_mass) == pytest.approx(p_sat, rel=1e-3), (
        f"Expected saturation pressure for {fluid_name} at T={temperature} K."
    )


@pytest.mark.parametrize("fluid_name, temperature", TEST_FLUIDS)
def test_all_vapor_condition(fluid_name, temperature):
    """
    If the tank doesn't have enough mass to sustain liquid, it should be all
    vapor and the pressure should follow the real-gas equation of state.
    """
    volume = 0.01  # m^3

    # m_vap_sat = mass of saturated vapor that just fills the tank
    m_vap_sat = CP.PropsSI("D", "T", temperature, "Q", 1, fluid_name) * volume

    # Put slightly less than that => ensures no liquid
    mass = 0.5 * m_vap_sat
    tank = tank_models.Tank(
        fluid_name=fluid_name,
        volume=volume,
        temperature=temperature,
        initial_fluid_mass=mass,
    )

    p_real = CP.PropsSI("P", "T", temperature, "D", mass / volume, fluid_name)
    assert tank.get_pressure(mass) == pytest.approx(p_real, rel=1e-3), (
        f"Expected real-gas pressure for {fluid_name} at T={temperature} K with insufficient mass."
    )


def test_near_critical_vapor_not_misclassified_as_two_phase():
    """
    Near the critical point the saturated-vapor density far exceeds the
    ideal-gas value, so a fill between the two is still single-phase vapor.
    The phase split must use the real saturated-vapor density; the ideal-gas
    threshold would wrongly report the saturation pressure here.
    """
    fluid_name, temperature, volume = "N2O", 298.0, 0.01  # T_c = 309.5 K

    p_sat = CP.PropsSI("P", "T", temperature, "Q", 0, fluid_name)
    molar_mass = CP.PropsSI("M", fluid_name)
    rho_vapor = CP.PropsSI("D", "T", temperature, "Q", 1, fluid_name)
    rho_vapor_ideal = p_sat * molar_mass / (scipy.constants.R * temperature)
    assert rho_vapor > 1.5 * rho_vapor_ideal  # genuinely near-critical

    # Fill between the ideal-gas and real saturated-vapor masses: above the old
    # (ideal-gas) threshold, below the real one.
    mass = 0.5 * (rho_vapor_ideal + rho_vapor) * volume
    assert rho_vapor_ideal * volume < mass < rho_vapor * volume

    tank = tank_models.Tank(
        fluid_name=fluid_name,
        volume=volume,
        temperature=temperature,
        initial_fluid_mass=mass,
    )

    # Single-phase vapor: the pressure is the real-gas value and stays strictly
    # below saturation. The old ideal-gas threshold would have reported p_sat.
    p_real = CP.PropsSI("P", "T", temperature, "D", mass / volume, fluid_name)
    pressure = tank.get_pressure(mass)
    assert pressure == pytest.approx(p_real, rel=1e-3)
    assert pressure < p_sat


@pytest.mark.parametrize("fluid_name, temperature", TEST_FLUIDS)
def test_empty_tank_pressure_and_density(fluid_name, temperature):
    """
    An empty tank (zero fluid mass) must report ~zero pressure and density.
    """
    tank = tank_models.Tank(
        fluid_name=fluid_name,
        volume=0.02,
        temperature=temperature,
        initial_fluid_mass=1.0,
    )

    assert tank.get_density(0.0) == 0.0, "Density should be zero when empty."
    assert tank.get_pressure(0.0) == pytest.approx(0.0, abs=1e-9), (
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
    m_vap_sat = CP.PropsSI("D", "T", temperature, "Q", 1, fluid_name) * volume

    fluid_mass = 2.0 * m_vap_sat
    tank = tank_models.Tank(
        fluid_name=fluid_name,
        volume=volume,
        temperature=temperature,
        initial_fluid_mass=fluid_mass,
    )

    rho_liquid = CP.PropsSI("D", "T", temperature, "Q", 0, fluid_name)
    assert tank.get_density(fluid_mass) == pytest.approx(rho_liquid, rel=1e-3)


@pytest.mark.parametrize("fluid_name, temperature", TEST_FLUIDS)
def test_two_phase_density_constant_while_two_phase(fluid_name, temperature):
    """
    While the tank remains two-phase, ``get_density()`` must be invariant
    under mass change — it tracks the saturated liquid density, not the
    bulk mixture.
    """
    volume = 0.01
    m_vap_sat = CP.PropsSI("D", "T", temperature, "Q", 1, fluid_name) * volume

    tank = tank_models.Tank(
        fluid_name=fluid_name,
        volume=volume,
        temperature=temperature,
        initial_fluid_mass=2.5 * m_vap_sat,
    )

    # Both masses leave the tank two-phase (> m_vap_sat), so density is invariant.
    # Multipliers stay below the liquid/vapor density ratio to avoid overfill for
    # near-critical fluids like N2O.
    higher_mass = 2.5 * m_vap_sat
    lower_mass = 1.5 * m_vap_sat
    assert lower_mass > m_vap_sat
    assert tank.get_density(lower_mass) == pytest.approx(
        tank.get_density(higher_mass), rel=1e-6
    )


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
        tank_models.Tank(
            fluid_name=fluid_name,
            volume=volume,
            temperature=temperature,
            initial_fluid_mass=overfill_mass,
        )


@pytest.mark.parametrize("fluid_name, temperature", TEST_FLUIDS)
def test_check_not_overfilled_accepts_fill_just_under_liquid(fluid_name, temperature):
    """
    Filling close to (but under) the saturated-liquid density must pass —
    this is the limiting physical case.
    """
    rho_liquid = CP.PropsSI("D", "T", temperature, "Q", 0, fluid_name)
    volume = 1e-3
    mass = rho_liquid * volume * 0.99

    tank_models.Tank(
        fluid_name=fluid_name,
        volume=volume,
        temperature=temperature,
        initial_fluid_mass=mass,
    )


@pytest.mark.parametrize("fluid_name, temperature", TEST_FLUIDS)
def test_check_not_overfilled_accepts_within_tolerance(fluid_name, temperature):
    """
    Bulk density slightly above liquid density but within the configured
    tolerance must pass — the tolerance absorbs property-table noise.
    """
    rho_liquid = CP.PropsSI("D", "T", temperature, "Q", 0, fluid_name)
    volume = 1e-3
    tolerance = 0.01
    mass = rho_liquid * volume * (1 + tolerance / 2)

    tank_models.Tank(
        fluid_name=fluid_name,
        volume=volume,
        temperature=temperature,
        initial_fluid_mass=mass,
        overfill_tolerance=tolerance,
    )


@pytest.mark.parametrize("fluid_name, temperature", TEST_FLUIDS)
def test_check_not_overfilled_rejects_just_outside_tolerance(fluid_name, temperature):
    """
    Bulk density above liquid density by more than the tolerance must be
    rejected — the tolerance does not extend to arbitrary overfill.
    """
    rho_liquid = CP.PropsSI("D", "T", temperature, "Q", 0, fluid_name)
    volume = 1e-3
    tolerance = 0.01
    mass = rho_liquid * volume * (1 + tolerance * 2)

    with pytest.raises(ValueError, match="overfilled"):
        tank_models.Tank(
            fluid_name=fluid_name,
            volume=volume,
            temperature=temperature,
            initial_fluid_mass=mass,
            overfill_tolerance=tolerance,
        )


def test_init_invokes_overfill_check():
    """
    The constructor must call :meth:`tank_models.Tank._check_not_overfilled` so an
    overfilled tank fails fast at API boundaries rather than silently
    producing nonsensical pressure / density results downstream.
    """
    with pytest.raises(ValueError, match="overfilled"):
        tank_models.Tank(
            fluid_name="Water",
            volume=1e-3,
            temperature=300.0,
            initial_fluid_mass=10.0,  # 10000 kg/m^3, liquid water ~997 kg/m^3
        )


@pytest.mark.parametrize(
    "overrides, match",
    [
        ({"volume": 0.0}, "volume must be strictly positive"),
        ({"volume": -1e-3}, "volume must be strictly positive"),
        ({"temperature": 0.0}, "temperature must be strictly positive"),
        ({"temperature": -10.0}, "temperature must be strictly positive"),
        ({"initial_fluid_mass": -0.1}, "initial_fluid_mass must be non-negative"),
        ({"overfill_tolerance": -0.01}, "overfill_tolerance must be non-negative"),
    ],
)
def test_init_rejects_invalid_inputs(overrides, match):
    """The constructor must reject physically invalid arguments up front."""
    kwargs = dict(
        fluid_name="Water",
        volume=1e-3,
        temperature=300.0,
        initial_fluid_mass=0.5,
    )
    kwargs.update(overrides)

    with pytest.raises(ValueError, match=match):
        tank_models.Tank(**kwargs)


@pytest.mark.parametrize("fluid_name", ["N2O", "Ethanol"])
def test_init_rejects_supercritical_temperature(fluid_name):
    """
    Above the critical temperature no distinct liquid phase exists, so the
    saturation lookups have no answer and the tank must reject the input with a
    clean error instead of letting CoolProp fail.
    """
    temperature = CP.PropsSI("Tcrit", fluid_name) + 50.0

    with pytest.raises(ValueError, match="outside the two-phase range"):
        tank_models.Tank(
            fluid_name=fluid_name,
            volume=0.01,
            temperature=temperature,
            initial_fluid_mass=0.5,
        )


@pytest.mark.parametrize("fluid_name", ["N2O", "Ethanol"])
def test_init_rejects_critical_temperature(fluid_name):
    """
    The critical temperature itself is excluded: liquid and vapor are already
    indistinguishable there, which the two-phase model cannot represent.
    """
    temperature = CP.PropsSI("Tcrit", fluid_name)

    with pytest.raises(ValueError, match="outside the two-phase range"):
        tank_models.Tank(
            fluid_name=fluid_name,
            volume=0.01,
            temperature=temperature,
            initial_fluid_mass=0.5,
        )


@pytest.mark.parametrize("fluid_name", ["N2O", "Ethanol"])
def test_init_rejects_temperature_below_triple_point(fluid_name):
    """
    Below the triple point the fluid is solid, so the saturated-liquid lookups
    are undefined and the tank must reject the input.
    """
    temperature = CP.PropsSI("Ttriple", fluid_name) - 10.0

    with pytest.raises(ValueError, match="outside the two-phase range"):
        tank_models.Tank(
            fluid_name=fluid_name,
            volume=0.01,
            temperature=temperature,
            initial_fluid_mass=0.5,
        )


@pytest.mark.parametrize("fluid_name", ["N2O", "Ethanol"])
def test_init_accepts_triple_point_temperature(fluid_name):
    """
    The triple point is the inclusive lower end of the range: liquid and vapor
    still coexist there, so the tank must accept it and resolve saturation.
    """
    temperature = CP.PropsSI("Ttriple", fluid_name)

    tank = tank_models.Tank(
        fluid_name=fluid_name,
        volume=0.01,
        temperature=temperature,
        initial_fluid_mass=0.5,
    )

    assert tank.saturation_pressure > 0.0
    assert tank.saturated_liquid_density > tank.saturated_vapor_density


@pytest.mark.parametrize("fluid_name", ["N2O", "Ethanol"])
def test_init_accepts_temperature_inside_two_phase_range(fluid_name):
    """A temperature between the two bounds stays valid."""
    triple_point_temperature = CP.PropsSI("Ttriple", fluid_name)
    critical_temperature = CP.PropsSI("Tcrit", fluid_name)
    temperature = 0.5 * (triple_point_temperature + critical_temperature)

    tank = tank_models.Tank(
        fluid_name=fluid_name,
        volume=0.01,
        temperature=temperature,
        initial_fluid_mass=0.5,
    )

    assert tank.saturation_pressure == pytest.approx(
        CP.PropsSI("P", "T", temperature, "Q", 0, fluid_name)
    )


def test_init_rejects_unknown_fluid():
    """An unrecognized fluid must surface as a clean error, not a CoolProp one."""
    with pytest.raises(ValueError, match="recognized by CoolProp"):
        tank_models.Tank(
            fluid_name="Unobtainium",
            volume=0.01,
            temperature=298.0,
            initial_fluid_mass=0.5,
        )
