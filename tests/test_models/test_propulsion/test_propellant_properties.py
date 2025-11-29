"""Tests for propellant properties dataclasses."""

import pytest
import scipy.constants

from machwave.models.propulsion.propellants.properties import (
    ChemicalPropellantProperties,
    LiquidPropellantProperties,
    SolidPropellantProperties,
)
from tests.test_models.test_propulsion.factories import (
    LiquidPropellantPropertiesFactory,
    SolidPropellantPropertiesFactory,
)


class TestSolidPropellantProperties:
    """Test suite for SolidPropellantProperties."""

    def test_instantiation_with_all_required_fields(self):
        """Test that SolidPropellantProperties can be instantiated with all required fields."""
        props = SolidPropellantPropertiesFactory.build()

        # Verify all fields are set correctly
        assert props.gamma_chamber == 1.15
        assert props.density == 1800.0
        assert props.qsi_chamber == 0.3

    @pytest.mark.parametrize(
        "field",
        [
            "gamma_chamber",
            "gamma_exhaust",
            "adiabatic_flame_temperature",
            "adiabatic_flame_temperature_ideal",
            "molecular_weight_chamber",
            "molecular_weight_exhaust",
            "i_sp_frozen",
            "i_sp_shifting",
            "density",
            "qsi_chamber",
            "qsi_exhaust",
        ],
    )
    def test_required_fields(self, field):
        """Test that all fields are required."""
        # Build dict with all fields except the one being tested
        props = SolidPropellantPropertiesFactory.build()
        data = {k: v for k, v in props.__dict__.items() if k != field}

        with pytest.raises(TypeError):
            SolidPropellantProperties(**data)

    def test_inheritance(self):
        """Test that SolidPropellantProperties inherits from ChemicalPropellantProperties."""
        props = SolidPropellantPropertiesFactory.build()

        assert isinstance(props, ChemicalPropellantProperties)
        assert isinstance(props, SolidPropellantProperties)

    def test_dataclass_equality(self):
        """Test that dataclass equality works correctly."""
        props1 = SolidPropellantPropertiesFactory.build()
        props2 = SolidPropellantPropertiesFactory.build()

        assert props1 == props2

    def test_dataclass_repr(self):
        """Test that dataclass repr works correctly."""
        props = SolidPropellantPropertiesFactory.build()

        assert "SolidPropellantProperties" in repr(props)

    def test_dataclass_frozen(self):
        """Test that dataclass is immutable (frozen)."""
        props = SolidPropellantPropertiesFactory.build()

        with pytest.raises(AttributeError):
            props.density = 2000.0


class TestLiquidPropellantProperties:
    """Test suite for LiquidPropellantProperties."""

    def test_instantiation_with_all_required_fields(self):
        """Test that LiquidPropellantProperties can be instantiated with all required fields."""
        props = LiquidPropellantPropertiesFactory.build()

        # Verify all fields are set correctly
        assert props.gamma_chamber == 1.20
        assert props.oxidizer_tank_density == 1141.0
        assert props.fuel_tank_density == 810.0

    @pytest.mark.parametrize(
        "field",
        [
            "gamma_chamber",
            "gamma_exhaust",
            "adiabatic_flame_temperature",
            "adiabatic_flame_temperature_ideal",
            "molecular_weight_chamber",
            "molecular_weight_exhaust",
            "i_sp_frozen",
            "i_sp_shifting",
            "oxidizer_tank_density",
            "fuel_tank_density",
        ],
    )
    def test_required_fields(self, field):
        """Test that all fields are required."""
        props = LiquidPropellantPropertiesFactory.build()
        data = {k: v for k, v in props.__dict__.items() if k != field}

        with pytest.raises(TypeError):
            LiquidPropellantProperties(**data)

    def test_inheritance(self):
        """Test that LiquidPropellantProperties inherits from ChemicalPropellantProperties."""
        props = LiquidPropellantPropertiesFactory.build()

        assert isinstance(props, ChemicalPropellantProperties)
        assert isinstance(props, LiquidPropellantProperties)

    def test_dataclass_equality(self):
        """Test that dataclass equality works correctly."""
        props1 = LiquidPropellantPropertiesFactory.build()
        props2 = LiquidPropellantPropertiesFactory.build()

        assert props1 == props2

    def test_dataclass_repr(self):
        """Test that dataclass repr works correctly."""
        props = LiquidPropellantPropertiesFactory.build()

        assert "LiquidPropellantProperties" in repr(props)

    def test_dataclass_frozen(self):
        """Test that dataclass is immutable (frozen)."""
        props = LiquidPropellantPropertiesFactory.build()

        with pytest.raises(AttributeError):
            props.oxidizer_tank_density = 2000.0


class TestChemicalPropellantProperties:
    """Test suite for ChemicalPropellantProperties abstract base class."""

    def test_is_abstract(self):
        """Test that ChemicalPropellantProperties is an abstract base class."""
        assert issubclass(SolidPropellantProperties, ChemicalPropellantProperties)
        assert issubclass(LiquidPropellantProperties, ChemicalPropellantProperties)

    @pytest.mark.parametrize(
        "attr",
        [
            "gamma_chamber",
            "gamma_exhaust",
            "adiabatic_flame_temperature",
            "adiabatic_flame_temperature_ideal",
            "molecular_weight_chamber",
            "molecular_weight_exhaust",
            "i_sp_frozen",
            "i_sp_shifting",
        ],
    )
    def test_common_fields_exist(self, attr):
        """Test that all subclasses have the common fields from base class."""
        solid_props = SolidPropellantPropertiesFactory.build()
        liquid_props = LiquidPropellantPropertiesFactory.build()

        assert hasattr(solid_props, attr)
        assert hasattr(liquid_props, attr)

    @pytest.mark.parametrize(
        "method",
        ["R_chamber", "R_exhaust"],
    )
    def test_common_methods_exist(self, method):
        """Test that all subclasses have the common property methods from base class."""
        solid_props = SolidPropellantPropertiesFactory.build()
        liquid_props = LiquidPropellantPropertiesFactory.build()

        assert hasattr(solid_props, method)
        assert hasattr(liquid_props, method)
        # Verify they are properties
        assert isinstance(getattr(type(solid_props), method), property)
        assert isinstance(getattr(type(liquid_props), method), property)


class TestDerivedProperties:
    """Test suite for derived property calculations."""

    @pytest.mark.parametrize(
        "molecular_weight_chamber,expected_R_chamber",
        [
            (0.04, scipy.constants.R / 0.04),
            (0.02, scipy.constants.R / 0.02),
            (0.03, scipy.constants.R / 0.03),
        ],
    )
    def test_R_chamber_calculation(self, molecular_weight_chamber, expected_R_chamber):
        """Test that R_chamber is correctly calculated from molecular weight."""
        props = SolidPropellantPropertiesFactory.build(
            molecular_weight_chamber=molecular_weight_chamber
        )

        assert abs(props.R_chamber - expected_R_chamber) < 1e-9

    @pytest.mark.parametrize(
        "molecular_weight_exhaust,expected_R_exhaust",
        [
            (0.041, scipy.constants.R / 0.041),
            (0.021, scipy.constants.R / 0.021),
            (0.031, scipy.constants.R / 0.031),
        ],
    )
    def test_R_exhaust_calculation(self, molecular_weight_exhaust, expected_R_exhaust):
        """Test that R_exhaust is correctly calculated from molecular weight."""
        props = SolidPropellantPropertiesFactory.build(
            molecular_weight_exhaust=molecular_weight_exhaust
        )

        assert abs(props.R_exhaust - expected_R_exhaust) < 1e-9

    def test_R_properties_are_readonly(self):
        """Test that R_chamber and R_exhaust cannot be set directly."""
        props = SolidPropellantPropertiesFactory.build()

        with pytest.raises(AttributeError):
            props.R_chamber = 100.0

        with pytest.raises(AttributeError):
            props.R_exhaust = 100.0


class TestPropertyValidation:
    """Test suite for validating property value relationships."""

    @pytest.mark.parametrize(
        "props_factory",
        [
            SolidPropellantPropertiesFactory,
            LiquidPropellantPropertiesFactory,
        ],
    )
    def test_shifting_isp_greater_than_or_equal_frozen(self, props_factory):
        """Test that shifting equilibrium Isp is >= frozen Isp."""
        props = props_factory.build()

        assert props.i_sp_shifting >= props.i_sp_frozen

    @pytest.mark.parametrize(
        "props_factory",
        [
            SolidPropellantPropertiesFactory,
            LiquidPropellantPropertiesFactory,
        ],
    )
    def test_effective_temperature_less_than_or_equal_ideal(self, props_factory):
        """Test that effective temperature is <= ideal temperature."""
        props = props_factory.build()

        assert (
            props.adiabatic_flame_temperature <= props.adiabatic_flame_temperature_ideal
        )

    @pytest.mark.parametrize(
        "props_factory",
        [
            SolidPropellantPropertiesFactory,
            LiquidPropellantPropertiesFactory,
        ],
    )
    def test_gamma_values_in_valid_range(self, props_factory):
        """Test that gamma values are in typical range for combustion gases."""
        props = props_factory.build()

        assert 1.0 < props.gamma_chamber < 1.7
        assert 1.0 < props.gamma_exhaust < 1.7

    @pytest.mark.parametrize(
        "props_factory",
        [
            SolidPropellantPropertiesFactory,
            LiquidPropellantPropertiesFactory,
        ],
    )
    def test_molecular_weights_positive(self, props_factory):
        """Test that molecular weights are positive."""
        props = props_factory.build()

        assert props.molecular_weight_chamber > 0
        assert props.molecular_weight_exhaust > 0

    @pytest.mark.parametrize(
        "props_factory",
        [
            SolidPropellantPropertiesFactory,
            LiquidPropellantPropertiesFactory,
        ],
    )
    def test_temperatures_positive(self, props_factory):
        """Test that temperatures are positive."""
        props = props_factory.build()

        assert props.adiabatic_flame_temperature > 0
        assert props.adiabatic_flame_temperature_ideal > 0

    @pytest.mark.parametrize(
        "props_factory",
        [
            SolidPropellantPropertiesFactory,
            LiquidPropellantPropertiesFactory,
        ],
    )
    def test_specific_impulse_positive(self, props_factory):
        """Test that specific impulse values are positive."""
        props = props_factory.build()

        assert props.i_sp_frozen > 0
        assert props.i_sp_shifting > 0


class TestSolidSpecificValidation:
    """Test suite for solid propellant specific validations."""

    def test_density_positive(self):
        """Test that density is positive."""
        props = SolidPropellantPropertiesFactory.build()

        assert props.density > 0

    def test_qsi_values_non_negative(self):
        """Test that qsi values are non-negative."""
        props = SolidPropellantPropertiesFactory.build()

        assert props.qsi_chamber >= 0
        assert props.qsi_exhaust >= 0


class TestLiquidSpecificValidation:
    """Test suite for liquid propellant specific validations."""

    def test_tank_densities_positive(self):
        """Test that tank densities are positive."""
        props = LiquidPropellantPropertiesFactory.build()

        assert props.oxidizer_tank_density > 0
        assert props.fuel_tank_density > 0
