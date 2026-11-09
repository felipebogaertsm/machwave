"""The fluid at the top of a stacked tank fills the volume the piston sweeps."""

import math

import CoolProp.CoolProp as CP
import pytest
import scipy.integrate

import machwave.models.feed_systems as feed_systems_models
import machwave.models.feed_systems.tank as tank_models
import machwave.simulation.biliquid.states as biliquid_states

OXIDIZER = "N2O"
FUEL = "Ethanol"
TEMPERATURE = 293.0
OXIDIZER_VOLUME = 0.01
OXIDIZER_MASS = 5.0
FUEL_VOLUME = 0.004
FUEL_MASS = 3.0
FUEL_TO_OXIDIZER_DRAIN_RATIO = 1.5


def build(**fuel_tank_overrides):
    fuel_tank_arguments = dict(
        fluid_name=FUEL,
        volume=FUEL_VOLUME,
        temperature=TEMPERATURE,
        initial_fluid_mass=FUEL_MASS,
        isothermal=True,
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


def drain(
    feed_system,
    oxidizer_mass_per_step,
    step_count,
    fuel_to_oxidizer_drain_ratio=FUEL_TO_OXIDIZER_DRAIN_RATIO,
):
    """
    Drain both lines in equal explicit steps, as the engine state does.

    Returns:
        The fluid mass of every line and the oxidizer internal energy at the
        end of the drain.
    """
    oxidizer_tank = feed_system.lines["oxidizer"].tank
    masses = {"oxidizer": OXIDIZER_MASS, "fuel": FUEL_MASS}
    internal_energy = oxidizer_tank.initial_internal_energy
    drained = {
        "oxidizer": oxidizer_mass_per_step,
        "fuel": fuel_to_oxidizer_drain_ratio * oxidizer_mass_per_step,
    }
    for _ in range(step_count):
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
        )
        masses = new_masses
    return masses, internal_energy


class TestIsentropicDrainOfAGrowingTank:
    """A slow adiabatic drain leaves the fluid behind on an isentrope."""

    FINAL_OXIDIZER_MASS = 3.0
    OXIDIZER_MASSES_PER_STEP = (2e-2, 1e-2, 5e-3)  # each half the last

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
                + FUEL_TO_OXIDIZER_DRAIN_RATIO
                * (OXIDIZER_MASS - fluid_mass)
                / fuel_density
            )

        def temperature_slope(fluid_mass, state):
            temperature = state[0]
            # the fluid left behind loses only the entropy of the liquid drained
            fluid_volume = volume(fluid_mass)
            volume_per_mass = -FUEL_TO_OXIDIZER_DRAIN_RATIO / fuel_density
            liquid_entropy = CP.PropsSI("S", "T", temperature, "Q", 0, OXIDIZER)
            entropy_per_mass = (
                cls.entropy(temperature, fluid_mass + 1e-6, fluid_volume)
                - cls.entropy(temperature, fluid_mass - 1e-6, fluid_volume)
            ) / 2e-6
            entropy_per_volume = (
                cls.entropy(temperature, fluid_mass, fluid_volume + 1e-9)
                - cls.entropy(temperature, fluid_mass, fluid_volume - 1e-9)
            ) / 2e-9
            entropy_per_temperature = (
                cls.entropy(temperature + 1e-3, fluid_mass, fluid_volume)
                - cls.entropy(temperature - 1e-3, fluid_mass, fluid_volume)
            ) / 2e-3
            return [
                (
                    liquid_entropy
                    - entropy_per_mass
                    - entropy_per_volume * volume_per_mass
                )
                / entropy_per_temperature
            ]

        solution = scipy.integrate.solve_ivp(
            temperature_slope,
            (OXIDIZER_MASS, cls.FINAL_OXIDIZER_MASS),
            [TEMPERATURE],
            rtol=1e-10,
            atol=1e-8,
        )
        return solution.y[0, -1], volume(cls.FINAL_OXIDIZER_MASS)

    def errors(self, oxidizer_mass_per_step):
        feed_system = build()
        oxidizer_tank = feed_system.lines["oxidizer"].tank
        step_count = round(
            (OXIDIZER_MASS - self.FINAL_OXIDIZER_MASS) / oxidizer_mass_per_step
        )
        masses, internal_energy = drain(feed_system, oxidizer_mass_per_step, step_count)
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

    def test_the_drain_follows_the_isentrope(self):
        reference_temperature, temperature_error, pressure_error = self.errors(
            self.OXIDIZER_MASSES_PER_STEP[-1]
        )

        # piston travel cools it 14.8 K, against 6.8 K for a fixed tank
        assert reference_temperature < TEMPERATURE - 14.0
        assert abs(temperature_error) < 0.01
        assert abs(pressure_error) < 2e-4

    def test_the_explicit_drain_is_first_order(self):
        temperature_errors = [
            self.errors(mass_per_step)[1]
            for mass_per_step in self.OXIDIZER_MASSES_PER_STEP
        ]

        observed_orders = [
            math.log2(coarse / fine)
            for coarse, fine in zip(temperature_errors, temperature_errors[1:])
        ]

        # measured 1.0018 and 1.0009
        assert observed_orders == pytest.approx([1.0, 1.0], abs=0.05)


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
        feed_system = build()
        fixed_tank = tank_models.Tank(
            fluid_name=OXIDIZER,
            volume=OXIDIZER_VOLUME,
            temperature=TEMPERATURE,
            initial_fluid_mass=OXIDIZER_MASS,
        )
        mass_per_step, step_count = 0.05, 20

        masses, internal_energy = drain(
            feed_system, mass_per_step, step_count, fuel_to_oxidizer_drain_ratio=0
        )

        fluid_mass = OXIDIZER_MASS
        fixed_internal_energy = fixed_tank.initial_internal_energy
        for _ in range(step_count):
            fixed_internal_energy -= (
                mass_per_step
                * fixed_tank.get_outflow_specific_enthalpy(
                    fluid_mass, fixed_internal_energy, mass_drained=mass_per_step
                )
            )
            fluid_mass -= mass_per_step

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
        states = {name: line.initial_state for name, line in feed_system.lines.items()}

        inlet = feed_system.get_inlet_states(states)["fuel"]

        assert states["fuel"].internal_energy is None
        assert inlet.temperature == TEMPERATURE
        assert inlet.density == pytest.approx(
            CP.PropsSI("D", "T", TEMPERATURE, "Q", 0, FUEL)
        )
        assert inlet.density == fuel_tank.saturated_liquid_density
