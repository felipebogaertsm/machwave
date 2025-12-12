"""Tests for solid propellant formulations.

This test suite automatically tests all solid propellant formulations
defined in the formulations.solid module. Any new formulation added
to the module will automatically be tested.
"""

import pytest

import machwave.models.propulsion.propellants.formulations.solid as solid_formulations
from machwave.models.propulsion.propellants.categories import (
    CEASolidPropellant,
    FixedSolidPropellant,
    SolidPropellant,
)
from machwave.models.propulsion.propellants.categories.base import (
    BurnRateOutOfBoundsError,
)


def get_all_solid_propellants():
    """Get all solid propellant instances from formulations module."""
    propellants = []
    for name in dir(solid_formulations):
        obj = getattr(solid_formulations, name)
        if isinstance(obj, SolidPropellant):
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
        assert isinstance(propellant, SolidPropellant), (
            f"{name} is not a SolidPropellant"
        )

    @pytest.mark.parametrize("name,propellant", ALL_SOLID_PROPELLANTS)
    def test_has_burn_rate_data(self, name, propellant):
        """Verify formulation has valid burn rate data."""
        assert propellant.burn_rate, f"{name} missing burn_rate"
        assert isinstance(propellant.burn_rate, list), (
            f"{name} burn_rate should be list"
        )
        assert len(propellant.burn_rate) > 0, f"{name} burn_rate is empty"

        # Check each burn rate segment has required keys
        for i, segment in enumerate(propellant.burn_rate):
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
                for segment in propellant.burn_rate
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

        # Check key properties are present and valid
        assert propellant.properties.gamma_chamber > 1.0, (
            f"{name} gamma_chamber invalid"
        )
        assert propellant.properties.gamma_exhaust > 1.0, (
            f"{name} gamma_exhaust invalid"
        )
        assert propellant.properties.adiabatic_flame_temperature > 0, (
            f"{name} temperature invalid"
        )
        assert propellant.properties.adiabatic_flame_temperature_ideal > 0, (
            f"{name} ideal temperature invalid"
        )
        assert propellant.properties.molecular_weight_chamber > 0, (
            f"{name} chamber MW invalid"
        )
        assert propellant.properties.molecular_weight_exhaust > 0, (
            f"{name} exhaust MW invalid"
        )
        assert propellant.properties.i_sp_frozen > 0, f"{name} frozen Isp invalid"
        assert propellant.properties.i_sp_shifting > 0, f"{name} shifting Isp invalid"
        assert propellant.properties.density > 0, f"{name} density invalid"


class TestFixedSolidPropellantSpecifics:
    """Test specific behaviors of FixedSolidPropellant formulations."""

    @pytest.fixture
    def fixed_propellants(self):
        """Get only FixedSolidPropellant formulations."""
        return [
            (name, prop)
            for name, prop in ALL_SOLID_PROPELLANTS
            if isinstance(prop, FixedSolidPropellant)
        ]

    def test_fixed_have_immediate_properties(self, fixed_propellants):
        """Verify FixedSolidPropellant formulations have properties immediately."""
        for name, propellant in fixed_propellants:
            assert propellant.properties is not None, (
                f"{name} should have immediate properties"
            )


class TestCEASolidPropellantSpecifics:
    """Test specific behaviors of CEASolidPropellant formulations."""

    @pytest.fixture
    def cea_propellants(self):
        """Get only CEASolidPropellant formulations."""
        return [
            (name, prop)
            for name, prop in ALL_SOLID_PROPELLANTS
            if isinstance(prop, CEASolidPropellant)
        ]

    def test_cea_have_density_attributes(self, cea_propellants):
        """Verify CEA propellants have ideal_density and density_percentage."""
        for name, propellant in cea_propellants:
            assert hasattr(propellant, "ideal_density"), f"{name} missing ideal_density"
            assert hasattr(propellant, "density_percentage"), (
                f"{name} missing density_percentage"
            )
            assert propellant.ideal_density > 0, f"{name} ideal_density invalid"
            assert 0 < propellant.density_percentage <= 100, (
                f"{name} density_percentage invalid"
            )

    def test_cea_real_density_calculation(self, cea_propellants):
        """Test real_density() method for CEA propellants."""
        for name, propellant in cea_propellants:
            expected = propellant.ideal_density * (
                propellant.density_percentage / 100.0
            )
            actual = propellant.real_density()
            assert abs(actual - expected) < 0.01, (
                f"{name} real_density calculation incorrect"
            )

    def test_cea_evaluate_populates_properties(self, cea_propellants):
        """Test that evaluate() populates properties for CEA propellants."""
        chamber_pressure = 5e6  # 5 MPa
        expansion_ratio = 8.0

        for name, propellant in cea_propellants:
            # Create fresh instance to test from None state
            fresh_instance = CEASolidPropellant(
                cea_name=propellant.cea_name,
                burn_rate=propellant.burn_rate,
                ideal_density=propellant.ideal_density,
                density_percentage=propellant.density_percentage,
                combustion_efficiency=propellant.combustion_efficiency,
            )

            assert fresh_instance.properties is None, (
                f"{name} properties should initially be None"
            )

            properties = fresh_instance.evaluate(chamber_pressure, expansion_ratio)

            assert properties is not None, f"{name} evaluate() returned None"
            assert fresh_instance.properties is properties, (
                f"{name} properties not stored"
            )


class TestBurnRateBehavior:
    """Test burn rate behavior across formulations."""

    def test_out_of_bounds_pressure(self):
        """Test that out-of-bounds pressure raises error."""
        # Use first propellant in the list
        if len(ALL_SOLID_PROPELLANTS) > 0:
            name, propellant = ALL_SOLID_PROPELLANTS[0]

            # Find a pressure way outside the range
            max_pressure = max(segment["max"] for segment in propellant.burn_rate)
            out_of_bounds_pressure = max_pressure * 2

            with pytest.raises(BurnRateOutOfBoundsError):
                propellant.get_burn_rate(out_of_bounds_pressure)


class TestConsistency:
    """Test consistency across all formulations."""

    @pytest.mark.parametrize("name,propellant", ALL_SOLID_PROPELLANTS)
    def test_temperature_relationship(self, name, propellant):
        """Verify ideal temperature is always >= actual temperature."""
        # Ensure properties exist
        if propellant.properties is None:
            propellant.evaluate(5e6, 8.0)

        assert (
            propellant.properties.adiabatic_flame_temperature_ideal
            >= propellant.properties.adiabatic_flame_temperature
        ), f"{name} ideal temp should be >= actual temp"

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
    def test_gamma_reasonable_range(self, name, propellant):
        """Verify gamma values are in reasonable range."""
        # Ensure properties exist
        if propellant.properties is None:
            propellant.evaluate(5e6, 8.0)

        assert 1.0 < propellant.properties.gamma_chamber < 1.7, (
            f"{name} chamber gamma out of range"
        )
        assert 1.0 < propellant.properties.gamma_exhaust < 1.7, (
            f"{name} exhaust gamma out of range"
        )

    @pytest.mark.parametrize("name,propellant", ALL_SOLID_PROPELLANTS)
    def test_density_reasonable_range(self, name, propellant):
        """Verify densities are in reasonable range for solid propellants."""
        # Ensure properties exist
        if propellant.properties is None:
            propellant.evaluate(5e6, 8.0)

        # Typical solid propellants: 1500-2000 kg/m³
        assert 1500 < propellant.properties.density < 2000, (
            f"{name} density out of range"
        )
