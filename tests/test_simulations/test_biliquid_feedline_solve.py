"""The injector flow of a line solved together with its own feedline loss."""

from __future__ import annotations

import math

import pytest
import scipy.optimize

import machwave.models.feed_systems as feed_systems_models
import machwave.models.thrust_chamber.injector as injector_models
import machwave.simulation.biliquid.states as biliquid_states
from tests.factories import (
    FluidStateFactory,
    InjectorElementFactory,
    PropellantLineFactory,
    TankFactory,
)

HEAD_PRESSURE = 55e5
CHAMBER_PRESSURE = 30e5
DENSITY = 790.0


def solve(line, element, head_state=None, chamber_pressure=CHAMBER_PRESSURE):
    return biliquid_states.get_injector_mass_flows(
        chamber_pressure,
        injector=injector_models.Injector(elements={line.name: element}),
        lines={line.name: line},
        inlet_states={
            line.name: head_state
            or FluidStateFactory.build(
                fluid_name="Ethanol", pressure=HEAD_PRESSURE, density=DENSITY
            )
        },
        line_masses={line.name: math.inf},
        is_feeding=True,
        d_t=1.0,
    )[line.name]


def get_solve_tolerance(element, head_state, chamber_pressure=CHAMBER_PRESSURE):
    return biliquid_states.LINE_FLOW_RELATIVE_TOLERANCE * element.get_mass_flow(
        inlet=head_state, chamber_pressure=chamber_pressure
    )


ETHANOL_HEAD = FluidStateFactory.build(
    fluid_name="Ethanol", pressure=HEAD_PRESSURE, density=DENSITY
)


class TestIncompressibleSeriesResistances:
    """The orifice and the line act as two quadratic resistances in series."""

    @pytest.mark.parametrize("loss_coefficient", [0.5, 5.0, 50.0])
    def test_matches_the_closed_form(self, loss_coefficient):
        element = InjectorElementFactory.build(discharge_coefficient=0.6, area=1.5e-5)
        resistance = feed_systems_models.FeedlineResistance(
            loss_coefficient=loss_coefficient, flow_area=3.0e-5
        )
        line = PropellantLineFactory.build(resistance=resistance)

        expected = math.sqrt(
            2.0
            * DENSITY
            * (HEAD_PRESSURE - CHAMBER_PRESSURE)
            / (1.0 / (0.6 * 1.5e-5) ** 2 + loss_coefficient / 3.0e-5**2)
        )

        assert solve(line, element) == pytest.approx(
            expected, abs=get_solve_tolerance(element, ETHANOL_HEAD)
        )

    def test_a_line_without_resistance_is_the_bare_orifice(self):
        element = InjectorElementFactory.build(discharge_coefficient=0.6, area=1.5e-5)
        line = PropellantLineFactory.build()

        assert solve(line, element) == pytest.approx(
            0.6 * 1.5e-5 * math.sqrt(2.0 * DENSITY * (HEAD_PRESSURE - CHAMBER_PRESSURE))
        )

    def test_a_quarter_of_the_driving_pressure_halves_the_flow(self):
        element = InjectorElementFactory.build(discharge_coefficient=0.6, area=1.5e-5)
        resistance = feed_systems_models.FeedlineResistance(
            loss_coefficient=5.0, flow_area=3.0e-5
        )
        line = PropellantLineFactory.build(resistance=resistance)

        quarter_chamber_pressure = (
            HEAD_PRESSURE - (HEAD_PRESSURE - CHAMBER_PRESSURE) / 4
        )
        full = solve(line, element)
        quarter = solve(line, element, chamber_pressure=quarter_chamber_pressure)

        # each flow carries its own solve tolerance
        assert quarter == pytest.approx(
            full / 2.0,
            abs=get_solve_tolerance(element, ETHANOL_HEAD)
            + get_solve_tolerance(element, ETHANOL_HEAD, quarter_chamber_pressure),
        )


class TestNoFlow:
    def test_no_flow_once_the_chamber_reaches_the_head(self):
        element = InjectorElementFactory.build()
        line = PropellantLineFactory.build(
            resistance=feed_systems_models.FeedlineResistance(
                loss_coefficient=5.0, flow_area=3.0e-5
            )
        )

        assert solve(line, element, chamber_pressure=HEAD_PRESSURE) == 0.0

    def test_flows_on_a_drop_below_the_design_line_loss(self):
        """A fixed 2 bar loss would have stopped this 0.1 bar drop from flowing."""
        element = InjectorElementFactory.build()
        line = PropellantLineFactory.build(
            resistance=feed_systems_models.FeedlineResistance.from_design_point(
                pressure_drop=2e5, mass_flow=0.5, density=DENSITY, flow_area=9.37e-5
            )
        )

        assert solve(line, element, chamber_pressure=HEAD_PRESSURE - 1e4) > 0.0


class TestSaturatedNitrousOxide:
    def test_the_element_sees_the_head_less_the_line_drop(self):
        element = InjectorElementFactory.build(area=1.4e-5 / 0.48)
        line = PropellantLineFactory.build(
            resistance=feed_systems_models.FeedlineResistance(
                loss_coefficient=5.0, flow_area=2.0e-5
            )
        )
        head = FluidStateFactory.build(
            fluid_name="N2O", pressure=57e5, temperature=300.0, density=725.0
        )

        flow = solve(line, element, head_state=head)
        seen = FluidStateFactory.build(
            fluid_name="N2O",
            pressure=57e5 - line.resistance.get_pressure_drop(flow, 725.0),
            temperature=300.0,
            density=725.0,
        )

        assert (
            0.0
            < flow
            < element.get_mass_flow(inlet=head, chamber_pressure=CHAMBER_PRESSURE)
        )
        assert flow == pytest.approx(
            element.get_mass_flow(inlet=seen, chamber_pressure=CHAMBER_PRESSURE),
            rel=1e-8,
        )

    def test_matches_a_tight_root_find(self):
        element = InjectorElementFactory.build(area=1.4e-5 / 0.48)
        resistance = feed_systems_models.FeedlineResistance(
            loss_coefficient=5.0, flow_area=2.0e-5
        )
        line = PropellantLineFactory.build(resistance=resistance)
        head = FluidStateFactory.build(
            fluid_name="N2O", pressure=57e5, temperature=290.0, density=785.0
        )

        def residual(mass_flow):
            seen = FluidStateFactory.build(
                fluid_name="N2O",
                pressure=57e5 - resistance.get_pressure_drop(mass_flow, 785.0),
                temperature=290.0,
                density=785.0,
            )
            return mass_flow - element.get_mass_flow(
                inlet=seen, chamber_pressure=CHAMBER_PRESSURE
            )

        reference = scipy.optimize.brentq(
            residual,
            0.0,
            element.get_mass_flow(inlet=head, chamber_pressure=CHAMBER_PRESSURE),
            xtol=1e-14,
        )

        assert solve(line, element, head_state=head) == pytest.approx(
            reference, rel=1e-8
        )


class TestCap:
    def test_no_line_delivers_more_than_it_holds_over_the_step(self):
        element = InjectorElementFactory.build()
        line = PropellantLineFactory.build(
            name="fuel",
            resistance=feed_systems_models.FeedlineResistance(
                loss_coefficient=5.0, flow_area=3.0e-5
            ),
        )
        injector = injector_models.Injector(elements={"fuel": element})

        flows = biliquid_states.get_injector_mass_flows(
            CHAMBER_PRESSURE,
            injector=injector,
            lines={"fuel": line},
            inlet_states={
                "fuel": FluidStateFactory.build(
                    fluid_name="Ethanol", pressure=HEAD_PRESSURE, density=DENSITY
                )
            },
            line_masses={"fuel": 1e-6},
            is_feeding=True,
            d_t=1e-4,
        )

        assert flows["fuel"] == pytest.approx(1e-2)
