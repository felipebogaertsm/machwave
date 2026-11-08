"""A tank running an energy balance cools as it drains.

An isothermal tank holds its saturation pressure flat for as long as any
liquid remains, which a self-pressurizing tank does not do: the fluid left
behind boils to refill the ullage and cools doing it. The energy balance
carries the tank's internal energy alongside its mass and takes out the
enthalpy of whatever leaves.
"""

import math

import CoolProp.CoolProp as CP
import pytest
import scipy.integrate

import machwave.models.feed_systems.tank as tank_models

FLUID = "N2O"
VOLUME = 0.01
TEMPERATURE = 293.0
FLUID_MASS = 5.0


def build(isothermal, **overrides):
    arguments = dict(
        fluid_name=FLUID,
        volume=VOLUME,
        temperature=TEMPERATURE,
        initial_fluid_mass=FLUID_MASS,
        isothermal=isothermal,
    )
    arguments.update(overrides)
    return tank_models.Tank(**arguments)


def drain(tank, mass_drained, fluid_mass=FLUID_MASS, internal_energy=None):
    """Take one lump of fluid out, with the enthalpy it carries."""
    if internal_energy is None:
        internal_energy = tank.initial_internal_energy
    outflow_enthalpy = tank.get_outflow_specific_enthalpy(
        fluid_mass, internal_energy, mass_drained=mass_drained
    )
    return (
        fluid_mass - mass_drained,
        internal_energy - mass_drained * outflow_enthalpy,
    )


class TestInitialInternalEnergy:
    def test_matches_the_loaded_state(self):
        tank = build(isothermal=False)

        assert tank.initial_internal_energy == pytest.approx(
            FLUID_MASS
            * CP.PropsSI("U", "T", TEMPERATURE, "D", FLUID_MASS / VOLUME, FLUID)
        )

    def test_an_empty_tank_carries_none(self):
        tank = build(isothermal=False, initial_fluid_mass=0.0)

        assert tank.initial_internal_energy == 0.0


class TestIsothermalTankIgnoresIt:
    def test_temperature_holds(self):
        tank = build(isothermal=True)

        assert tank.get_temperature(FLUID_MASS) == TEMPERATURE
        assert tank.get_temperature(FLUID_MASS, 1.0) == TEMPERATURE

    def test_pressure_holds(self):
        tank = build(isothermal=True)

        assert tank.get_pressure(FLUID_MASS, 1.0) == tank.get_pressure(FLUID_MASS)

    def test_it_needs_no_internal_energy(self):
        tank = build(isothermal=True)

        assert tank.get_pressure(FLUID_MASS) == pytest.approx(tank.saturation_pressure)


class TestEnergyBalanceTank:
    def test_the_loaded_state_agrees_with_the_isothermal_one(self):
        energy_balance = build(isothermal=False)
        isothermal = build(isothermal=True)
        internal_energy = energy_balance.initial_internal_energy

        assert energy_balance.get_temperature(
            FLUID_MASS, internal_energy
        ) == pytest.approx(TEMPERATURE)
        assert energy_balance.get_pressure(
            FLUID_MASS, internal_energy
        ) == pytest.approx(isothermal.get_pressure(FLUID_MASS), rel=1e-6)

    def test_draining_cools_the_tank(self):
        tank = build(isothermal=False)

        fluid_mass, internal_energy = drain(tank, 1.0)

        assert tank.get_temperature(fluid_mass, internal_energy) < TEMPERATURE

    def test_the_pressure_follows_the_temperature_down(self):
        tank = build(isothermal=False)

        fluid_mass, internal_energy = drain(tank, 1.0)

        assert tank.get_pressure(fluid_mass, internal_energy) < tank.get_pressure(
            FLUID_MASS, tank.initial_internal_energy
        )

    def test_the_decay_keeps_going(self):
        tank = build(isothermal=False)

        pressures = []
        fluid_mass, internal_energy = FLUID_MASS, tank.initial_internal_energy
        for _ in range(4):
            fluid_mass, internal_energy = drain(tank, 0.5, fluid_mass, internal_energy)
            pressures.append(tank.get_pressure(fluid_mass, internal_energy))

        assert pressures == sorted(pressures, reverse=True)

    def test_the_pressure_stays_on_the_saturation_curve(self):
        tank = build(isothermal=False)

        fluid_mass, internal_energy = drain(tank, 1.0)

        temperature = tank.get_temperature(fluid_mass, internal_energy)
        assert tank.get_pressure(fluid_mass, internal_energy) == pytest.approx(
            CP.PropsSI("P", "T", temperature, "Q", 0, FLUID), rel=1e-6
        )

    def test_the_density_follows_the_temperature(self):
        tank = build(isothermal=False)

        fluid_mass, internal_energy = drain(tank, 1.0)

        # A colder liquid is a denser one.
        assert tank.get_density(fluid_mass, internal_energy) > tank.get_density(
            FLUID_MASS, tank.initial_internal_energy
        )

    def test_it_asks_for_the_internal_energy(self):
        tank = build(isothermal=False)

        with pytest.raises(ValueError, match="initial_internal_energy"):
            tank.get_pressure(FLUID_MASS)

    def test_a_state_off_the_chart_says_so(self):
        tank = build(isothermal=False)

        with pytest.raises(ValueError, match="outside the range CoolProp"):
            tank.get_pressure(FLUID_MASS, -1e12)

    def test_a_mid_burn_state_the_flash_gets_wrong_stays_on_the_dome(self):
        # CoolProp 6.8.0's (D, U) flash puts this N2O state at 270.37 K and
        # 1.45 MPa, single-phase. The saturated mix at the reference
        # temperature and quality gives back its density and internal energy.
        density = 454.50072100174214
        specific_internal_energy = 228590.2487156092
        reference_temperature = 291.03099264302705
        reference_quality = 0.17165274259158367
        assert CP.PropsSI(
            "D", "T", reference_temperature, "Q", reference_quality, FLUID
        ) == pytest.approx(density, rel=1e-12)
        tank = build(isothermal=False)
        fluid_mass = density * VOLUME
        internal_energy = specific_internal_energy * fluid_mass

        # The dome solve stops at a 1e-10 K bracket; 1e-6 K leaves room for
        # the round-off in the reference state, and moves the saturation
        # pressure by about 1e-8 relative.
        assert tank.get_temperature(fluid_mass, internal_energy) == pytest.approx(
            reference_temperature, abs=1e-6
        )
        assert tank.get_pressure(fluid_mass, internal_energy) == pytest.approx(
            CP.PropsSI("P", "T", reference_temperature, "Q", 0, FLUID), rel=1e-7
        )
        assert tank.is_delivering_liquid(fluid_mass, internal_energy)


class TestOutflowEnthalpy:
    def test_liquid_leaves_at_the_saturated_liquid_enthalpy(self):
        tank = build(isothermal=False)
        internal_energy = tank.initial_internal_energy

        temperature = tank.get_temperature(FLUID_MASS, internal_energy)
        assert tank.get_outflow_specific_enthalpy(
            FLUID_MASS, internal_energy, mass_drained=1.0
        ) == pytest.approx(CP.PropsSI("H", "T", temperature, "Q", 0, FLUID))

    def test_a_draw_past_the_liquid_takes_saturated_vapor_for_the_rest(self):
        tank = build(isothermal=True)
        liquid_mass = 1e-3
        fluid_mass = tank.saturated_vapor_density * VOLUME + liquid_mass * (
            1.0 - tank.saturated_vapor_density / tank.saturated_liquid_density
        )

        outflow_enthalpy = tank.get_outflow_specific_enthalpy(
            fluid_mass, mass_drained=4 * liquid_mass
        )

        assert outflow_enthalpy == pytest.approx(
            0.25 * CP.PropsSI("H", "T", TEMPERATURE, "Q", 0, FLUID)
            + 0.75 * CP.PropsSI("H", "T", TEMPERATURE, "Q", 1, FLUID)
        )

    def test_a_tank_back_in_the_dome_with_a_trace_of_liquid_keeps_cooling(self):
        tank = build(isothermal=False)
        temperature = 260.0
        vapor_density = CP.PropsSI("D", "T", temperature, "Q", 1, FLUID)
        fluid_mass = 1.0001 * vapor_density * VOLUME
        internal_energy = fluid_mass * CP.PropsSI(
            "U", "T", temperature, "D", fluid_mass / VOLUME, FLUID
        )

        drained_mass, drained_energy = drain(
            tank, 0.5 * fluid_mass, fluid_mass, internal_energy
        )

        assert drained_energy / drained_mass < internal_energy / fluid_mass

    def test_vapor_leaves_at_the_bulk_state(self):
        tank = build(isothermal=True)
        # Below the saturated vapor fill, so no liquid is left to draw on.
        vapor_mass = 0.5 * tank.saturated_vapor_density * VOLUME

        assert tank.get_outflow_specific_enthalpy(
            vapor_mass, mass_drained=0.1 * vapor_mass
        ) == pytest.approx(
            CP.PropsSI("H", "T", TEMPERATURE, "D", vapor_mass / VOLUME, FLUID)
        )

    def test_an_empty_tank_carries_nothing_out(self):
        tank = build(isothermal=False)

        assert tank.get_outflow_specific_enthalpy(0.0, 0.0, mass_drained=0.0) == 0.0


class TestAgainstTheIsentropicDrain:
    """
    A slow adiabatic drain of saturated liquid is reversible: the fluid left
    behind and the parcel on its way out stay in equilibrium as they expand,
    so the tank's entropy falls by the liquid entropy of what leaves,
    $dS = s_l \\, dm$. Integrating that on the saturation curve, with no
    internal energy and no (D, U) flash, is a reference the energy balance
    does not share any code path with.
    """

    FINAL_FLUID_MASS = 1.6  # Above the 1.57 kg of saturated vapor at 293 K.
    MASS_STEPS = (2e-2, 1e-2, 5e-3)  # Each half the last.

    @staticmethod
    def saturation(temperature):
        return [
            CP.PropsSI(key, "T", temperature, "Q", quality, FLUID)
            for key, quality in (("D", 0), ("D", 1), ("S", 0), ("S", 1))
        ]

    @classmethod
    def entropy(cls, temperature, fluid_mass):
        liquid_density, vapor_density, liquid_entropy, vapor_entropy = cls.saturation(
            temperature
        )
        latent_entropy_per_volume = (vapor_entropy - liquid_entropy) / (
            1.0 / vapor_density - 1.0 / liquid_density
        )
        return (
            fluid_mass * liquid_entropy
            + (VOLUME - fluid_mass / liquid_density) * latent_entropy_per_volume
        )

    @classmethod
    def isentropic_temperature(cls):
        def temperature_slope(fluid_mass, state):
            temperature = state[0]
            liquid_density, vapor_density, liquid_entropy, vapor_entropy = (
                cls.saturation(temperature)
            )
            entropy_slope = (
                cls.entropy(temperature + 1e-3, fluid_mass)
                - cls.entropy(temperature - 1e-3, fluid_mass)
            ) / 2e-3
            # dS/dT dT = (s_l - dS/dm at fixed T) dm, and the bracket is
            # v_l (s_v - s_l) / (v_v - v_l).
            return [
                (vapor_entropy - liquid_entropy)
                / liquid_density
                / (1.0 / vapor_density - 1.0 / liquid_density)
                / entropy_slope
            ]

        solution = scipy.integrate.solve_ivp(
            temperature_slope,
            (FLUID_MASS, cls.FINAL_FLUID_MASS),
            [TEMPERATURE],
            rtol=1e-10,
            atol=1e-8,
        )
        return solution.y[0, -1]

    @classmethod
    def drain_to_the_final_mass(cls, mass_step):
        tank = build(isothermal=False)
        fluid_mass, internal_energy = FLUID_MASS, tank.initial_internal_energy
        steps = round((FLUID_MASS - cls.FINAL_FLUID_MASS) / mass_step)
        for _ in range(steps):
            fluid_mass, internal_energy = drain(
                tank, mass_step, fluid_mass, internal_energy
            )
        return tank, fluid_mass, internal_energy

    def test_the_drain_follows_the_isentrope(self):
        tank, fluid_mass, internal_energy = self.drain_to_the_final_mass(
            self.MASS_STEPS[-1]
        )

        reference_temperature = self.isentropic_temperature()

        # About 12 K and 1.3 MPa of decay; explicit steps of 5 g land within
        # 0.01 K and 2e-4 of the pressure.
        assert reference_temperature < TEMPERATURE - 12.0
        assert tank.get_temperature(fluid_mass, internal_energy) == pytest.approx(
            reference_temperature, abs=0.05
        )
        assert tank.get_pressure(fluid_mass, internal_energy) == pytest.approx(
            CP.PropsSI("P", "T", reference_temperature, "Q", 0, FLUID), rel=5e-4
        )

    def test_the_explicit_drain_is_first_order(self):
        reference_temperature = self.isentropic_temperature()
        errors = []
        for mass_step in self.MASS_STEPS:
            tank, fluid_mass, internal_energy = self.drain_to_the_final_mass(mass_step)
            errors.append(
                tank.get_temperature(fluid_mass, internal_energy)
                - reference_temperature
            )

        observed_orders = [
            math.log2(coarse / fine) for coarse, fine in zip(errors, errors[1:])
        ]

        # Measured 1.0016 and 1.0008; the reference is solved to rtol 1e-10,
        # far below the 7 mK error left at the finest step.
        assert observed_orders == pytest.approx([1.0, 1.0], abs=0.05)
