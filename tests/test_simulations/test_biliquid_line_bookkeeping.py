"""The engine state, results and report carry one series per propellant line.

The third line here drains and is accounted for like any other, but nothing
evaluates the mixture it makes: blending a third propellant through the
thermochemical service is separate work. These cover the bookkeeping.
"""

from __future__ import annotations

import io

import numpy as np
import pytest

import machwave.models.feed_systems as feed_systems_models
import machwave.models.feed_systems.tank as tank_models
import machwave.models.propellants as propellants_models
import machwave.models.thrust_chamber as thrust_chamber_models
import machwave.simulation.biliquid as biliquid_simulation
from tests.test_simulations import motor_builders
from tests.test_simulations.conftest import (
    assert_recorded_arrays_aligned,
    run_simulation,
)

DILUENT_LINE_NAME = "diluent"


def build_engine_with_a_diluent_line():
    """The 1 kN engine with a third line stacked below the piston."""
    motor, params = motor_builders.build_1kn_biliquid_engine()
    feed_system = motor.feed_system

    diluent_line = feed_systems_models.PropellantLine(
        name=DILUENT_LINE_NAME,
        role=propellants_models.ComponentRole.ADDITIVE,
        tank=tank_models.Tank(
            fluid_name="Water",
            volume=1.0e-3,
            temperature=300.0,
            initial_fluid_mass=0.5,
        ),
    )
    motor.feed_system = feed_systems_models.StackedTankPressureFedFeedSystem(
        lines=[*feed_system.lines.values(), diluent_line],
        pressurizing_line="oxidizer",
        piston_loss=feed_system.piston_loss,
        line_losses={**feed_system.line_losses, DILUENT_LINE_NAME: 2e5},
    )
    motor.thrust_chamber.injector = thrust_chamber_models.Injector(
        elements={
            **motor.thrust_chamber.injector.elements,
            DILUENT_LINE_NAME: thrust_chamber_models.InjectorElement(
                discharge_coefficient=0.48, area=2.0e-6 / 0.48
            ),
        }
    )
    return motor, params


@pytest.fixture(scope="module")
def state_after_one_timestep():
    motor, params = build_engine_with_a_diluent_line()
    state = biliquid_simulation.BiliquidEngineState(
        motor=motor,
        igniter_pressure=params.igniter_pressure,
        external_pressure=params.external_pressure,
    )
    state.run_timestep(params.d_t, params.external_pressure)
    return state


class TestStatePerLine:
    def test_every_series_is_keyed_by_line_name(self, state_after_one_timestep):
        state = state_after_one_timestep
        expected = {"oxidizer", "fuel", DILUENT_LINE_NAME}

        assert set(state.fluid_mass_per_line) == expected
        assert set(state.mass_flow_rate_per_line) == expected
        assert set(state.tank_pressure_per_line) == expected
        assert set(state.tank_temperature_per_line) == expected
        assert set(state.internal_energy_per_line) == expected

    def test_a_line_starts_at_its_tank_loading(self, state_after_one_timestep):
        state = state_after_one_timestep

        assert state.fluid_mass_per_line[DILUENT_LINE_NAME][0] == pytest.approx(0.5)

    def test_a_third_line_drains_like_any_other(self, state_after_one_timestep):
        state = state_after_one_timestep

        assert state.mass_flow_rate_per_line[DILUENT_LINE_NAME][-1] > 0.0
        assert (
            state.fluid_mass_per_line[DILUENT_LINE_NAME][-1]
            < state.fluid_mass_per_line[DILUENT_LINE_NAME][0]
        )

    def test_the_propellant_mass_adds_up_every_line(self, state_after_one_timestep):
        state = state_after_one_timestep

        assert state.propellant_mass[0] == pytest.approx(
            sum(series[0] for series in state.fluid_mass_per_line.values())
        )


class TestMixtureRatio:
    def test_is_the_oxidizer_total_over_the_fuel_total(self, state_after_one_timestep):
        state = state_after_one_timestep

        ratio = state._get_mixture_ratio(
            {"oxidizer": 3.0, "fuel": 1.0, DILUENT_LINE_NAME: 5.0}
        )

        assert ratio == pytest.approx(3.0)

    def test_an_additive_line_stays_out_of_the_ratio(self, state_after_one_timestep):
        state = state_after_one_timestep
        flows = {"oxidizer": 3.0, "fuel": 1.0}

        assert state._get_mixture_ratio(
            {**flows, DILUENT_LINE_NAME: 5.0}
        ) == state._get_mixture_ratio({**flows, DILUENT_LINE_NAME: 0.0})

    @pytest.mark.parametrize(
        "flows",
        [
            {"oxidizer": 0.0, "fuel": 1.0},
            {"oxidizer": 3.0, "fuel": 0.0},
        ],
    )
    def test_a_side_that_stopped_flowing_leaves_no_ratio(
        self, state_after_one_timestep, flows
    ):
        state = state_after_one_timestep

        assert state._get_mixture_ratio({**flows, DILUENT_LINE_NAME: 1.0}) is None


class TestResultPerLine:
    @pytest.fixture(scope="class")
    def result(self):
        return run_simulation(*build_engine_with_a_diluent_line())

    def test_every_series_is_keyed_by_line_name(self, result):
        expected = {"oxidizer", "fuel", DILUENT_LINE_NAME}

        assert set(result.fluid_mass_per_line) == expected
        assert set(result.tank_pressure_per_line) == expected
        assert set(result.tank_temperature_per_line) == expected
        assert set(result.final_fluid_mass_per_line) == expected

    def test_the_final_mass_is_where_the_series_ended(self, result):
        for name, series in result.fluid_mass_per_line.items():
            assert result.final_fluid_mass_per_line[name] == pytest.approx(series[-1])

    def test_recorded_arrays_stay_aligned(self, result):
        assert_recorded_arrays_aligned(result)

    def test_the_report_lists_every_line(self, result):
        file = io.StringIO()

        result.report(file=file)

        report = file.getvalue()
        assert "PROPELLANT REMAINING (kg)" in report
        for name in result.final_fluid_mass_per_line:
            assert name.capitalize() in report

    def test_the_summary_carries_a_final_mass_per_line(self, result):
        summary = result.summary()

        for name in result.final_fluid_mass_per_line:
            assert f"final_{name}_mass" in summary

    def test_the_masses_never_grow(self, result):
        for name, series in result.fluid_mass_per_line.items():
            assert (np.diff(series) <= 1e-9).all(), f"{name} mass increased"
