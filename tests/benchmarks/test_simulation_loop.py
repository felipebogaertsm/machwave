from __future__ import annotations

import dataclasses
import warnings

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

import machwave.simulation as simulation_module

from tests.test_simulations import motor_builders


def _run_simulation_silently(
    simulation: simulation_module.InternalBallisticsSimulation,
) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        simulation.run()


@pytest.mark.benchmark(group="simulation-loop")
def test_solid_motor_simulation_loop(benchmark: BenchmarkFixture) -> None:
    def setup() -> tuple[
        tuple[simulation_module.InternalBallisticsSimulation], dict[str, object]
    ]:
        motor, params = motor_builders.build_kappa_rnakka_motor()
        params = dataclasses.replace(params, d_t=0.01)
        simulation = simulation_module.InternalBallisticsSimulation(
            motor=motor, params=params
        )
        return (simulation,), {}

    benchmark.pedantic(
        _run_simulation_silently,
        setup=setup,
        rounds=5,
        iterations=1,
        warmup_rounds=0,
    )


@pytest.mark.benchmark(group="simulation-loop")
def test_liquid_engine_simulation_loop(benchmark: BenchmarkFixture) -> None:
    def setup() -> tuple[
        tuple[simulation_module.InternalBallisticsSimulation], dict[str, object]
    ]:
        motor, params = motor_builders.build_1kn_lre()
        params = dataclasses.replace(params, d_t=4e-4)
        simulation = simulation_module.InternalBallisticsSimulation(
            motor=motor, params=params
        )
        return (simulation,), {}

    benchmark.pedantic(
        _run_simulation_silently,
        setup=setup,
        rounds=3,
        iterations=1,
        warmup_rounds=0,
    )
