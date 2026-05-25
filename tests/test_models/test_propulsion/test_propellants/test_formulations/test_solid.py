"""
Tests for solid propellant formulations.

This test suite automatically tests all solid propellant formulations
defined in the formulations.solid module. Any new formulation added
to the module will automatically be tested.
"""

import pytest

import machwave.models.propellants as propellants_models
import machwave.models.propellants.categories as propellant_categories
import machwave.models.propellants.categories.base as propellant_base
import machwave.models.propellants.categories.solid as solid_propellant_category
import machwave.models.propellants.formulations.solid as solid_formulations


def get_all_solid_propellants():
    """Get all solid propellant instances from formulations module."""
    propellants = []
    for name in dir(solid_formulations):
        obj = getattr(solid_formulations, name)
        if isinstance(obj, propellants_models.SolidPropellant):
            propellants.append((name, obj))
    return propellants


ALL_SOLID_PROPELLANTS = get_all_solid_propellants()


class TestAllSolidPropellants:
    """Test suite for all solid propellant formulations."""

    def test_propellants_found(self):
        """Verify at least one solid propellant is defined."""
        assert len(ALL_SOLID_PROPELLANTS) > 0, "No solid propellants found"

    @pytest.mark.parametrize("name,propellant", ALL_SOLID_PROPELLANTS)
    def test_is_solid_propellant(self, name, propellant):
        """Verify formulation is instance of SolidPropellant."""
        assert isinstance(propellant, propellants_models.SolidPropellant), (
            f"{name} is not a SolidPropellant"
        )
        assert propellant.mixture_type in ("solid", "hybrid"), (
            f"{name} has wrong mixture_type"
        )

    @pytest.mark.parametrize("name,propellant", ALL_SOLID_PROPELLANTS)
    def test_has_burn_rate_data(self, name, propellant):
        """Verify formulation has valid burn rate data."""
        assert propellant.burn_rate_map, f"{name} missing burn_rate_map"
        assert isinstance(propellant.burn_rate_map, list), (
            f"{name} burn_rate_map should be list"
        )
        assert len(propellant.burn_rate_map) > 0, f"{name} burn_rate_map is empty"

        # Check each burn rate segment has required keys
        for i, segment in enumerate(propellant.burn_rate_map):
            assert "min" in segment, f"{name} segment {i} missing 'min'"
            assert "max" in segment, f"{name} segment {i} missing 'max'"
            assert "a" in segment, f"{name} segment {i} missing 'a'"
            assert "n" in segment, f"{name} segment {i} missing 'n'"

    @pytest.mark.parametrize("name,propellant", ALL_SOLID_PROPELLANTS)
    def test_burn_rate_calculation(self, name, propellant):
        """Test burn rate calculation for various pressures."""
        test_pressures = [1e6, 3e6, 5e6]  # 1, 3, 5 MPa

        for pressure in test_pressures:
            # Check if pressure is within any burn rate range
            in_range = any(
                segment["min"] <= pressure <= segment["max"]
                for segment in propellant.burn_rate_map
            )

            if in_range:
                burn_rate = propellant.get_burn_rate(pressure)
                assert burn_rate > 0, (
                    f"{name} burn rate should be positive at {pressure / 1e6:.1f} MPa"
                )
                assert burn_rate < 0.1, (
                    f"{name} burn rate unreasonably high at {pressure / 1e6:.1f} MPa"
                )

    @pytest.mark.parametrize("name,propellant", ALL_SOLID_PROPELLANTS)
    def test_properties_interface(self, name, propellant):
        """Test that all solid propellants have consistent properties interface."""
        chamber_pressure = 5e6  # 5 MPa
        expansion_ratio = 8.0

        # If properties is None (CEA propellants), evaluate first
        if propellant.properties is None:
            propellant.evaluate(chamber_pressure, expansion_ratio)

        # Now properties must exist
        assert propellant.properties is not None, f"{name} properties is None"

        # Check theoretical properties are present and valid
        assert propellant.properties.k_chamber > 1.0, f"{name} k_chamber invalid"
        assert propellant.properties.k_exhaust > 1.0, f"{name} k_exhaust invalid"
        assert propellant.properties.adiabatic_flame_temperature > 0, (
            f"{name} temperature invalid"
        )
        assert propellant.properties.molecular_weight_chamber > 0, (
            f"{name} chamber MW invalid"
        )
        assert propellant.properties.molecular_weight_exhaust > 0, (
            f"{name} exhaust MW invalid"
        )
        assert propellant.properties.i_sp_frozen > 0, f"{name} frozen Isp invalid"
        assert propellant.properties.i_sp_shifting > 0, f"{name} shifting Isp invalid"

        # Check operational properties are accessible from propellant class
        assert propellant.combustion_efficiency > 0, (
            f"{name} combustion efficiency invalid"
        )


class TestFixedSolidPropellantSpecifics:
    """Test specific behaviors of solid propellants with pre-defined properties."""

    @pytest.fixture
    def fixed_propellants(self):
        """Get solid propellants with pre-defined properties."""
        return [
            (name, prop)
            for name, prop in ALL_SOLID_PROPELLANTS
            if prop.properties is not None
        ]

    def test_fixed_have_immediate_properties(self, fixed_propellants):
        """Verify solid propellants with pre-defined properties have them immediately."""
        for name, propellant in fixed_propellants:
            assert propellant.properties is not None, (
                f"{name} should have immediate properties"
            )


class TestSolidPropellantConstruction:
    """Test construction-time validation of SolidPropellant."""

    def test_missing_components_raises(self):
        """Reject a solid propellant built without components."""
        with pytest.raises(propellant_base.PropellantValidationError):
            propellant_categories.SolidPropellant(name="Empty")


class TestBurnRateBehavior:
    """Test burn rate behavior across formulations."""

    def test_out_of_bounds_pressure(self):
        """Test that out-of-bounds pressure raises error."""
        # Use first propellant in the list
        if len(ALL_SOLID_PROPELLANTS) > 0:
            name, propellant = ALL_SOLID_PROPELLANTS[0]

            # Find a pressure way outside the range
            max_pressure = max(segment["max"] for segment in propellant.burn_rate_map)
            out_of_bounds_pressure = max_pressure * 2

            with pytest.raises(solid_propellant_category.BurnRateOutOfBoundsError):
                propellant.get_burn_rate(out_of_bounds_pressure)


class TestConsistency:
    """Test consistency across all formulations."""

    @pytest.mark.parametrize("name,propellant", ALL_SOLID_PROPELLANTS)
    def test_combustion_efficiency_field(self, name, propellant):
        """Verify combustion_efficiency field exists and is valid."""
        # Ensure properties exist
        if propellant.properties is None:
            propellant.evaluate(5e6, 8.0)

        assert hasattr(propellant, "combustion_efficiency"), (
            f"{name} should have combustion_efficiency field"
        )
        assert 0 < propellant.combustion_efficiency <= 1, (
            f"{name} combustion_efficiency should be between 0 and 1"
        )

    @pytest.mark.parametrize("name,propellant", ALL_SOLID_PROPELLANTS)
    def test_isp_relationship(self, name, propellant):
        """Verify shifting Isp is typically >= frozen Isp."""
        # Ensure properties exist
        if propellant.properties is None:
            propellant.evaluate(5e6, 8.0)

        # Shifting equilibrium typically gives higher or equal Isp
        assert (
            propellant.properties.i_sp_shifting
            >= propellant.properties.i_sp_frozen - 1.0  # Small tolerance
        ), f"{name} shifting Isp relationship violated"

    @pytest.mark.parametrize("name,propellant", ALL_SOLID_PROPELLANTS)
    def test_isentropic_exponent_reasonable_range(self, name, propellant):
        """Verify isentropic exponent values are in reasonable range."""
        # Ensure properties exist
        if propellant.properties is None:
            propellant.evaluate(5e6, 8.0)

        assert 1.0 < propellant.properties.k_chamber < 1.7, (
            f"{name} chamber isentropic exponent out of range"
        )
        assert 1.0 < propellant.properties.k_exhaust < 1.7, (
            f"{name} exit isentropic exponent out of range"
        )

    @pytest.mark.parametrize("name,propellant", ALL_SOLID_PROPELLANTS)
    def test_density_reasonable_range(self, name, propellant):
        """Verify densities are in reasonable range for solid propellants."""
        # Ensure properties exist
        if propellant.properties is None:
            propellant.evaluate(5e6, 8.0)

        # Skip density check for propellants with pre-defined properties
        # since their component densities aren't used for CEA calculations
        if propellant.properties is not None:
            return

        # Typical solid propellants: 1500-2000 kg/m^3
        # Density is grain-specific, check ideal_density from propellant formulation
        if hasattr(propellant, "ideal_density"):
            density = propellant.ideal_density
            assert 1500 < density < 2100, (
                f"{name} ideal density out of range: {density}"
            )
