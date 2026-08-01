import pytest

import machwave.core.incompressible_flow as incompressible_flow
import machwave.models.feed_systems.tank as tank_models
from machwave.models.thrust_chamber import MassFlowModel
from tests.factories import (
    BipropellantInjectorFactory,
    StackedTankPressureFedFeedSystemFactory,
)

# Nitrous oxide has no CoolProp viscosity model, so a line on it needs one.
OXIDIZER_VISCOSITY = 1e-4


def test_get_mass_flow_ox_delegates_to_injector_dispatch():
    """Feed-system call equals the injector's own dispatch on the ox tank."""
    oxidizer_mass = 5.0
    oxidizer_tank = tank_models.Tank(
        fluid_name="N2O",
        volume=0.01,
        temperature=293.0,
        initial_fluid_mass=oxidizer_mass,
    )
    feed_system = StackedTankPressureFedFeedSystemFactory.build(
        oxidizer_tank=oxidizer_tank,
    )
    injector = BipropellantInjectorFactory.build(
        mass_flow_model_oxidizer=MassFlowModel.HEM,
    )
    chamber_pressure = 20e5

    actual = feed_system.get_mass_flow_ox(
        chamber_pressure, injector=injector, oxidizer_mass=oxidizer_mass
    )
    expected = injector.get_mass_flow_ox(
        tank=oxidizer_tank,
        pressure_upstream=feed_system.get_oxidizer_tank_pressure(
            oxidizer_mass=oxidizer_mass
        ),
        chamber_pressure=chamber_pressure,
        fluid_mass=oxidizer_mass,
    )
    assert actual == pytest.approx(expected)


def test_get_mass_flow_fuel_uses_piston_pressurized_upstream():
    """Fuel-side upstream is the oxidizer tank pressure minus piston loss."""
    feed_system = StackedTankPressureFedFeedSystemFactory.build(
        piston_loss=2e5, fuel_line_length=0.0
    )
    injector = BipropellantInjectorFactory.build()
    chamber_pressure = 15e5
    oxidizer_mass = feed_system.oxidizer_tank.initial_fluid_mass
    fuel_mass = feed_system.fuel_tank.initial_fluid_mass

    actual = feed_system.get_mass_flow_fuel(
        chamber_pressure,
        injector=injector,
        fuel_mass=fuel_mass,
        oxidizer_mass=oxidizer_mass,
    )
    expected = injector.get_mass_flow_fuel(
        tank=feed_system.fuel_tank,
        pressure_upstream=feed_system.get_oxidizer_tank_pressure(
            oxidizer_mass=oxidizer_mass
        )
        - 2e5,
        chamber_pressure=chamber_pressure,
        fluid_mass=fuel_mass,
    )
    assert actual == pytest.approx(expected)


class TestFeedlinePressureDrop:
    def test_a_line_at_rest_takes_nothing(self):
        feed_system = StackedTankPressureFedFeedSystemFactory.build()
        fuel_mass = feed_system.fuel_tank.initial_fluid_mass
        oxidizer_mass = feed_system.oxidizer_tank.initial_fluid_mass

        assert feed_system.get_fuel_tank_pressure(
            oxidizer_mass=oxidizer_mass, fuel_mass=fuel_mass, mass_flow_rate=0.0
        ) == feed_system.oxidizer_tank.get_pressure(oxidizer_mass)

    def test_a_flowing_line_takes_the_darcy_weisbach_drop(self):
        feed_system = StackedTankPressureFedFeedSystemFactory.build()
        fuel_tank = feed_system.fuel_tank
        fuel_mass = fuel_tank.initial_fluid_mass
        oxidizer_mass = feed_system.oxidizer_tank.initial_fluid_mass
        mass_flow_rate = 0.4

        delivered = feed_system.get_fuel_tank_pressure(
            oxidizer_mass=oxidizer_mass,
            fuel_mass=fuel_mass,
            mass_flow_rate=mass_flow_rate,
        )

        expected_drop = incompressible_flow.get_pipe_pressure_drop(
            density=fuel_tank.get_density(fuel_mass),
            mass_flow_rate=mass_flow_rate,
            length=feed_system.fuel_line_length,
            diameter=feed_system.fuel_line_diameter,
            dynamic_viscosity=fuel_tank.get_dynamic_viscosity(fuel_mass),
        )
        assert expected_drop > 0.0
        assert delivered == pytest.approx(
            feed_system.oxidizer_tank.get_pressure(oxidizer_mass) - expected_drop
        )

    def test_the_drop_grows_with_the_flow(self):
        feed_system = StackedTankPressureFedFeedSystemFactory.build()
        fuel_mass = feed_system.fuel_tank.initial_fluid_mass
        oxidizer_mass = feed_system.oxidizer_tank.initial_fluid_mass

        pressures = [
            feed_system.get_fuel_tank_pressure(
                oxidizer_mass=oxidizer_mass,
                fuel_mass=fuel_mass,
                mass_flow_rate=mass_flow_rate,
            )
            for mass_flow_rate in (0.1, 0.2, 0.4)
        ]

        assert pressures == sorted(pressures, reverse=True)

    def test_a_line_holds_the_flow_below_the_lossless_one(self):
        with_line = StackedTankPressureFedFeedSystemFactory.build(fuel_line_length=2.0)
        without_line = StackedTankPressureFedFeedSystemFactory.build(
            fuel_line_length=0.0
        )
        injector = BipropellantInjectorFactory.build()
        chamber_pressure = 15e5
        fuel_mass = with_line.fuel_tank.initial_fluid_mass
        oxidizer_mass = with_line.oxidizer_tank.initial_fluid_mass

        flows = [
            feed_system.get_mass_flow_fuel(
                chamber_pressure,
                injector=injector,
                fuel_mass=fuel_mass,
                oxidizer_mass=oxidizer_mass,
            )
            for feed_system in (with_line, without_line)
        ]

        assert 0.0 < flows[0] < flows[1]

    def test_the_solved_flow_matches_its_own_delivered_pressure(self):
        feed_system = StackedTankPressureFedFeedSystemFactory.build(
            fuel_line_length=2.0
        )
        injector = BipropellantInjectorFactory.build()
        chamber_pressure = 15e5
        fuel_mass = feed_system.fuel_tank.initial_fluid_mass
        oxidizer_mass = feed_system.oxidizer_tank.initial_fluid_mass

        mass_flow_rate = feed_system.get_mass_flow_fuel(
            chamber_pressure,
            injector=injector,
            fuel_mass=fuel_mass,
            oxidizer_mass=oxidizer_mass,
        )
        delivered = feed_system.get_fuel_tank_pressure(
            oxidizer_mass=oxidizer_mass,
            fuel_mass=fuel_mass,
            mass_flow_rate=mass_flow_rate,
        )

        assert injector.get_mass_flow_fuel(
            tank=feed_system.fuel_tank,
            pressure_upstream=delivered,
            chamber_pressure=chamber_pressure,
            fluid_mass=fuel_mass,
        ) == pytest.approx(mass_flow_rate, rel=1e-3)

    def test_a_line_that_would_eat_the_head_throttles_instead_of_stopping(self):
        # A hair-thin line settles at the trickle its own drop allows, rather
        # than at the nothing an iteration overshooting its first guess reports.
        injector = BipropellantInjectorFactory.build()
        chamber_pressure = 15e5

        flows = []
        for fuel_line_diameter in (5e-4, 8e-3):
            feed_system = StackedTankPressureFedFeedSystemFactory.build(
                fuel_line_diameter=fuel_line_diameter, fuel_line_length=5.0
            )
            flows.append(
                feed_system.get_mass_flow_fuel(
                    chamber_pressure,
                    injector=injector,
                    fuel_mass=feed_system.fuel_tank.initial_fluid_mass,
                    oxidizer_mass=feed_system.oxidizer_tank.initial_fluid_mass,
                )
            )

        assert 0.0 < flows[0] < 0.1 * flows[1]

    def test_a_tank_below_the_chamber_does_not_feed(self):
        feed_system = StackedTankPressureFedFeedSystemFactory.build()
        injector = BipropellantInjectorFactory.build()
        fuel_mass = feed_system.fuel_tank.initial_fluid_mass
        oxidizer_mass = feed_system.oxidizer_tank.initial_fluid_mass
        chamber_pressure = 2 * feed_system.get_fuel_tank_pressure(
            oxidizer_mass=oxidizer_mass, fuel_mass=fuel_mass
        )

        assert (
            feed_system.get_mass_flow_fuel(
                chamber_pressure,
                injector=injector,
                fuel_mass=fuel_mass,
                oxidizer_mass=oxidizer_mass,
            )
            == 0.0
        )

    def test_the_oxidizer_line_is_not_on_the_fuel_path(self):
        oxidizer_tank = tank_models.Tank(
            fluid_name="N2O",
            volume=0.01,
            temperature=293.0,
            initial_fluid_mass=5.0,
            dynamic_viscosity=OXIDIZER_VISCOSITY,
        )
        feed_system = StackedTankPressureFedFeedSystemFactory.build(
            oxidizer_tank=oxidizer_tank,
            oxidizer_line_length=2.0,
            fuel_line_length=0.0,
        )
        fuel_mass = feed_system.fuel_tank.initial_fluid_mass
        oxidizer_mass = oxidizer_tank.initial_fluid_mass

        assert feed_system.get_fuel_tank_pressure(
            oxidizer_mass=oxidizer_mass, fuel_mass=fuel_mass, mass_flow_rate=0.5
        ) == pytest.approx(oxidizer_tank.get_pressure(oxidizer_mass))
        assert feed_system.get_oxidizer_tank_pressure(
            oxidizer_mass=oxidizer_mass, mass_flow_rate=0.5
        ) < oxidizer_tank.get_pressure(oxidizer_mass)


class TestValidation:
    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("oxidizer_line_diameter", 0.0),
            ("fuel_line_diameter", -0.01),
            ("oxidizer_line_length", -1.0),
            ("fuel_line_length", -1.0),
            ("piston_loss", -1.0),
            ("oxidizer_line_loss_coefficient", -1.0),
            ("fuel_line_loss_coefficient", -1.0),
        ],
    )
    def test_rejects_out_of_range_line_inputs(self, field, value):
        with pytest.raises(ValueError, match=field):
            StackedTankPressureFedFeedSystemFactory.build(**{field: value})
