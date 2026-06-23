import pytest

from tests.factories import (
    CombustionChamberFactory,
    NozzleFactory,
    SolidMotorThrustChamberFactory,
)


class TestThrustChamberValidation:
    @pytest.mark.parametrize("dry_mass", [0.0, -1.0])
    def test_non_positive_dry_mass(self, dry_mass):
        with pytest.raises(ValueError, match="dry_mass"):
            SolidMotorThrustChamberFactory.build(dry_mass=dry_mass)

    @pytest.mark.parametrize("inlet_diameter", [72e-3, 90e-3])
    def test_nozzle_inlet_larger_than_casing_bore(self, inlet_diameter):
        # Default chamber casing_inner_diameter is 70 mm.
        oversized_nozzle = NozzleFactory.build(inlet_diameter=inlet_diameter)
        with pytest.raises(ValueError, match="does not fit"):
            SolidMotorThrustChamberFactory.build(nozzle=oversized_nozzle)

    def test_nozzle_inlet_flush_with_casing_bore_is_allowed(self):
        """A nozzle inlet equal to the casing bore fits (flush mounting)."""
        nozzle = NozzleFactory.build(inlet_diameter=70e-3)
        chamber = CombustionChamberFactory.build(casing_inner_diameter=70e-3)
        thrust_chamber = SolidMotorThrustChamberFactory.build(
            nozzle=nozzle, combustion_chamber=chamber
        )
        assert thrust_chamber.nozzle.inlet_diameter == pytest.approx(70e-3)

    @pytest.mark.parametrize("distance", [-0.01, -1.0])
    def test_negative_grain_port_distance(self, distance):
        with pytest.raises(ValueError, match="nozzle_exit_to_grain_port_distance"):
            SolidMotorThrustChamberFactory.build(
                nozzle_exit_to_grain_port_distance=distance
            )


def _test_combustion_chamber_properties(combustion_chamber_olympus):
    """
    Generic test function for CombustionChamber and its descendents.

    Tests geometric properties of the class, such as inner radius
    (calculated from inner diameter) and more.
    """
    net = combustion_chamber_olympus.inner_diameter
    gross = combustion_chamber_olympus.casing_inner_diameter

    assert net > 0
    assert net == gross - 2 * combustion_chamber_olympus.thermal_liner_thickness

    assert combustion_chamber_olympus.inner_radius == net / 2
    assert (
        combustion_chamber_olympus.outer_radius
        == combustion_chamber_olympus.outer_diameter / 2
    )

    assert gross == net + 2 * combustion_chamber_olympus.liner.thickness
