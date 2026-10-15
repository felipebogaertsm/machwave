import pytest

from machwave.common.mass_properties import DryMassProperties

from tests.factories import SolidMotorThrustChamberFactory


class TestThrustChamberValidation:
    @pytest.mark.parametrize("dry_mass", [0.0, -1.0])
    def test_non_positive_dry_mass(self, dry_mass):
        with pytest.raises(ValueError, match="dry_mass"):
            SolidMotorThrustChamberFactory.build(dry_mass=dry_mass)

    @pytest.mark.parametrize("distance", [-0.01, -1.0])
    def test_negative_grain_port_distance(self, distance):
        with pytest.raises(ValueError, match="nozzle_exit_to_grain_port_distance"):
            SolidMotorThrustChamberFactory.build(
                nozzle_exit_to_grain_port_distance=distance
            )

    def test_dry_mass_properties_optional(self):
        thrust_chamber = SolidMotorThrustChamberFactory.build(dry_mass_properties=None)
        assert thrust_chamber.dry_mass_properties is None


class TestDryMassProperties:
    @pytest.mark.parametrize("dry_mass", [0.0, -1.0])
    def test_non_positive_dry_mass(self, dry_mass):
        with pytest.raises(ValueError, match="dry_mass"):
            DryMassProperties(
                dry_mass=dry_mass,
                center_of_gravity_coordinate=(0.04, 0.0, 0.0),
                moment_of_inertia=(0.02, 0.02, 0.005),
            )

    @pytest.mark.parametrize("moment_of_inertia", [(-1.0, 0.1, 0.1), (0.1, 0.1, -0.02)])
    def test_negative_moment_of_inertia(self, moment_of_inertia):
        with pytest.raises(ValueError, match="moment_of_inertia components must be"):
            DryMassProperties(
                dry_mass=0.85,
                center_of_gravity_coordinate=(0.04, 0.0, 0.0),
                moment_of_inertia=moment_of_inertia,
            )

    @pytest.mark.parametrize("moment_of_inertia", [(0.1, 0.1), (0.1, 0.1, 0.1, 0.1)])
    def test_moment_of_inertia_wrong_length(self, moment_of_inertia):
        with pytest.raises(ValueError, match="three components"):
            DryMassProperties(
                dry_mass=0.85,
                center_of_gravity_coordinate=(0.04, 0.0, 0.0),
                moment_of_inertia=moment_of_inertia,
            )

    def test_wrong_length_center_of_gravity(self):
        with pytest.raises(ValueError, match="three components"):
            DryMassProperties(
                dry_mass=0.85,
                center_of_gravity_coordinate=(0.04, 0.0),
                moment_of_inertia=(0.02, 0.02, 0.005),
            )
