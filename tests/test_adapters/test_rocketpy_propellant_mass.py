"""Tests for the simulated propellant mass passed to RocketPy."""

import numpy as np
import pytest
import rocketpy

import machwave.adapters.rocketpy as rocketpy_adapters
import machwave.adapters.rocketpy.base as rocketpy_base
import machwave.models.grain as grain_models
import machwave.models.motors as motors_models
import machwave.models.propellants.formulations.solid as solid_propellants
import machwave.simulation as machwave_simulation
import machwave.simulation.solid.results as solid_results

from tests.factories import (
    BatesSegmentFactory,
    CombustionChamberFactory,
    NozzleFactory,
    SolidMotorFactory,
    SolidMotorThrustChamberFactory,
)

DRY_MASS = 6.0


@pytest.fixture(scope="module")
def simulated_motor() -> tuple[
    motors_models.SolidMotor, solid_results.SolidSimulationResult
]:
    grain = grain_models.Grain(spacing=0.01)
    for _ in range(4):
        grain.add_segment(
            BatesSegmentFactory.build(
                outer_diameter=0.085, core_diameter=0.035, length=0.150
            )
        )
    thrust_chamber = SolidMotorThrustChamberFactory.build(
        nozzle=NozzleFactory.build(
            throat_diameter=0.022, divergent_angle=12, expansion_ratio=8
        ),
        combustion_chamber=CombustionChamberFactory.build(
            inner_diameter=89.25e-3, internal_length=grain.total_length + 0.01
        ),
        dry_mass=DRY_MASS,
        center_of_gravity_coordinate=(0.35, 0.0, 0.0),
        moment_of_inertia=(0.19, 0.19, 0.008),
    )
    motor = SolidMotorFactory.build(
        grain=grain,
        propellant=solid_propellants.KNSB_NAKKA,
        thrust_chamber=thrust_chamber,
    )
    params = machwave_simulation.InternalBallisticsSimulationParams(
        d_t=0.01, igniter_pressure=1e6, external_pressure=1.013e5
    )
    result = machwave_simulation.InternalBallisticsSimulation(
        motor=motor, params=params
    ).run()
    return motor, result


@pytest.fixture(
    scope="module",
    params=[
        rocketpy_adapters.RocketPySolidMotorAdapter,
        rocketpy_adapters.RocketPyGenericMotorAdapter,
    ],
    ids=["solid_motor", "generic_motor"],
)
def adapter(request, simulated_motor) -> rocketpy_base.RocketPyMotorAdapter:
    motor, result = simulated_motor
    return request.param(motor=motor, simulation_result=result)


def test_propellant_mass_matches_the_simulation(adapter) -> None:
    result = adapter.simulation_result

    assert adapter.propellant_mass(result.time) == pytest.approx(result.propellant_mass)


def test_mass_flow_rate_integrates_to_the_expelled_propellant_mass(adapter) -> None:
    result = adapter.simulation_result

    expelled_mass = -adapter.total_mass_flow_rate.integral(
        result.time[0], result.time[-1]
    )

    assert expelled_mass == pytest.approx(
        result.propellant_mass[0] - result.propellant_mass[-1]
    )


def test_mass_flow_rate_is_the_derivative_of_the_propellant_mass(adapter) -> None:
    result = adapter.simulation_result
    burning = result.propellant_mass > 0

    mass_flow_rate = adapter.total_mass_flow_rate(result.time[burning])
    finite_difference = np.gradient(result.propellant_mass, result.time)[burning]

    assert np.all(mass_flow_rate < 0)
    assert mass_flow_rate == pytest.approx(finite_difference)


def test_mass_flow_rate_matches_the_total_mass_flow_rate(adapter) -> None:
    time = adapter.simulation_result.time

    assert adapter.mass_flow_rate(time) == pytest.approx(
        adapter.total_mass_flow_rate(time)
    )


def test_total_mass_at_burnout_equals_dry_mass(adapter) -> None:
    burn_out_time = adapter.burn_out_time

    assert adapter.total_mass(burn_out_time) == pytest.approx(DRY_MASS)
    assert adapter.total_mass(burn_out_time + 1.0) == pytest.approx(DRY_MASS)
    assert adapter.total_mass_flow_rate(burn_out_time + 1.0) == pytest.approx(0.0)


@pytest.mark.parametrize("equations_of_motion", ["standard", "solid_propulsion"])
def test_flight_reaches_apogee(adapter, equations_of_motion) -> None:
    rocket = rocketpy.Rocket(
        radius=0.0508,
        mass=15.0,
        inertia=(6.0, 6.0, 0.035),
        power_off_drag=0.5,
        power_on_drag=0.5,
        center_of_mass_without_motor=0.0,
    )
    rocket.add_motor(adapter, position=-0.6)
    environment = rocketpy.Environment(
        latitude=32.99, longitude=-106.975, elevation=1400
    )
    environment.set_atmospheric_model(type="standard_atmosphere")

    flight = rocketpy.Flight(
        rocket=rocket,
        environment=environment,
        rail_length=5.2,
        inclination=85,
        heading=0,
        equations_of_motion=equations_of_motion,
    )

    assert flight.apogee_time > adapter.burn_out_time
    assert flight.apogee - environment.elevation > 1000.0
