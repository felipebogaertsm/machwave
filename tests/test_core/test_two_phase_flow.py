import CoolProp.CoolProp as CP
import numpy as np
import pytest

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
