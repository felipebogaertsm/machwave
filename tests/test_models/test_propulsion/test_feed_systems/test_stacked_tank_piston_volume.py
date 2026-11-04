"""The fluid at the top of a stacked tank fills the volume the piston sweeps.

As the lines below the piston drain, the piston moves down and the top tank's
fluid fills its own volume plus the liquid volume pushed out below. It boils
to fill the extra space and does boundary work on the piston as it goes.
"""

import CoolProp.CoolProp as CP
import pytest
import scipy.integrate

import machwave.models.feed_systems as feed_systems_models
import machwave.models.feed_systems.tank as tank_models
import machwave.simulation.biliquid.states as biliquid_states
from tests.factories import PropellantLineFactory, TankFactory

OXIDIZER = "N2O"
FUEL = "Ethanol"
TEMPERATURE = 293.0
OXIDIZER_VOLUME = 0.01
OXIDIZER_MASS = 5.0
FUEL_VOLUME = 0.004
FUEL_MASS = 3.0
# The fuel line drains this much for every unit of oxidizer drained.
FUEL_PER_OXIDIZER = 1.5


def build(**fuel_tank_overrides):
    fuel_tank_arguments = dict(
        fluid_name=FUEL,
        volume=FUEL_VOLUME,
        temperature=TEMPERATURE,
        initial_fluid_mass=FUEL_MASS,
    )
    fuel_tank_arguments.update(fuel_tank_overrides)
    return feed_systems_models.StackedTankPressureFedFeedSystem.from_oxidizer_and_fuel(
        oxidizer_tank=tank_models.Tank(
            fluid_name=OXIDIZER,
            volume=OXIDIZER_VOLUME,
            temperature=TEMPERATURE,
            initial_fluid_mass=OXIDIZER_MASS,
        ),
        fuel_tank=tank_models.Tank(**fuel_tank_arguments),
    )


def drain(feed_system, oxidizer_step, steps, fuel_per_oxidizer=FUEL_PER_OXIDIZER):
    """
    Drain both lines in equal explicit steps, as the engine state does.

    Returns:
        The fluid mass of every line and the oxidizer internal energy at the
        end of the drain.
    """
    oxidizer_tank = feed_system.lines["oxidizer"].tank
    masses = {"oxidizer": OXIDIZER_MASS, "fuel": FUEL_MASS}
    internal_energy = oxidizer_tank.initial_internal_energy
    drained = {"oxidizer": oxidizer_step, "fuel": fuel_per_oxidizer * oxidizer_step}
    for _ in range(steps):
        new_masses = {name: masses[name] - drained[name] for name in masses}
        volume = feed_system.get_tank_volumes(masses)["oxidizer"]
        new_volume = feed_system.get_tank_volumes(new_masses)["oxidizer"]
        internal_energy = biliquid_states.BiliquidEngineState._drain_internal_energy(
            tank=oxidizer_tank,
            internal_energy=internal_energy,
            fluid_mass=masses["oxidizer"],
            mass_drained=drained["oxidizer"],
            volume=volume,
            swept_volume=new_volume - volume,
            d_t=1.0,
        )
        masses = new_masses
    return masses, internal_energy


class TestIsentropicDrainOfAGrowingTank:
    """
    A slow adiabatic drain leaves the fluid behind on an isentrope.

    With dS = s_l dm for the fluid that stays and V(m) set by the piston,
    S(T, m, V) on the saturation curve gives an ODE in T alone, integrated
    from CoolProp saturation properties with no (D, U) flash.
    """

    FINAL_OXIDIZER_MASS = 3.0

    @staticmethod
    def entropy(temperature, fluid_mass, volume):
        liquid_density = CP.PropsSI("D", "T", temperature, "Q", 0, OXIDIZER)
        vapor_density = CP.PropsSI("D", "T", temperature, "Q", 1, OXIDIZER)
        liquid_mass = (fluid_mass - vapor_density * volume) / (
            1.0 - vapor_density / liquid_density
        )
        return liquid_mass * CP.PropsSI("S", "T", temperature, "Q", 0, OXIDIZER) + (
            fluid_mass - liquid_mass
        ) * CP.PropsSI("S", "T", temperature, "Q", 1, OXIDIZER)

    @classmethod
    def isentropic_temperature(cls):
        fuel_density = CP.PropsSI("D", "T", TEMPERATURE, "Q", 0, FUEL)

        def volume(fluid_mass):
            return (
                OXIDIZER_VOLUME
                + FUEL_PER_OXIDIZER * (OXIDIZER_MASS - fluid_mass) / fuel_density
            )

        def temperature_slope(fluid_mass, state):
            temperature = state[0]
            # With m the independent variable, dV/dm = -1.5 / rho_fuel and
            # S_T dT/dm = s_l - S_m - S_V dV/dm.
            v = volume(fluid_mass)
            d_volume = -FUEL_PER_OXIDIZER / fuel_density
            liquid_entropy = CP.PropsSI("S", "T", temperature, "Q", 0, OXIDIZER)
            mass_slope = (
                cls.entropy(temperature, fluid_mass + 1e-6, v)
                - cls.entropy(temperature, fluid_mass - 1e-6, v)
            ) / 2e-6
            volume_slope = (
                cls.entropy(temperature, fluid_mass, v + 1e-9)
                - cls.entropy(temperature, fluid_mass, v - 1e-9)
            ) / 2e-9
            temperature_slope = (
                cls.entropy(temperature + 1e-3, fluid_mass, v)
                - cls.entropy(temperature - 1e-3, fluid_mass, v)
            ) / 2e-3
            return [
                (liquid_entropy - mass_slope - volume_slope * d_volume)
                / temperature_slope
            ]

        solution = scipy.integrate.solve_ivp(
            temperature_slope,
            (OXIDIZER_MASS, cls.FINAL_OXIDIZER_MASS),
            [TEMPERATURE],
            rtol=1e-10,
            atol=1e-8,
        )
        return solution.y[0, -1], volume(cls.FINAL_OXIDIZER_MASS)

    def errors(self, oxidizer_step):
        feed_system = build()
        oxidizer_tank = feed_system.lines["oxidizer"].tank
        steps = round((OXIDIZER_MASS - self.FINAL_OXIDIZER_MASS) / oxidizer_step)
        masses, internal_energy = drain(feed_system, oxidizer_step, steps)
        volume = feed_system.get_tank_volumes(masses)["oxidizer"]
        reference_temperature, reference_volume = self.isentropic_temperature()
        assert volume == pytest.approx(reference_volume, rel=1e-12)

        temperature = oxidizer_tank.get_temperature(
            masses["oxidizer"], internal_energy, volume=volume
        )
        pressure = oxidizer_tank.get_pressure(
            masses["oxidizer"], internal_energy, volume=volume
        )
        reference_pressure = CP.PropsSI(
            "P", "T", reference_temperature, "Q", 0, OXIDIZER
        )
        return (
            reference_temperature,
            temperature - reference_temperature,
            pressure / reference_pressure - 1.0,
        )

    def test_the_drain_follows_the_isentrope_and_converges_with_the_step(self):
        reference_temperature, coarse_temperature, coarse_pressure = self.errors(0.02)
        _, fine_temperature, fine_pressure = self.errors(0.005)

        # 3 kg of fuel sweeps 3.8 L onto the 10 L tank: 14.8 K of cooling,
        # against 6.8 K for a fixed tank draining the same 2 kg of oxidizer.
        # Steps of 5 g land within 0.01 K and 2e-4 of the pressure.
        assert reference_temperature < TEMPERATURE - 14.0
        assert abs(fine_temperature) < 0.01
        assert abs(fine_pressure) < 2e-4
        # First order in the step: a quarter of the step, a quarter of the
        # error.
        assert abs(fine_temperature) == pytest.approx(
            abs(coarse_temperature) / 4.0, rel=0.2
        )
        assert abs(fine_pressure) == pytest.approx(abs(coarse_pressure) / 4.0, rel=0.2)


class TestPistonVolume:
    def test_the_volumes_add_up_to_the_same_total_over_a_drain(self):
        feed_system = build()
        start = feed_system.get_tank_volumes(
            {"oxidizer": OXIDIZER_MASS, "fuel": FUEL_MASS}
        )

        for fuel_mass in (3.0, 2.2, 1.1, 0.3, 0.0):
            volumes = feed_system.get_tank_volumes({"oxidizer": 4.0, "fuel": fuel_mass})
            assert sum(volumes.values()) == pytest.approx(
                sum(start.values()), rel=1e-14
            )

    def test_the_top_tank_starts_at_its_own_volume(self):
        feed_system = build()

        volumes = feed_system.get_tank_volumes(
            {"oxidizer": OXIDIZER_MASS, "fuel": FUEL_MASS}
        )

        assert volumes["oxidizer"] == OXIDIZER_VOLUME
        assert volumes["fuel"] == pytest.approx(
            FUEL_MASS / CP.PropsSI("D", "T", TEMPERATURE, "Q", 0, FUEL)
        )

    def test_without_fuel_flow_the_top_tank_drains_as_a_fixed_tank(self):
        """No piston travel, no work: exactly the fixed-volume energy balance."""
        feed_system = build()
        fixed_tank = tank_models.Tank(
            fluid_name=OXIDIZER,
            volume=OXIDIZER_VOLUME,
            temperature=TEMPERATURE,
            initial_fluid_mass=OXIDIZER_MASS,
        )
        step, steps = 0.05, 20

        masses, internal_energy = drain(feed_system, step, steps, fuel_per_oxidizer=0)

        fluid_mass = OXIDIZER_MASS
        fixed_internal_energy = fixed_tank.initial_internal_energy
        for _ in range(steps):
            fixed_internal_energy -= step * fixed_tank.get_outflow_specific_enthalpy(
                fluid_mass, fixed_internal_energy, mass_drained=step
            )
            fluid_mass -= step

        assert masses["fuel"] == FUEL_MASS
        assert internal_energy == fixed_internal_energy
        assert feed_system.get_inlet_pressures(
            {
                "oxidizer": feed_systems_models.LineState(
                    fluid_mass=masses["oxidizer"], internal_energy=internal_energy
                ),
                "fuel": feed_systems_models.LineState(fluid_mass=FUEL_MASS),
            }
        )["oxidizer"] == fixed_tank.get_pressure(fluid_mass, fixed_internal_energy)

    def test_the_piston_work_lowers_the_top_tank_pressure(self):
        feed_system = build()
        oxidizer_tank = feed_system.lines["oxidizer"].tank
        masses = {"oxidizer": OXIDIZER_MASS, "fuel": FUEL_MASS}
        new_masses = {"oxidizer": OXIDIZER_MASS - 0.1, "fuel": FUEL_MASS - 0.15}
        volume = feed_system.get_tank_volumes(masses)["oxidizer"]
        new_volume = feed_system.get_tank_volumes(new_masses)["oxidizer"]
        common = dict(
            tank=oxidizer_tank,
            internal_energy=oxidizer_tank.initial_internal_energy,
            fluid_mass=OXIDIZER_MASS,
            mass_drained=0.1,
            volume=volume,
            d_t=1e-3,
        )

        with_work = biliquid_states.BiliquidEngineState._drain_internal_energy(
            **common, swept_volume=new_volume - volume
        )
        without_piston = biliquid_states.BiliquidEngineState._drain_internal_energy(
            **common, swept_volume=0.0
        )

        stack_pressure = oxidizer_tank.get_pressure(
            OXIDIZER_MASS, oxidizer_tank.initial_internal_energy
        )
        assert without_piston - with_work == pytest.approx(
            stack_pressure * (new_volume - volume)
        )


class TestLowerLines:
    def test_a_line_below_the_piston_feeds_liquid_at_its_loading_temperature(self):
        feed_system = build()
        fuel_tank = feed_system.lines["fuel"].tank
        states = feed_system.get_initial_line_states()

        inlet = feed_system.get_inlet_states(states)["fuel"]

        assert states["fuel"].internal_energy is None
        assert inlet.temperature == TEMPERATURE
        assert inlet.density == pytest.approx(
            CP.PropsSI("D", "T", TEMPERATURE, "Q", 0, FUEL)
        )
        assert inlet.density == fuel_tank.saturated_liquid_density

    def test_the_top_line_still_starts_from_its_loaded_energy(self):
        feed_system = build()

        state = feed_system.get_initial_line_states()["oxidizer"]

        assert state.internal_energy == pytest.approx(
            feed_system.lines["oxidizer"].tank.initial_internal_energy
        )

    def test_rejects_a_lower_load_that_does_not_fit_its_tank(self):
        liquid_density = CP.PropsSI("D", "T", TEMPERATURE, "Q", 0, FUEL)

        with pytest.raises(ValueError, match="more than its tank volume"):
            build(
                initial_fluid_mass=1.02 * liquid_density * FUEL_VOLUME,
                overfill_tolerance=0.05,
            )

    def test_rejects_a_lower_line_that_would_boil_at_the_stack_pressure(self):
        with pytest.raises(ValueError, match="boils"):
            feed_systems_models.StackedTankPressureFedFeedSystem(
                lines=[
                    PropellantLineFactory.build(
                        name="oxidizer",
                        role="oxidizer",
                        tank=TankFactory.build(fluid_name="N2O", temperature=280.0),
                    ),
                    PropellantLineFactory.build(
                        name="fuel",
                        role="fuel",
                        tank=TankFactory.build(
                            fluid_name="N2O", temperature=300.0, initial_fluid_mass=6.0
                        ),
                    ),
                ],
                pressurizing_line="oxidizer",
            )
