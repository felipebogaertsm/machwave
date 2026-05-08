"""Motor-level CoG tests; see test_grain/ for grain-only CoG tests."""

import numpy as np
import pytest

from machwave.models import grain as grain_models
from machwave.models.propellants.formulations import (
    solid as solid_propellants,
)

from tests.factories import (
    BatesSegmentFactory,
    CombustionChamberFactory,
    LiquidEngineFactory,
    LiquidEngineThrustChamberFactory,
    NozzleFactory,
    SolidMotorFactory,
    SolidMotorThrustChamberFactory,
)


@pytest.fixture
def simple_bates_motor():
    grain = grain_models.Grain()
    grain.add_segment(
        BatesSegmentFactory.build(
            outer_diameter=41e-3,
            core_diameter=15e-3,
            length=67.5e-3,
        )
    )
    nozzle = NozzleFactory.build(
        inlet_diameter=43e-3,
        throat_diameter=9.5e-3,
        divergent_angle=12,
        convergent_angle=40,
        expansion_ratio=8,
    )
    combustion_chamber = CombustionChamberFactory.build(
        casing_inner_diameter=44.5e-3,
        casing_outer_diameter=50.8e-3,
        thermal_liner_thickness=1e-3,
        internal_length=grain.total_length + 10e-3,
    )
    thrust_chamber = SolidMotorThrustChamberFactory.build(
        nozzle=nozzle,
        combustion_chamber=combustion_chamber,
        center_of_gravity_coordinate=(0.04, 0.0, 0.0),
    )
    return SolidMotorFactory.build(
        grain=grain,
        propellant=solid_propellants.KNDX,
        thrust_chamber=thrust_chamber,
    )


@pytest.fixture
def multi_segment_bates_motor():
    grain = grain_models.Grain()
    for _ in range(4):
        grain.add_segment(
            BatesSegmentFactory.build(
                outer_diameter=0.086, core_diameter=0.032, length=0.150
            )
        )
    for _ in range(3):
        grain.add_segment(
            BatesSegmentFactory.build(
                outer_diameter=0.086, core_diameter=0.046, length=0.150
            )
        )

    nozzle = NozzleFactory.build(
        inlet_diameter=0.086,
        throat_diameter=0.022,
        divergent_angle=12,
        convergent_angle=45,
        expansion_ratio=8,
    )
    combustion_chamber = CombustionChamberFactory.build(
        casing_inner_diameter=0.086,
        casing_outer_diameter=0.096,
        thermal_liner_thickness=1e-3,
        internal_length=grain.total_length + 0.01,
    )
    thrust_chamber = SolidMotorThrustChamberFactory.build(
        nozzle=nozzle,
        combustion_chamber=combustion_chamber,
        dry_mass=2.5,
        center_of_gravity_coordinate=(0.5, 0.0, 0.0),
    )
    return SolidMotorFactory.build(
        grain=grain,
        propellant=solid_propellants.KNSB_NAKKA,
        thrust_chamber=thrust_chamber,
    )


class TestSolidMotorCoG:
    def test_motor_cog_initial_state(self, simple_bates_motor):
        cog = simple_bates_motor.get_center_of_gravity(web_distance=0.0)

        assert isinstance(cog, np.ndarray)
        assert cog.shape == (3,)
        assert cog.dtype == np.float64
        assert cog[0] > 0

    def test_motor_cog_includes_hardware(self, simple_bates_motor):
        cog = simple_bates_motor.get_center_of_gravity(web_distance=0.0)
        grain_cog = simple_bates_motor.grain.get_center_of_gravity(web_distance=0.0)

        assert isinstance(cog, np.ndarray)
        assert isinstance(grain_cog, np.ndarray)

    def test_motor_cog_with_burn_progression(self, simple_bates_motor):
        web_thickness = simple_bates_motor.grain.segments[0].get_web_thickness()

        cog_initial = simple_bates_motor.get_center_of_gravity(web_distance=0.0)
        cog_mid = simple_bates_motor.get_center_of_gravity(
            web_distance=web_thickness * 0.5
        )

        assert isinstance(cog_initial, np.ndarray)
        assert isinstance(cog_mid, np.ndarray)

    def test_motor_cog_multi_segment(self, multi_segment_bates_motor):
        cog = multi_segment_bates_motor.get_center_of_gravity(web_distance=0.0)

        assert isinstance(cog, np.ndarray)
        assert cog.shape == (3,)

        chamber_length = (
            multi_segment_bates_motor.thrust_chamber.combustion_chamber.internal_length
        )
        assert 0 < cog[0] <= chamber_length

    def test_motor_cog_default_parameter(self, simple_bates_motor):
        cog_default = simple_bates_motor.get_center_of_gravity()
        cog_zero = simple_bates_motor.get_center_of_gravity(web_distance=0.0)

        np.testing.assert_array_almost_equal(cog_default, cog_zero)

    def test_motor_cog_with_custom_dry_mass_cog(self):
        grain = grain_models.Grain()
        grain.add_segment(
            BatesSegmentFactory.build(
                outer_diameter=41e-3,
                core_diameter=15e-3,
                length=67.5e-3,
            )
        )
        thrust_chamber = SolidMotorThrustChamberFactory.build(
            nozzle=NozzleFactory.build(
                inlet_diameter=43e-3,
                throat_diameter=9.5e-3,
                divergent_angle=12,
                convergent_angle=40,
                expansion_ratio=8,
            ),
            combustion_chamber=CombustionChamberFactory.build(
                casing_inner_diameter=44.5e-3,
                casing_outer_diameter=50.8e-3,
                thermal_liner_thickness=1e-3,
                internal_length=grain.total_length + 10e-3,
            ),
            center_of_gravity_coordinate=(0.05, 0.0, 0.0),
        )
        motor = SolidMotorFactory.build(
            grain=grain,
            propellant=solid_propellants.KNDX,
            thrust_chamber=thrust_chamber,
        )

        cog = motor.get_center_of_gravity(web_distance=0.0)

        assert isinstance(cog, np.ndarray)
        assert cog.shape == (3,)
        assert cog[0] > 0


class TestLiquidEngineCoG:
    def test_liquid_engine_cog_default_estimates(self):
        engine = LiquidEngineFactory.build()

        cog_full = engine.get_center_of_gravity(propellant_fraction=0.0)
        assert isinstance(cog_full, np.ndarray)
        assert cog_full.shape == (3,)
        assert cog_full[0] > 0

        cog_half = engine.get_center_of_gravity(propellant_fraction=0.5)
        assert isinstance(cog_half, np.ndarray)
        assert cog_half.shape == (3,)

    def test_liquid_engine_cog_custom_positions(self):
        dry_cog_value = 0.15
        ox_cog = 0.8
        fuel_cog = 0.75

        engine = LiquidEngineFactory.build(
            thrust_chamber=LiquidEngineThrustChamberFactory.build(
                dry_mass=5.0,
                center_of_gravity_coordinate=(dry_cog_value, 0.0, 0.0),
            ),
            oxidizer_tank_cog=ox_cog,
            fuel_tank_cog=fuel_cog,
        )

        cog = engine.get_center_of_gravity(propellant_fraction=0.0)

        assert isinstance(cog, np.ndarray)
        assert cog.shape == (3,)

        assert cog[0] > dry_cog_value
        assert cog[0] < max(ox_cog, fuel_cog)

        cog_empty = engine.get_center_of_gravity(propellant_fraction=1.0)
        assert abs(cog_empty[0] - dry_cog_value) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
