import CoolProp.CoolProp as CP
import numpy as np
import pytest

import machwave.core.incompressible_flow as incompressible_flow
import machwave.core.two_phase_flow as two_phase_flow


def _get_reference_hem_mass_flux(
    fluid_name: str,
    temperature_upstream: float,
    pressure_downstream: float,
    pressure_upstream: float | None = None,
    sweep_points: int = 2000,
) -> float:
    """High-resolution HEM oracle reproducing PropSim's TwoPhaseN2OFlow.m."""
    p_up = (
        CP.PropsSI("P", "T", temperature_upstream, "Q", 0, fluid_name)
        if pressure_upstream is None
        else pressure_upstream
    )
    if pressure_downstream >= p_up:
        return 0.0
    h_up = CP.PropsSI("H", "T", temperature_upstream, "Q", 0, fluid_name)
    s_up = CP.PropsSI("S", "T", temperature_upstream, "Q", 0, fluid_name)
    pressures = np.linspace(pressure_downstream, p_up, sweep_points)
    fluxes = np.zeros_like(pressures)
    for i, pressure in enumerate(pressures):
        try:
            density = CP.PropsSI("D", "P", pressure, "S", s_up, fluid_name)
            enthalpy = CP.PropsSI("H", "P", pressure, "S", s_up, fluid_name)
        except ValueError:
            continue
        delta_enthalpy = h_up - enthalpy
        if delta_enthalpy > 0:
            fluxes[i] = density * np.sqrt(2.0 * delta_enthalpy)
    return float(fluxes.max())


@pytest.mark.parametrize(
    "temperature_upstream,pressure_downstream",
    [
        (283.0, 20e5),
        (293.0, 20e5),
        (293.0, 30e5),
    ],
)
def test_get_homogeneous_equilibrium_mass_flux_matches_reference_within_five_percent(
    temperature_upstream,
    pressure_downstream,
):
    """
    HEM mass flux for saturated nitrous oxide matches the PropSim-style
    reference within 5%.
    """
    actual = two_phase_flow.get_homogeneous_equilibrium_mass_flux(
        fluid_name="N2O",
        temperature_upstream=temperature_upstream,
        pressure_downstream=pressure_downstream,
    )
    expected = _get_reference_hem_mass_flux(
        fluid_name="N2O",
        temperature_upstream=temperature_upstream,
        pressure_downstream=pressure_downstream,
    )
    assert actual == pytest.approx(expected, rel=0.05)


@pytest.mark.parametrize("pressure_drop", [1e3, 2e5])
def test_get_homogeneous_equilibrium_mass_flux_below_saturation_matches_saturation(
    pressure_drop,
):
    temperature_upstream = 293.0
    pressure_downstream = 20e5
    p_sat = CP.PropsSI("P", "T", temperature_upstream, "Q", 0, "N2O")

    actual = two_phase_flow.get_homogeneous_equilibrium_mass_flux(
        fluid_name="N2O",
        temperature_upstream=temperature_upstream,
        pressure_downstream=pressure_downstream,
        pressure_upstream=p_sat - pressure_drop,
    )
    at_saturation = two_phase_flow.get_homogeneous_equilibrium_mass_flux(
        fluid_name="N2O",
        temperature_upstream=temperature_upstream,
        pressure_downstream=pressure_downstream,
        pressure_upstream=p_sat,
    )
    assert actual == pytest.approx(at_saturation, rel=1e-3)


def test_get_homogeneous_equilibrium_mass_flux_returns_zero_when_downstream_at_or_above_upstream():
    """No flow when chamber pressure is at or above the upstream pressure."""
    p_sat = CP.PropsSI("P", "T", 293.0, "Q", 0, "N2O")

    assert (
        two_phase_flow.get_homogeneous_equilibrium_mass_flux(
            fluid_name="N2O",
            temperature_upstream=293.0,
            pressure_downstream=p_sat,
        )
        == 0.0
    )
    assert (
        two_phase_flow.get_homogeneous_equilibrium_mass_flux(
            fluid_name="N2O",
            temperature_upstream=293.0,
            pressure_downstream=p_sat + 1e5,
        )
        == 0.0
    )


def test_get_homogeneous_equilibrium_mass_flux_chokes_below_critical_back_pressure():
    """Two deeply subcritical chamber pressures yield the same choked mass flux."""
    flux_low = two_phase_flow.get_homogeneous_equilibrium_mass_flux(
        fluid_name="N2O",
        temperature_upstream=293.0,
        pressure_downstream=5e5,
    )
    flux_mid = two_phase_flow.get_homogeneous_equilibrium_mass_flux(
        fluid_name="N2O",
        temperature_upstream=293.0,
        pressure_downstream=15e5,
    )
    assert flux_low == pytest.approx(flux_mid, rel=1e-3)


def test_get_homogeneous_equilibrium_mass_flux_is_subcritical_above_choking_back_pressure():
    """
    Above the choking back-pressure, lowering chamber pressure increases
    mass flux.
    """
    flux_high_back_pressure = two_phase_flow.get_homogeneous_equilibrium_mass_flux(
        fluid_name="N2O",
        temperature_upstream=293.0,
        pressure_downstream=45e5,
    )
    flux_lower_back_pressure = two_phase_flow.get_homogeneous_equilibrium_mass_flux(
        fluid_name="N2O",
        temperature_upstream=293.0,
        pressure_downstream=42e5,
    )
    assert flux_lower_back_pressure > flux_high_back_pressure


def test_get_homogeneous_equilibrium_mass_flux_predicts_lower_flow_than_incompressible_for_saturated_n2o():
    """HEM is conservative relative to SPI evaluated on saturated-liquid density."""
    fluid_name = "N2O"
    temperature_upstream = 293.0
    pressure_downstream = 20e5
    p_sat = CP.PropsSI("P", "T", temperature_upstream, "Q", 0, fluid_name)
    rho_l = CP.PropsSI("D", "T", temperature_upstream, "Q", 0, fluid_name)

    flux_hem = two_phase_flow.get_homogeneous_equilibrium_mass_flux(
        fluid_name=fluid_name,
        temperature_upstream=temperature_upstream,
        pressure_downstream=pressure_downstream,
    )
    flux_spi = np.sqrt(2.0 * rho_l * (p_sat - pressure_downstream))

    assert flux_hem < flux_spi


def test_get_homogeneous_equilibrium_mass_flux_raises_on_degenerate_sweep_points():
    """ValueError is raised when `sweep_points` is less than 2."""
    with pytest.raises(ValueError, match="sweep_points must be at least 2"):
        two_phase_flow.get_homogeneous_equilibrium_mass_flux(
            fluid_name="N2O",
            temperature_upstream=293.0,
            pressure_downstream=20e5,
            sweep_points=1,
        )


def test_get_homogeneous_equilibrium_mass_flux_honors_pressure_upstream_override():
    """
    Explicit upstream pressure is used in place of the saturation pressure
    at the upstream temperature.
    """
    fluid_name = "N2O"
    temperature_upstream = 293.0
    pressure_downstream = 20e5
    p_sat = CP.PropsSI("P", "T", temperature_upstream, "Q", 0, fluid_name)

    default = two_phase_flow.get_homogeneous_equilibrium_mass_flux(
        fluid_name=fluid_name,
        temperature_upstream=temperature_upstream,
        pressure_downstream=pressure_downstream,
    )
    overridden = two_phase_flow.get_homogeneous_equilibrium_mass_flux(
        fluid_name=fluid_name,
        temperature_upstream=temperature_upstream,
        pressure_downstream=pressure_downstream,
        pressure_upstream=p_sat,
    )
    assert default == pytest.approx(overridden)


def _get_dyer_mass_flux(
    temperature_upstream: float,
    pressure_upstream: float,
    pressure_downstream: float,
    density_upstream: float | None = None,
) -> float:
    density = (
        CP.PropsSI("D", "T", temperature_upstream, "Q", 0, "N2O")
        if density_upstream is None
        else density_upstream
    )
    return two_phase_flow.get_dyer_mass_flux(
        fluid_name="N2O",
        temperature_upstream=temperature_upstream,
        density_upstream=density,
        pressure_upstream=pressure_upstream,
        pressure_downstream=pressure_downstream,
    )


def test_get_dyer_mass_flux_matches_a_hand_computed_state_point():
    """
    The 1 kN test engine's oxidizer inlet: saturated N2O at 300 K behind a
    0.2 MPa line loss, into a 3.2635 MPa chamber.

    CoolProp at 300 K: Pv = 5.88744 MPa, rho_l = 724.70 kg/m^3.
    P1 = 5.6874 MPa, P2 = 3.2635 MPa, so P1 - P2 = 2.4239 MPa.

    G_SPI = sqrt(2 * 724.70 * 2.4239e6) = sqrt(3.5132e9) = 59272 kg/(m^2 s)
    kappa = sqrt(2.4239 / (5.88744 - 3.2635)) = sqrt(0.92378) = 0.96113
    G_HEM = 31422 kg/(m^2 s): the choked flux of the isentropic sweep, the
        same to 1e-8 with 200, 2000 and 20000 points; the critical pressure
        (4.14 MPa) is above P2.
    G = (0.96113 * 59272 + 31422) / 1.96113 = 88391 / 1.96113 = 45071 kg/(m^2 s)

    The tolerance covers the five significant figures carried by hand.
    """
    assert _get_dyer_mass_flux(
        temperature_upstream=300.0,
        pressure_upstream=5.6874e6,
        pressure_downstream=3.2635e6,
        density_upstream=724.70,
    ) == pytest.approx(45071.0, rel=1e-4)


@pytest.mark.parametrize("pressure_downstream_offset", [0.0, 1e5])
def test_get_dyer_mass_flux_is_spi_when_the_chamber_is_above_the_vapor_pressure(
    pressure_downstream_offset,
):
    """With P2 >= Pv the liquid cannot flash: the kappa -> infinity limit."""
    temperature_upstream = 293.0
    vapor_pressure = CP.PropsSI("P", "T", temperature_upstream, "Q", 0, "N2O")
    pressure_upstream = 8.0e6
    pressure_downstream = vapor_pressure + pressure_downstream_offset
    density = CP.PropsSI("D", "T", temperature_upstream, "Q", 0, "N2O")

    actual = _get_dyer_mass_flux(
        temperature_upstream, pressure_upstream, pressure_downstream
    )

    assert actual == pytest.approx(
        incompressible_flow.get_mass_flow_orifice(
            discharge_coefficient=1.0,
            area=1.0,
            density=density,
            pressure_upstream=pressure_upstream,
            pressure_downstream=pressure_downstream,
        ),
        rel=1e-12,
    )


def test_get_dyer_mass_flux_tends_to_spi_as_the_non_equilibrium_parameter_grows():
    """
    A subcooled inlet into a chamber just below the vapor pressure has a
    large kappa, and the flux closes on SPI as P2 rises to Pv.
    """
    temperature_upstream = 293.0
    vapor_pressure = CP.PropsSI("P", "T", temperature_upstream, "Q", 0, "N2O")
    density = CP.PropsSI("D", "T", temperature_upstream, "Q", 0, "N2O")
    pressure_upstream = 8.0e6

    gaps = []
    for margin in (1e5, 1e4, 1e2):
        pressure_downstream = vapor_pressure - margin
        spi = np.sqrt(2.0 * density * (pressure_upstream - pressure_downstream))
        actual = _get_dyer_mass_flux(
            temperature_upstream, pressure_upstream, pressure_downstream
        )
        gaps.append(abs(actual - spi) / spi)

    assert gaps == sorted(gaps, reverse=True)
    assert gaps[-1] < 1e-2


def test_get_dyer_mass_flux_tends_to_hem_as_the_non_equilibrium_parameter_vanishes():
    """
    An inlet well below its vapor pressure with a small pressure drop has
    kappa -> 0, and the flux closes on the swept HEM flux.
    """
    temperature_upstream = 300.0
    vapor_pressure = CP.PropsSI("P", "T", temperature_upstream, "Q", 0, "N2O")
    pressure_upstream = vapor_pressure - 2e6

    gaps = []
    for pressure_drop in (1e4, 1e3, 1e2):
        pressure_downstream = pressure_upstream - pressure_drop
        hem = two_phase_flow.get_homogeneous_equilibrium_mass_flux(
            fluid_name="N2O",
            temperature_upstream=temperature_upstream,
            pressure_downstream=pressure_downstream,
            pressure_upstream=pressure_upstream,
        )
        actual = _get_dyer_mass_flux(
            temperature_upstream, pressure_upstream, pressure_downstream
        )
        gaps.append(abs(actual - hem) / hem)

    assert gaps == sorted(gaps, reverse=True)
    assert gaps[-1] < 1e-2


@pytest.mark.parametrize(
    "temperature_upstream,pressure_upstream",
    [(300.0, 5.6874e6), (293.0, 6.0e6)],
)
def test_get_dyer_mass_flux_falls_as_the_chamber_pressure_rises(
    temperature_upstream, pressure_upstream
):
    pressures_downstream = np.linspace(0.5e6, pressure_upstream - 1e4, 40)

    fluxes = [
        _get_dyer_mass_flux(temperature_upstream, pressure_upstream, p)
        for p in pressures_downstream
    ]

    assert all(np.diff(fluxes) < 0.0)


@pytest.mark.parametrize("pressure_downstream", [5.0e6, 5.5e6])
def test_get_dyer_mass_flux_returns_zero_when_downstream_at_or_above_upstream(
    pressure_downstream,
):
    assert _get_dyer_mass_flux(293.0, 5.0e6, pressure_downstream) == 0.0


def test_get_dyer_mass_flux_lies_between_spi_and_hem_for_saturated_n2o():
    temperature_upstream = 293.0
    pressure_upstream = CP.PropsSI("P", "T", temperature_upstream, "Q", 0, "N2O")
    density = CP.PropsSI("D", "T", temperature_upstream, "Q", 0, "N2O")
    pressure_downstream = 20e5

    spi = np.sqrt(2.0 * density * (pressure_upstream - pressure_downstream))
    hem = two_phase_flow.get_homogeneous_equilibrium_mass_flux(
        fluid_name="N2O",
        temperature_upstream=temperature_upstream,
        pressure_downstream=pressure_downstream,
    )
    actual = _get_dyer_mass_flux(
        temperature_upstream, pressure_upstream, pressure_downstream
    )

    # A saturated inlet has kappa = 1: the plain average of the two, built
    # from the same HEM sweep, so only round-off separates them.
    assert hem < actual < spi
    assert actual == pytest.approx(0.5 * (spi + hem), rel=1e-12)


def test_get_dyer_mass_flux_is_spi_for_an_all_vapor_inlet():
    """A drained tank feeds vapor, which has no liquid left to flash."""
    temperature_upstream = 300.0
    vapor_density = 0.5 * CP.PropsSI("D", "T", temperature_upstream, "Q", 1, "N2O")
    pressure_upstream = CP.PropsSI(
        "P", "T", temperature_upstream, "D", vapor_density, "N2O"
    )
    pressure_downstream = 1e6

    actual = _get_dyer_mass_flux(
        temperature_upstream,
        pressure_upstream,
        pressure_downstream,
        density_upstream=vapor_density,
    )

    assert actual == pytest.approx(
        np.sqrt(2.0 * vapor_density * (pressure_upstream - pressure_downstream))
    )


def test_get_dyer_mass_flux_is_spi_above_the_critical_temperature():
    """A supercritical inlet has no vapor pressure to flash against."""
    temperature_upstream = 315.0
    pressure_upstream = 9.0e6
    density = CP.PropsSI("D", "T", temperature_upstream, "P", pressure_upstream, "N2O")

    actual = _get_dyer_mass_flux(
        temperature_upstream, pressure_upstream, 3e6, density_upstream=density
    )

    assert actual == pytest.approx(np.sqrt(2.0 * density * 6.0e6))
