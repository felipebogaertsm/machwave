"""End-to-end integration tests for LiquidEngine internal ballistics
simulations.

The motor configuration below mirrors the one in examples/1kn_lre.py
(the lone biliquid example) but is duplicated here so the tests stay
independent of the example layer.
"""

from __future__ import annotations

import numpy as np
import pytest

from machwave.models import feed_systems, motors, propellants
from machwave.models import thrust_chamber as thrust_chamber_models
from machwave.models.feed_systems import tanks
from machwave.simulation import InternalBallisticsSimulationParams
from machwave.states import LiquidEngineState
from tests.test_simulations.conftest import (
    SimulationResult,
    assert_recorded_arrays_aligned,
    run_simulation,
)


def _build_1kn_lre() -> tuple[motors.LiquidEngine, InternalBallisticsSimulationParams]:
    """1 kN-class N2O / Ethanol biliquid engine (HalfCat Sphinx-like)."""
    oxidizer_name = "N2O"
    fuel_name = "Ethanol"

    oxidizer = propellants.PropellantComponent(
        name=oxidizer_name,
        role=propellants.ComponentRole.OXIDIZER,
        density=745.0,
        chemical_formula={"N": 2, "O": 1},
        enthalpy=0.0,
        initial_temperature=300.0,
    )
    fuel = propellants.PropellantComponent(
        name=fuel_name,
        role=propellants.ComponentRole.FUEL,
        density=789.0,
        chemical_formula={"C": 2, "H": 6, "O": 1},
        enthalpy=0.0,
        initial_temperature=300.0,
    )
    propellant = propellants.BiliquidPropellant(
        name=f"{oxidizer_name}/{fuel_name}",
        components=[oxidizer, fuel],
        combustion_efficiency=0.98,
        of_ratio=1.9495,
    )

    fuel_tank = tanks.Tank(
        fuel_name.upper(),
        volume=2.261e-4,
        temperature=300,
        initial_fluid_mass=1.55,
    )
    oxidizer_tank = tanks.Tank(
        oxidizer_name,
        volume=3.622e-3,
        temperature=300,
        initial_fluid_mass=2.78,
    )
    feed_system = feed_systems.StackedTankPressureFedFeedSystem(
        oxidizer_line_diameter=7.925e-3,
        oxidizer_line_length=0.5,
        fuel_line_diameter=5.715e-3,
        fuel_line_length=0.5,
        oxidizer_tank=oxidizer_tank,
        fuel_tank=fuel_tank,
        piston_loss=1e5,
    )

    nozzle = thrust_chamber_models.Nozzle(
        inlet_diameter=55e-3,
        throat_diameter=25.4e-3,
        divergent_angle=12,
        convergent_angle=45,
        expansion_ratio=4,
    )
    injector = thrust_chamber_models.BipropellantInjector(
        discharge_coefficient_fuel=0.48,
        discharge_coefficient_oxidizer=0.48,
        area_fuel=8.2e-6 / 0.48,
        area_ox=1.4e-5 / 0.48,
    )
    combustion_chamber = thrust_chamber_models.CombustionChamber(
        casing_inner_diameter=70e-3,
        casing_outer_diameter=76e-3,
        internal_length=13e-3,
        thermal_liner_thickness=2e-3,
    )
    thrust_chamber = thrust_chamber_models.LiquidEngineThrustChamber(
        nozzle=nozzle,
        injector=injector,
        combustion_chamber=combustion_chamber,
        dry_mass=2,
        center_of_gravity_coordinate=(0.02, 0.0, 0.0),
    )
    motor = motors.LiquidEngine(
        propellant=propellant,
        feed_system=feed_system,
        thrust_chamber=thrust_chamber,
        oxidizer_tank_cog=0.5,
        fuel_tank_cog=0.4,
    )
    params = InternalBallisticsSimulationParams(
        d_t=1e-4,
        igniter_pressure=1e6,
        external_pressure=1e5,
        other_losses=12.0,
    )
    return motor, params


@pytest.fixture(scope="module")
def simulation_result() -> SimulationResult:
    motor, params = _build_1kn_lre()
    return run_simulation(motor, params)


def test_simulation_completes_with_terminal_state(
    simulation_result: SimulationResult,
) -> None:
    state = simulation_result.state
    assert isinstance(state, LiquidEngineState)
    assert state.end_thrust is True
    assert simulation_result.time.size == len(state.t)
    assert simulation_result.time.size > 1


def test_burn_time_and_thrust_time_are_finite_and_ordered(
    simulation_result: SimulationResult,
) -> None:
    state = simulation_result.state
    assert np.isfinite(state.burn_time)
    assert np.isfinite(state.thrust_time)
    assert state.burn_time > 0.0
    assert state.thrust_time >= state.burn_time


def test_propellant_masses_are_monotone_non_increasing(
    simulation_result: SimulationResult,
) -> None:
    state = simulation_result.state
    for series_name in ("fuel_mass", "oxidizer_mass", "propellant_mass"):
        series = np.asarray(getattr(state, series_name))
        diffs = np.diff(series)
        assert (diffs <= 1e-9).all(), (
            f"{series_name} increased between steps; max delta={diffs.max():.3e}"
        )
        assert series[-1] <= series[0]


def test_chamber_pressure_and_thrust_are_physically_plausible(
    simulation_result: SimulationResult,
) -> None:
    state = simulation_result.state
    peak_pressure = float(np.max(state.chamber_pressure))
    peak_thrust = float(np.max(state.thrust))
    # A 1 kN-class biliquid engine should peak at 0.5 to 5 MPa chamber pressure
    # and produce on the order of 100 N to 10 kN of peak thrust.
    assert 0.5e6 < peak_pressure < 5.0e6, (
        f"peak chamber pressure {peak_pressure:.2e} Pa outside [5e5, 5e6]"
    )
    assert 100.0 < peak_thrust < 1.0e4, (
        f"peak thrust {peak_thrust:.2e} N outside [100, 1e4]"
    )


def test_recorded_per_timestep_arrays_are_aligned(
    simulation_result: SimulationResult,
) -> None:
    assert_recorded_arrays_aligned(
        simulation_result.state,
        attribute_names=(
            "chamber_pressure",
            "exit_pressure",
            "thrust",
            "thrust_coefficient",
            "thrust_coefficient_ideal",
            "fuel_mass",
            "oxidizer_mass",
            "propellant_mass",
            "nozzle_correction_factor",
            "fuel_tank_pressure",
            "oxidizer_tank_pressure",
        ),
    )
