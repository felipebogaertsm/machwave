"""End-to-end integration tests for LiquidEngine internal ballistics
simulations.

The motor configuration below mirrors the one in examples/1kn_lre.py
(the lone biliquid example) but is duplicated here so the tests stay
independent of the example layer.
"""

from __future__ import annotations

import numpy as np
import pytest

from machwave.models import motors
from machwave.simulation import InternalBallisticsSimulationParams
from machwave.states import LiquidEngineState
from tests.factories import (
    BiliquidPropellantFactory,
    BipropellantInjectorFactory,
    CombustionChamberFactory,
    FuelComponentFactory,
    LiquidEngineFactory,
    LiquidEngineThrustChamberFactory,
    NozzleFactory,
    OxidizerComponentFactory,
    StackedTankPressureFedFeedSystemFactory,
    TankFactory,
)
from tests.test_simulations.conftest import (
    SimulationResult,
    assert_recorded_arrays_aligned,
    run_simulation,
)


def _build_1kn_lre() -> tuple[motors.LiquidEngine, InternalBallisticsSimulationParams]:
    """1 kN-class N2O / Ethanol biliquid engine (HalfCat Sphinx-like)."""
    oxidizer = OxidizerComponentFactory.build(initial_temperature=300.0)
    fuel = FuelComponentFactory.build(initial_temperature=300.0)
    propellant = BiliquidPropellantFactory.build(
        components=[oxidizer, fuel],
        oxidizer_to_fuel_ratio=1.9495,
    )

    feed_system = StackedTankPressureFedFeedSystemFactory.build(
        oxidizer_tank=TankFactory.build(
            fluid_name="N2O",
            volume=3.80e-3,
            temperature=300,
            initial_fluid_mass=2.78,
        ),
        fuel_tank=TankFactory.build(
            fluid_name="ETHANOL",
            volume=2.0e-3,
            temperature=300,
            initial_fluid_mass=1.55,
        ),
        oxidizer_line_diameter=7.925e-3,
        oxidizer_line_length=0.5,
        fuel_line_diameter=5.715e-3,
        fuel_line_length=0.5,
        piston_loss=1e5,
    )

    thrust_chamber = LiquidEngineThrustChamberFactory.build(
        nozzle=NozzleFactory.build(
            inlet_diameter=55e-3,
            throat_diameter=25.4e-3,
            divergent_angle=12,
            convergent_angle=45,
            expansion_ratio=4,
        ),
        injector=BipropellantInjectorFactory.build(),
        combustion_chamber=CombustionChamberFactory.build(
            casing_inner_diameter=70e-3,
            casing_outer_diameter=76e-3,
            internal_length=13e-3,
            thermal_liner_thickness=2e-3,
        ),
    )

    motor = LiquidEngineFactory.build(
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
        other_losses=0.12,
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


def test_thrust_time_is_finite_and_positive(
    simulation_result: SimulationResult,
) -> None:
    state = simulation_result.state
    assert np.isfinite(state.thrust_time)
    assert state.thrust_time > 0.0


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
        assert (series >= -1e-9).all(), (
            f"{series_name} went negative; min={series.min():.3e}"
        )


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


def _build_state_for_burnout_test() -> LiquidEngineState:
    motor, params = _build_1kn_lre()
    return LiquidEngineState(
        motor=motor,
        initial_pressure=params.igniter_pressure,
        initial_atmospheric_pressure=params.external_pressure,
        other_losses=params.other_losses,
    )


def test_run_timestep_sets_end_burn_when_fuel_exhausts() -> None:
    state = _build_state_for_burnout_test()
    state.fuel_mass[-1] = 1e-9

    state.run_timestep(d_t=1e-4, external_pressure=1e5)

    assert state.end_burn is True
    assert state.burn_time == pytest.approx(state.t[-1])


def test_run_timestep_sets_end_burn_when_oxidizer_exhausts() -> None:
    state = _build_state_for_burnout_test()
    state.oxidizer_mass[-1] = 1e-9

    state.run_timestep(d_t=1e-4, external_pressure=1e5)

    assert state.end_burn is True
    assert state.burn_time == pytest.approx(state.t[-1])


def test_live_mixture_ratio_drives_cea(
    simulation_result: SimulationResult,
) -> None:
    state = simulation_result.state
    assert isinstance(state, LiquidEngineState)
    propellant = state.motor.propellant

    design_ratio = propellant.oxidizer_to_fuel_ratio
    assert design_ratio is not None

    fuel_mass = np.asarray(state.fuel_mass)
    oxidizer_mass = np.asarray(state.oxidizer_mass)
    fuel_consumed = -np.diff(fuel_mass)
    oxidizer_consumed = -np.diff(oxidizer_mass)
    valid = fuel_consumed > 0
    live_ratios = oxidizer_consumed[valid] / fuel_consumed[valid]
    assert np.any(np.abs(live_ratios - design_ratio) > 1e-6), (
        "Live oxidizer/fuel mass deltas never deviated from the design ratio"
    )

    chamber_pressure = state.chamber_pressure[len(state.chamber_pressure) // 2]
    expansion_ratio = state.motor.thrust_chamber.nozzle.expansion_ratio
    design_props = propellant.evaluate(
        chamber_pressure=chamber_pressure,
        expansion_ratio=expansion_ratio,
        mixture_ratio=design_ratio,
    )
    live_props = propellant.properties
    assert live_props is not None
    assert (
        live_props.adiabatic_flame_temperature
        != design_props.adiabatic_flame_temperature
    )


def test_simulation_runs_through_burnout_without_crashing(
    simulation_result: SimulationResult,
) -> None:
    state = simulation_result.state
    assert state.end_thrust is True
    assert state.propellant_mass[-1] <= state.propellant_mass[0]
