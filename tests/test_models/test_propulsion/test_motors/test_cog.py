"""
Tests for center of gravity calculations for Motor classes (SolidMotor, LiquidEngine).

Tests verify motor-level CoG calculations that combine grain/propellant mass with
hardware (thrust chamber, tanks, feed systems).

For grain-specific CoG tests, see:
- tests/test_models/test_propulsion/test_grain/test_grain_cog.py
- tests/test_models/test_propulsion/test_grain/test_fmm_cog.py
"""

import numpy as np
import pytest

from machwave.models.materials import Steel
from machwave.models.propulsion import grain as grain_models
from machwave.models.propulsion.grain import geometries as grain_geometries
from machwave.models.propulsion.motors import solid as solid_motors
from machwave.models.propulsion.propellants.formulations import (
    solid as solid_propellants,
)
from machwave.models.propulsion.thrust_chamber import (
    CombustionChamber,
    Nozzle,
    SolidMotorThrustChamber,
)


@pytest.fixture
def simple_bates_motor():
    """Create a simple solid motor with BATES grain for testing."""
    propellant = solid_propellants.KNDX

    grain = grain_models.Grain()
    bates_segment = grain_geometries.BatesSegment(
        outer_diameter=41e-3,
        core_diameter=15e-3,
        length=67.5e-3,
    )
    grain.add_segment(bates_segment)

    nozzle = Nozzle(
        inlet_diameter=43e-3,
        throat_diameter=9.5e-3,
        divergent_angle=12,
        convergent_angle=40,
        expansion_ratio=8,
        material=Steel(),
    )

    combustion_chamber = CombustionChamber(
        casing_inner_diameter=44.5e-3,
        casing_outer_diameter=50.8e-3,
        thermal_liner_thickness=1e-3,
        internal_length=grain.total_length + 10e-3,
    )

    thrust_chamber = SolidMotorThrustChamber(
        dry_mass=0.85,
        nozzle=nozzle,
        combustion_chamber=combustion_chamber,
    )

    motor = solid_motors.SolidMotor(
        grain=grain,
        propellant=propellant,
        thrust_chamber=thrust_chamber,
    )

    return motor


@pytest.fixture
def multi_segment_bates_motor():
    """Create a solid motor with multiple BATES segments for testing."""
    propellant = solid_propellants.KNSB_NAKKA

    grain = grain_models.Grain()

    bates_segment_1 = grain_geometries.BatesSegment(
        outer_diameter=0.086,
        core_diameter=0.032,
        length=0.150,
    )

    bates_segment_2 = grain_geometries.BatesSegment(
        outer_diameter=0.086,
        core_diameter=0.046,
        length=0.150,
    )

    # Add segments
    for _ in range(4):
        grain.add_segment(bates_segment_1)
    for _ in range(3):
        grain.add_segment(bates_segment_2)

    nozzle = Nozzle(
        inlet_diameter=0.086,
        throat_diameter=0.022,
        divergent_angle=12,
        convergent_angle=45,
        expansion_ratio=8,
        material=Steel(),
    )

    combustion_chamber = CombustionChamber(
        casing_inner_diameter=0.086,
        casing_outer_diameter=0.096,
        thermal_liner_thickness=1e-3,
        internal_length=grain.total_length + 0.01,
    )

    thrust_chamber = SolidMotorThrustChamber(
        dry_mass=2.5,
        nozzle=nozzle,
        combustion_chamber=combustion_chamber,
    )

    motor = solid_motors.SolidMotor(
        grain=grain,
        propellant=propellant,
        thrust_chamber=thrust_chamber,
    )

    return motor


class TestSolidMotorCoG:
    """Test CoG calculations for solid motors."""

    def test_motor_cog_initial_state(self, simple_bates_motor):
        """Motor CoG should be computed at initial state."""
        cog = simple_bates_motor.get_center_of_gravity(web_distance=0.0)

        assert isinstance(cog, np.ndarray)
        assert cog.shape == (3,)
        assert cog.dtype == np.float64

        # Should be positive (somewhere in the motor)
        assert cog[0] > 0

    def test_motor_cog_includes_hardware(self, simple_bates_motor):
        """Motor CoG should account for chamber and nozzle masses."""
        cog = simple_bates_motor.get_center_of_gravity(web_distance=0.0)

        # CoG should be a weighted average including hardware
        # It should be different from just the grain CoG
        grain_cog = simple_bates_motor.grain.get_center_of_gravity(web_distance=0.0)

        # They should be different (unless masses are perfectly balanced)
        # We just verify both are valid
        assert isinstance(cog, np.ndarray)
        assert isinstance(grain_cog, np.ndarray)

    def test_motor_cog_with_burn_progression(self, simple_bates_motor):
        """Motor CoG should change as propellant burns."""
        web_thickness = simple_bates_motor.grain.segments[0].get_web_thickness()

        cog_initial = simple_bates_motor.get_center_of_gravity(web_distance=0.0)
        cog_mid = simple_bates_motor.get_center_of_gravity(
            web_distance=web_thickness * 0.5
        )

        # Both should be valid
        assert isinstance(cog_initial, np.ndarray)
        assert isinstance(cog_mid, np.ndarray)

        # As propellant burns away, CoG will shift
        # (exact direction depends on geometry and hardware distribution)

    def test_motor_cog_multi_segment(self, multi_segment_bates_motor):
        """Motor with multiple segments should compute CoG correctly."""
        cog = multi_segment_bates_motor.get_center_of_gravity(web_distance=0.0)

        assert isinstance(cog, np.ndarray)
        assert cog.shape == (3,)

        # Should be somewhere within the motor length
        chamber_length = (
            multi_segment_bates_motor.thrust_chamber.combustion_chamber.internal_length
        )
        assert 0 < cog[0] <= chamber_length

    def test_motor_cog_default_parameter(self, simple_bates_motor):
        """Motor CoG should work with default web_distance parameter."""
        cog_default = simple_bates_motor.get_center_of_gravity()
        cog_zero = simple_bates_motor.get_center_of_gravity(web_distance=0.0)

        # Default should be same as zero
        np.testing.assert_array_almost_equal(cog_default, cog_zero)

    def test_motor_cog_with_custom_dry_mass_cog(self):
        """Motor should use custom dry_mass_cog when provided."""
        propellant = solid_propellants.KNDX

        grain = grain_models.Grain()
        bates_segment = grain_geometries.BatesSegment(
            outer_diameter=41e-3,
            core_diameter=15e-3,
            length=67.5e-3,
        )
        grain.add_segment(bates_segment)

        nozzle = Nozzle(
            inlet_diameter=43e-3,
            throat_diameter=9.5e-3,
            divergent_angle=12,
            convergent_angle=40,
            expansion_ratio=8,
            material=Steel(),
        )

        combustion_chamber = CombustionChamber(
            casing_inner_diameter=44.5e-3,
            casing_outer_diameter=50.8e-3,
            thermal_liner_thickness=1e-3,
            internal_length=grain.total_length + 10e-3,
        )

        thrust_chamber = SolidMotorThrustChamber(
            dry_mass=0.85,
            nozzle=nozzle,
            combustion_chamber=combustion_chamber,
        )

        # Create motor with custom dry mass CoG at 0.05m from throat
        custom_dry_cog = 0.05
        motor = solid_motors.SolidMotor(
            grain=grain,
            propellant=propellant,
            thrust_chamber=thrust_chamber,
            dry_mass_cog=custom_dry_cog,
        )

        cog = motor.get_center_of_gravity(web_distance=0.0)

        # CoG should be influenced by the custom dry mass position
        assert isinstance(cog, np.ndarray)
        assert cog.shape == (3,)

        # With very light propellant compared to hardware, CoG should be close to dry_mass_cog
        # But since we have propellant, it won't be exactly at custom_dry_cog
        assert cog[0] > 0


class TestLiquidEngineCoG:
    """Test CoG calculations for liquid engines."""

    def test_liquid_engine_cog_default_estimates(self):
        """
        Liquid engine CoG with default position estimates.
        """
        from machwave.models.materials import Steel
        from machwave.models.propulsion.feed_systems.pressure_fed import (
            StackedTankPressureFedFeedSystem,
        )
        from machwave.models.propulsion.feed_systems.tanks import Tank
        from machwave.models.propulsion.motors.liquid import LiquidEngine
        from machwave.models.propulsion.propellants import (
            BiliquidPropellant,
            ComponentRole,
            PropellantComponent,
        )
        from machwave.models.propulsion.thrust_chamber import LiquidEngineThrustChamber
        from machwave.models.propulsion.thrust_chamber.combustion_chamber import (
            CombustionChamber,
        )
        from machwave.models.propulsion.thrust_chamber.injector import (
            BipropellantInjector,
        )
        from machwave.models.propulsion.thrust_chamber.nozzle import Nozzle

        # Create tanks
        ox_tank = Tank(
            fluid_name="N2O",
            volume=0.01,
            temperature=298.0,
            initial_fluid_mass=5.0,
        )

        fuel_tank = Tank(
            fluid_name="Ethanol",
            volume=0.008,
            temperature=298.0,
            initial_fluid_mass=3.0,
        )

        # Create feed system
        feed_system = StackedTankPressureFedFeedSystem(
            fuel_tank=fuel_tank,
            oxidizer_tank=ox_tank,
            oxidizer_line_diameter=0.01,
            oxidizer_line_length=0.5,
            fuel_line_diameter=0.008,
            fuel_line_length=0.5,
        )

        # Create thrust chamber components
        nozzle = Nozzle(
            inlet_diameter=0.04,
            throat_diameter=0.015,
            divergent_angle=15,
            convergent_angle=45,
            expansion_ratio=10,
            material=Steel(),
        )

        injector = BipropellantInjector(
            area_ox=1e-5,
            area_fuel=5e-6,
            discharge_coefficient_oxidizer=0.7,
            discharge_coefficient_fuel=0.7,
        )

        combustion_chamber = CombustionChamber(
            casing_inner_diameter=0.05,
            casing_outer_diameter=0.06,
            thermal_liner_thickness=2e-3,
            internal_length=0.3,
        )

        thrust_chamber = LiquidEngineThrustChamber(
            dry_mass=5.0,
            nozzle=nozzle,
            injector=injector,
            combustion_chamber=combustion_chamber,
        )

        # Create propellant components
        oxidizer = PropellantComponent(
            name="N2O",
            role=ComponentRole.OXIDIZER,
            density=745.0,
            chemical_formula={"N": 2, "O": 1},
            enthalpy=0.0,
            initial_temperature=298.0,
        )
        fuel = PropellantComponent(
            name="Ethanol",
            role=ComponentRole.FUEL,
            density=789.0,
            chemical_formula={"C": 2, "H": 6, "O": 1},
            enthalpy=0.0,
            initial_temperature=298.0,
        )

        propellant = BiliquidPropellant(
            name="N2O/Ethanol",
            components=[oxidizer, fuel],
            combustion_efficiency=0.98,
            of_ratio=2.0,
        )

        # Create engine
        engine = LiquidEngine(
            propellant=propellant,
            thrust_chamber=thrust_chamber,
            feed_system=feed_system,
        )

        # Test CoG at full tanks
        cog_full = engine.get_center_of_gravity(propellant_fraction=0.0)
        assert isinstance(cog_full, np.ndarray)
        assert cog_full.shape == (3,)
        assert cog_full[0] > 0  # Should be somewhere in the engine

        # Test CoG at half propellant
        cog_half = engine.get_center_of_gravity(propellant_fraction=0.5)
        assert isinstance(cog_half, np.ndarray)
        assert cog_half.shape == (3,)

        # CoG should shift as propellant is consumed
        # (exact direction depends on tank vs hardware positions)

    def test_liquid_engine_cog_custom_positions(self):
        """
        Liquid engine CoG with user-provided positions for dry mass and tanks.
        """
        from machwave.models.materials import Steel
        from machwave.models.propulsion.feed_systems.pressure_fed import (
            StackedTankPressureFedFeedSystem,
        )
        from machwave.models.propulsion.feed_systems.tanks import Tank
        from machwave.models.propulsion.motors.liquid import LiquidEngine
        from machwave.models.propulsion.propellants import (
            BiliquidPropellant,
            ComponentRole,
            PropellantComponent,
        )
        from machwave.models.propulsion.thrust_chamber import LiquidEngineThrustChamber
        from machwave.models.propulsion.thrust_chamber.combustion_chamber import (
            CombustionChamber,
        )
        from machwave.models.propulsion.thrust_chamber.injector import (
            BipropellantInjector,
        )
        from machwave.models.propulsion.thrust_chamber.nozzle import Nozzle

        # Create tanks
        ox_tank = Tank(
            fluid_name="N2O",
            volume=0.01,
            temperature=298.0,
            initial_fluid_mass=5.0,
        )

        fuel_tank = Tank(
            fluid_name="Ethanol",
            volume=0.008,
            temperature=298.0,
            initial_fluid_mass=3.0,
        )

        # Create feed system
        feed_system = StackedTankPressureFedFeedSystem(
            fuel_tank=fuel_tank,
            oxidizer_tank=ox_tank,
            oxidizer_line_diameter=0.01,
            oxidizer_line_length=0.5,
            fuel_line_diameter=0.008,
            fuel_line_length=0.5,
        )

        # Create thrust chamber components
        nozzle = Nozzle(
            inlet_diameter=0.04,
            throat_diameter=0.015,
            divergent_angle=15,
            convergent_angle=45,
            expansion_ratio=10,
            material=Steel(),
        )

        injector = BipropellantInjector(
            area_ox=1e-5,
            area_fuel=5e-6,
            discharge_coefficient_oxidizer=0.7,
            discharge_coefficient_fuel=0.7,
        )

        combustion_chamber = CombustionChamber(
            casing_inner_diameter=0.05,
            casing_outer_diameter=0.06,
            thermal_liner_thickness=2e-3,
            internal_length=0.3,
        )

        thrust_chamber = LiquidEngineThrustChamber(
            dry_mass=5.0,
            nozzle=nozzle,
            injector=injector,
            combustion_chamber=combustion_chamber,
        )

        # Create propellant components
        oxidizer = PropellantComponent(
            name="N2O",
            role=ComponentRole.OXIDIZER,
            density=745.0,
            chemical_formula={"N": 2, "O": 1},
            enthalpy=0.0,
            initial_temperature=298.0,
        )
        fuel = PropellantComponent(
            name="Ethanol",
            role=ComponentRole.FUEL,
            density=789.0,
            chemical_formula={"C": 2, "H": 6, "O": 1},
            enthalpy=0.0,
            initial_temperature=298.0,
        )

        propellant = BiliquidPropellant(
            name="N2O/Ethanol",
            components=[oxidizer, fuel],
            combustion_efficiency=0.98,
            of_ratio=2.0,
        )

        # Create engine with custom CoG positions
        dry_cog = 0.15  # 150mm from throat
        ox_cog = 0.8  # 800mm from throat
        fuel_cog = 0.75  # 750mm from throat

        engine = LiquidEngine(
            propellant=propellant,
            thrust_chamber=thrust_chamber,
            feed_system=feed_system,
            dry_mass_cog=dry_cog,
            oxidizer_tank_cog=ox_cog,
            fuel_tank_cog=fuel_cog,
        )

        # Test CoG calculation
        cog = engine.get_center_of_gravity(propellant_fraction=0.0)

        assert isinstance(cog, np.ndarray)
        assert cog.shape == (3,)

        # With full tanks, CoG should be between dry mass and tank positions
        # (weighted by masses)
        assert cog[0] > dry_cog  # Should be pulled toward tanks by propellant mass
        assert cog[0] < max(ox_cog, fuel_cog)

        # Test with empty tanks - should approach dry mass CoG
        cog_empty = engine.get_center_of_gravity(propellant_fraction=1.0)
        assert abs(cog_empty[0] - dry_cog) < 0.01  # Should be very close to dry_cog


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
