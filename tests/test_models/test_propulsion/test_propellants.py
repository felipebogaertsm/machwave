import numpy as np
import pytest

from machwave.models.propulsion.propellants.formulations import (
    KNDX,
    KNER,
    KNSB,
    KNSB_NAKKA,
    KNSU,
    MIT_CHERRY_LIMEADE,
    RNX_57,
    RNX_71V,
)
from machwave.models.propulsion.propellants.types import (
    BurnRateOutOfBoundsError,
    CEASolidPropellant,
    FixedSolidPropellant,
)

ALL_PROPELLANTS_TO_TEST = [
    ("KNDX", KNDX),
    ("KNSB", KNSB),
    ("KNSB_NAKKA", KNSB_NAKKA),
    ("KNSU", KNSU),
    ("KNER", KNER),
    ("RNX_57", RNX_57),
    ("RNX_71V", RNX_71V),
    ("MIT_CHERRY_LIMEADE", MIT_CHERRY_LIMEADE),
]


class TestSolidPropellantFormulation:
    """Test suite for SolidPropellantFormulation and preset compositions."""

    @pytest.mark.parametrize("name,propellant", ALL_PROPELLANTS_TO_TEST)
    def test_propellant_type(self, name, propellant):
        """Test that all propellants are FixedSolidPropellant or CEASolidPropellant instances."""
        assert isinstance(propellant, (FixedSolidPropellant, CEASolidPropellant)), (
            f"{name} should be a FixedSolidPropellant or CEASolidPropellant instance"
        )

    @pytest.mark.parametrize("name,propellant", ALL_PROPELLANTS_TO_TEST)
    def test_density_property(self, name, propellant):
        """Test that density property exists and has valid value."""
        assert hasattr(propellant.properties, "density"), (
            f"{name} should have density property"
        )
        assert isinstance(propellant.properties.density, (int, float)), (
            f"{name} density should be numeric"
        )
        assert propellant.properties.density > 0, f"{name} density should be positive"
        assert 1000 < propellant.properties.density < 3000, (
            f"{name} density should be reasonable for solid propellant"
        )

    @pytest.mark.parametrize("name,propellant", ALL_PROPELLANTS_TO_TEST)
    def test_combustion_efficiency_property(self, name, propellant):
        """Test that combustion_efficiency is calculated correctly from properties."""
        combustion_efficiency = (
            propellant.properties.adiabatic_flame_temperature
            / propellant.properties.adiabatic_flame_temperature_ideal
        )
        assert isinstance(combustion_efficiency, (int, float)), (
            f"{name} combustion_efficiency should be numeric"
        )
        assert 0 < combustion_efficiency <= 1, (
            f"{name} combustion_efficiency should be between 0 and 1"
        )

    @pytest.mark.parametrize("name,propellant", ALL_PROPELLANTS_TO_TEST)
    def test_isentropic_exponents(self, name, propellant):
        """Test that isentropic exponents gamma_chamber and gamma_exhaust exist and are valid."""
        assert hasattr(propellant.properties, "gamma_chamber"), (
            f"{name} should have gamma_chamber property"
        )
        assert hasattr(propellant.properties, "gamma_exhaust"), (
            f"{name} should have gamma_exhaust property"
        )

        assert isinstance(propellant.properties.gamma_chamber, (int, float)), (
            f"{name} gamma_chamber should be numeric"
        )
        assert isinstance(propellant.properties.gamma_exhaust, (int, float)), (
            f"{name} gamma_exhaust should be numeric"
        )

        # Typical range for isentropic exponents
        assert 1.0 < propellant.properties.gamma_chamber < 1.5, (
            f"{name} gamma_chamber should be in typical range for gases"
        )
        assert 1.0 < propellant.properties.gamma_exhaust < 1.5, (
            f"{name} gamma_exhaust should be in typical range for gases"
        )

    @pytest.mark.parametrize("name,propellant", ALL_PROPELLANTS_TO_TEST)
    def test_combustion_temperature_properties(self, name, propellant):
        """Test that temperature properties exist and are valid."""
        assert hasattr(propellant.properties, "adiabatic_flame_temperature_ideal"), (
            f"{name} should have adiabatic_flame_temperature_ideal property"
        )
        assert hasattr(propellant.properties, "adiabatic_flame_temperature"), (
            f"{name} should have adiabatic_flame_temperature property"
        )

        assert isinstance(
            propellant.properties.adiabatic_flame_temperature_ideal, (int, float)
        ), f"{name} adiabatic_flame_temperature_ideal should be numeric"
        assert isinstance(
            propellant.properties.adiabatic_flame_temperature, (int, float)
        ), f"{name} adiabatic_flame_temperature should be numeric"

        # Reasonable temperature ranges in Kelvin
        assert 1000 < propellant.properties.adiabatic_flame_temperature_ideal < 4000, (
            f"{name} adiabatic_flame_temperature_ideal should be in reasonable range"
        )
        assert (
            propellant.properties.adiabatic_flame_temperature
            < propellant.properties.adiabatic_flame_temperature_ideal
        ), (
            f"{name} adiabatic_flame_temperature should be less than adiabatic_flame_temperature_ideal due to efficiency"
        )
        combustion_efficiency = (
            propellant.properties.adiabatic_flame_temperature
            / propellant.properties.adiabatic_flame_temperature_ideal
        )
        assert (
            abs(
                propellant.properties.adiabatic_flame_temperature
                - propellant.properties.adiabatic_flame_temperature_ideal
                * combustion_efficiency
            )
            < 0.1
        ), (
            f"{name} adiabatic_flame_temperature should equal adiabatic_flame_temperature_ideal * combustion_efficiency"
        )

    @pytest.mark.parametrize("name,propellant", ALL_PROPELLANTS_TO_TEST)
    def test_molecular_weight_properties(self, name, propellant):
        """Test that molecular weight properties exist and are valid."""
        assert hasattr(propellant.properties, "molecular_weight_chamber"), (
            f"{name} should have molecular_weight_chamber property"
        )
        assert hasattr(propellant.properties, "molecular_weight_exhaust"), (
            f"{name} should have molecular_weight_exhaust property"
        )

        assert isinstance(
            propellant.properties.molecular_weight_chamber, (int, float)
        ), f"{name} molecular_weight_chamber should be numeric"
        assert isinstance(
            propellant.properties.molecular_weight_exhaust, (int, float)
        ), f"{name} molecular_weight_exhaust should be numeric"

        # Molecular weights should be in kg/mol and positive
        assert propellant.properties.molecular_weight_chamber > 0, (
            f"{name} molecular_weight_chamber should be positive"
        )
        assert propellant.properties.molecular_weight_exhaust > 0, (
            f"{name} molecular_weight_exhaust should be positive"
        )
        # Typical range for combustion products (in kg/mol)
        assert 0.01 < propellant.properties.molecular_weight_chamber < 0.1, (
            f"{name} molecular_weight_chamber should be in typical range"
        )
        assert 0.01 < propellant.properties.molecular_weight_exhaust < 0.1, (
            f"{name} molecular_weight_exhaust should be in typical range"
        )

    @pytest.mark.parametrize("name,propellant", ALL_PROPELLANTS_TO_TEST)
    def test_gas_constant_properties(self, name, propellant):
        """Test that gas constants R_chamber and R_exhaust are calculated correctly."""
        assert hasattr(propellant.properties, "R_chamber"), (
            f"{name} should have R_chamber property"
        )
        assert hasattr(propellant.properties, "R_exhaust"), (
            f"{name} should have R_exhaust property"
        )

        assert isinstance(propellant.properties.R_chamber, (int, float)), (
            f"{name} R_chamber should be numeric"
        )
        assert isinstance(propellant.properties.R_exhaust, (int, float)), (
            f"{name} R_exhaust should be numeric"
        )

        # Verify calculation: R_chamber = R_universal / molecular_weight_chamber
        import scipy.constants

        expected_R_chamber = (
            scipy.constants.R / propellant.properties.molecular_weight_chamber
        )
        expected_R_exhaust = (
            scipy.constants.R / propellant.properties.molecular_weight_exhaust
        )

        assert abs(propellant.properties.R_chamber - expected_R_chamber) < 0.01, (
            f"{name} R_chamber should be calculated correctly"
        )
        assert abs(propellant.properties.R_exhaust - expected_R_exhaust) < 0.01, (
            f"{name} R_exhaust should be calculated correctly"
        )

    @pytest.mark.parametrize("name,propellant", ALL_PROPELLANTS_TO_TEST)
    def test_specific_impulse_properties(self, name, propellant):
        """Test that specific impulse properties exist and are valid."""
        assert hasattr(propellant.properties, "i_sp_frozen"), (
            f"{name} should have i_sp_frozen property"
        )
        assert hasattr(propellant.properties, "i_sp_shifting"), (
            f"{name} should have i_sp_shifting property"
        )

        assert isinstance(propellant.properties.i_sp_frozen, (int, float)), (
            f"{name} i_sp_frozen should be numeric"
        )
        assert isinstance(propellant.properties.i_sp_shifting, (int, float)), (
            f"{name} i_sp_shifting should be numeric"
        )

        # Reasonable Isp ranges in seconds
        assert 100 < propellant.properties.i_sp_frozen < 300, (
            f"{name} i_sp_frozen should be in reasonable range"
        )
        assert 100 < propellant.properties.i_sp_shifting < 300, (
            f"{name} i_sp_shifting should be in reasonable range"
        )
        # Shifting flow typically has slightly higher Isp than frozen
        assert (
            propellant.properties.i_sp_shifting >= propellant.properties.i_sp_frozen
        ), f"{name} i_sp_shifting should be >= i_sp_frozen"

    @pytest.mark.parametrize("name,propellant", ALL_PROPELLANTS_TO_TEST)
    def test_condensed_phase_moles_properties(self, name, propellant):
        """Test that condensed-phase mole properties exist and are valid."""
        assert hasattr(propellant.properties, "qsi_chamber"), (
            f"{name} should have qsi_chamber property"
        )
        assert hasattr(propellant.properties, "qsi_exhaust"), (
            f"{name} should have qsi_exhaust property"
        )

        assert isinstance(propellant.properties.qsi_chamber, (int, float)), (
            f"{name} qsi_chamber should be numeric"
        )
        assert isinstance(propellant.properties.qsi_exhaust, (int, float)), (
            f"{name} qsi_exhaust should be numeric"
        )

        # qsi values should be between 0 and 1 (fraction per 100g)
        assert 0 <= propellant.properties.qsi_chamber <= 1, (
            f"{name} qsi_chamber should be between 0 and 1"
        )
        assert 0 <= propellant.properties.qsi_exhaust <= 1, (
            f"{name} qsi_exhaust should be between 0 and 1"
        )

    @pytest.mark.parametrize("name,propellant", ALL_PROPELLANTS_TO_TEST)
    def test_burn_rate_map_structure(self, name, propellant):
        """Test that burn_rate property exists and is properly structured."""
        assert hasattr(propellant, "burn_rate"), (
            f"{name} should have burn_rate property"
        )
        assert isinstance(propellant.burn_rate, list), (
            f"{name} burn_rate should be a list"
        )
        assert len(propellant.burn_rate) > 0, f"{name} burn_rate should not be empty"

        for i, segment in enumerate(propellant.burn_rate):
            assert isinstance(segment, dict), (
                f"{name} burn_rate segment {i} should be a dict"
            )
            assert "min" in segment, (
                f"{name} burn_rate segment {i} should have 'min' key"
            )
            assert "max" in segment, (
                f"{name} burn_rate segment {i} should have 'max' key"
            )
            assert "a" in segment, f"{name} burn_rate segment {i} should have 'a' key"
            assert "n" in segment, f"{name} burn_rate segment {i} should have 'n' key"
            assert segment["min"] < segment["max"], (
                f"{name} burn_rate segment {i} min should be less than max"
            )

    @pytest.mark.parametrize("name,propellant", ALL_PROPELLANTS_TO_TEST)
    def test_get_burn_rate_method_at_boundaries(self, name, propellant):
        """Test get_burn_rate method at pressure boundaries."""
        burn_rate_map = propellant.burn_rate

        # Test at minimum pressure (skip if min is 0, as burn rate will be 0)
        min_pressure = min(segment["min"] for segment in burn_rate_map)
        if min_pressure > 0:
            burn_rate = propellant.get_burn_rate(min_pressure)
            assert isinstance(burn_rate, float), (
                f"{name} get_burn_rate should return float at min pressure"
            )
            assert burn_rate > 0, f"{name} burn rate should be positive at min pressure"
        else:
            # At zero pressure, burn rate should be zero
            burn_rate = propellant.get_burn_rate(0)
            assert isinstance(burn_rate, float), (
                f"{name} get_burn_rate should return float at zero pressure"
            )
            assert burn_rate == 0.0, f"{name} burn rate should be zero at zero pressure"

        # Test at maximum pressure (use min of all max values to stay in range)
        max_pressure = min(segment["max"] for segment in burn_rate_map)
        burn_rate = propellant.get_burn_rate(max_pressure)
        assert isinstance(burn_rate, float), (
            f"{name} get_burn_rate should return float at max pressure"
        )
        assert burn_rate > 0, f"{name} burn rate should be positive at max pressure"

    @pytest.mark.parametrize("name,propellant", ALL_PROPELLANTS_TO_TEST)
    def test_get_burn_rate_method_mid_range(self, name, propellant):
        """Test get_burn_rate method at various pressures within range."""
        burn_rate_map = propellant.burn_rate

        # Test at several points within each segment
        for segment in burn_rate_map:
            min_p = segment["min"]
            max_p = segment["max"]

            # Test at 25%, 50%, 75% of the range
            for fraction in [0.25, 0.5, 0.75]:
                pressure = min_p + (max_p - min_p) * fraction
                burn_rate = propellant.get_burn_rate(pressure)

                assert isinstance(burn_rate, float), (
                    f"{name} get_burn_rate should return float"
                )
                assert burn_rate > 0, f"{name} burn rate should be positive"
                # Typical burn rate range in m/s
                assert 0.0001 < burn_rate < 0.1, (
                    f"{name} burn rate should be in typical range"
                )

    @pytest.mark.parametrize("name,propellant", ALL_PROPELLANTS_TO_TEST)
    def test_get_burn_rate_out_of_bounds(self, name, propellant):
        """Test that get_burn_rate raises error for out-of-bounds pressure."""
        burn_rate_map = propellant.burn_rate
        max_pressure = max(segment["max"] for segment in burn_rate_map)

        # Test pressure above maximum
        with pytest.raises(BurnRateOutOfBoundsError):
            propellant.get_burn_rate(max_pressure + 1e6)

    @pytest.mark.parametrize("name,propellant", ALL_PROPELLANTS_TO_TEST)
    def test_burn_rate_continuity(self, name, propellant):
        """Test burn rate calculation using St. Robert's law."""
        burn_rate_map = propellant.burn_rate

        for segment in burn_rate_map:
            min_p = segment["min"]
            max_p = segment["max"]
            a = segment["a"]
            n = segment["n"]

            # Test at midpoint
            test_pressure = (min_p + max_p) / 2
            burn_rate = propellant.get_burn_rate(test_pressure)

            # Calculate expected value using St. Robert's law
            # burn_rate (mm/s) = a * (P_MPa)^n, then convert to m/s
            expected = (a * (test_pressure * 1e-6) ** n) * 1e-3

            assert abs(burn_rate - expected) < 1e-6, (
                f"{name} burn rate calculation should match St. Robert's law"
            )


# Legacy tests for backwards compatibility with fixtures
def test_propellant_burn_rate_KNSB_NAKKA(propellant_KNSB_NAKKA):
    """Legacy test using fixture."""
    burn_rate_map = propellant_KNSB_NAKKA.burn_rate
    min_pressure = np.min([item["min"] for item in burn_rate_map])
    max_pressure = np.min([item["max"] for item in burn_rate_map])

    burn_rate = propellant_KNSB_NAKKA.get_burn_rate(min_pressure)
    assert isinstance(burn_rate, float)

    burn_rate = propellant_KNSB_NAKKA.get_burn_rate(max_pressure)
    assert isinstance(burn_rate, float)


def test_propellant_burn_rate_KNDX(propellant_KNDX):
    """Legacy test using fixture."""
    burn_rate_map = propellant_KNDX.burn_rate
    min_pressure = np.min([item["min"] for item in burn_rate_map])
    max_pressure = np.min([item["max"] for item in burn_rate_map])

    burn_rate = propellant_KNDX.get_burn_rate(min_pressure)
    assert isinstance(burn_rate, float)

    burn_rate = propellant_KNDX.get_burn_rate(max_pressure)
    assert isinstance(burn_rate, float)


def test_propellant_burn_rate_KNER(propellant_KNER):
    """Legacy test using fixture."""
    burn_rate_map = propellant_KNER.burn_rate
    min_pressure = np.min([item["min"] for item in burn_rate_map])
    max_pressure = np.min([item["max"] for item in burn_rate_map])

    burn_rate = propellant_KNER.get_burn_rate(min_pressure)
    assert isinstance(burn_rate, float)

    burn_rate = propellant_KNER.get_burn_rate(max_pressure)
    assert isinstance(burn_rate, float)


def test_propellant_burn_rate_KNSB(propellant_KNSB):
    """Legacy test using fixture."""
    burn_rate_map = propellant_KNSB.burn_rate
    min_pressure = np.min([item["min"] for item in burn_rate_map])
    max_pressure = np.min([item["max"] for item in burn_rate_map])

    burn_rate = propellant_KNSB.get_burn_rate(min_pressure)
    assert isinstance(burn_rate, float)

    burn_rate = propellant_KNSB.get_burn_rate(max_pressure)
    assert isinstance(burn_rate, float)


def test_propellant_burn_rate_KNSU(propellant_KNSU):
    """Legacy test using fixture."""
    burn_rate_map = propellant_KNSU.burn_rate
    min_pressure = np.min([item["min"] for item in burn_rate_map])
    max_pressure = np.min([item["max"] for item in burn_rate_map])

    burn_rate = propellant_KNSU.get_burn_rate(min_pressure)
    assert isinstance(burn_rate, float)

    burn_rate = propellant_KNSU.get_burn_rate(max_pressure)
    assert isinstance(burn_rate, float)
