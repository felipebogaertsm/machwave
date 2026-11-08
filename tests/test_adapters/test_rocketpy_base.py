"""Tests for the RocketPy base adapter."""

import numpy as np
import pytest
import rocketpy

import machwave.adapters.rocketpy as rocketpy_adapters
import machwave.adapters.rocketpy.base as rocketpy_base
import machwave.models.motors as motors_models
import machwave.simulation.solid.results as solid_results
from tests.test_simulations import motor_builders
from tests.test_simulations.conftest import run_simulation

# Catches only a gross error in the mass passed to RocketPy: the docs example
# reaches about 2.4 km above ground level.
MIN_APOGEE_ABOVE_GROUND = 1000.0


@pytest.fixture(scope="module")
def simulated_motor() -> tuple[
    motors_models.SolidMotor, solid_results.SolidSimulationResult
]:
    motor, params = motor_builders.build_rocketpy_example_motor()
    return motor, run_simulation(motor, params)


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
    dry_mass = adapter.motor.thrust_chamber.dry_mass_properties.dry_mass

    assert adapter.total_mass(burn_out_time) == pytest.approx(dry_mass)
    assert adapter.total_mass(burn_out_time + 1.0) == pytest.approx(dry_mass)
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
    assert flight.apogee - environment.elevation > MIN_APOGEE_ABOVE_GROUND
