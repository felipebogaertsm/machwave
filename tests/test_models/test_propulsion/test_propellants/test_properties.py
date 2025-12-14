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


class TestChemicalPropellantProperties:
    """Test suite for ChemicalPropellantProperties and common behaviors."""

    @pytest.mark.parametrize(
        "props_factory,props_class",
        [
            (SolidPropellantPropertiesFactory, SolidPropellantProperties),
            (LiquidPropellantPropertiesFactory, LiquidPropellantProperties),
        ],
        ids=["Solid", "Liquid"],
    )
    def test_inheritance(self, props_factory, props_class):
        """Test that properties inherit from ChemicalPropellantProperties."""
        props = props_factory.build()

        assert isinstance(props, ChemicalPropellantProperties)
        assert isinstance(props, props_class)

    @pytest.mark.parametrize(
        "props_factory,props_class",
        [
            (SolidPropellantPropertiesFactory, SolidPropellantProperties),
            (LiquidPropellantPropertiesFactory, LiquidPropellantProperties),
        ],
        ids=["Solid", "Liquid"],
    )
    def test_dataclass_equality(self, props_factory, props_class):
        """Test that dataclass equality works correctly."""
        props1 = props_factory.build()
        props2 = props_factory.build()

        assert props1 == props2

    @pytest.mark.parametrize(
        "props_factory,class_name",
        [
            (SolidPropellantPropertiesFactory, "SolidPropellantProperties"),
            (LiquidPropellantPropertiesFactory, "LiquidPropellantProperties"),
        ],
        ids=["Solid", "Liquid"],
    )
    def test_dataclass_repr(self, props_factory, class_name):
        """Test that dataclass repr includes class name."""
        props = props_factory.build()

        assert class_name in repr(props)

    @pytest.mark.parametrize(
        "props_factory",
        [SolidPropellantPropertiesFactory, LiquidPropellantPropertiesFactory],
        ids=["Solid", "Liquid"],
    )
    def test_dataclass_frozen(self, props_factory):
        """Test that dataclass is immutable (frozen)."""
        props = props_factory.build()

        with pytest.raises(AttributeError):
            props.gamma_chamber = 1.5

    @pytest.mark.parametrize(
        "method",
        ["R_chamber", "R_exhaust"],
    )
    def test_common_derived_properties_exist(self, method):
        """Test that derived properties are available on all subclasses."""
        solid_props = SolidPropellantPropertiesFactory.build()
        liquid_props = LiquidPropellantPropertiesFactory.build()

        assert hasattr(solid_props, method)
        assert hasattr(liquid_props, method)
        assert isinstance(getattr(type(solid_props), method), property)
        assert isinstance(getattr(type(liquid_props), method), property)


class TestSolidPropellantProperties:
    """Test suite for SolidPropellantProperties-specific features."""

    def test_instantiation(self):
        """Test that SolidPropellantProperties can be instantiated."""
        props = SolidPropellantPropertiesFactory.build()

        assert props.gamma_chamber == 1.15
        assert props.qsi_chamber == 0.3

    @pytest.mark.parametrize(
        "field",
        [
            "gamma_chamber",
            "gamma_exhaust",
            "adiabatic_flame_temperature",
            "molecular_weight_chamber",
            "molecular_weight_exhaust",
            "i_sp_frozen",
            "i_sp_shifting",
            "qsi_chamber",
            "qsi_exhaust",
        ],
    )
    def test_required_fields(self, field):
        """Test that all fields are required."""
        props = SolidPropellantPropertiesFactory.build()
        data = {k: v for k, v in props.__dict__.items() if k != field}

        with pytest.raises(TypeError):
            SolidPropellantProperties(**data)

    def test_qsi_values_non_negative(self):
        """Test that qsi values (solid-specific) are non-negative."""
        props = SolidPropellantPropertiesFactory.build()

        assert props.qsi_chamber >= 0
        assert props.qsi_exhaust >= 0


class TestLiquidPropellantProperties:
    """Test suite for LiquidPropellantProperties-specific features."""

    def test_instantiation(self):
        """Test that LiquidPropellantProperties can be instantiated."""
        props = LiquidPropellantPropertiesFactory.build()

        assert props.gamma_chamber == 1.20
        assert props.i_sp_frozen == 300.0
        assert props.i_sp_shifting == 310.0

    @pytest.mark.parametrize(
        "field",
        [
            "gamma_chamber",
            "gamma_exhaust",
            "adiabatic_flame_temperature",
            "molecular_weight_chamber",
            "molecular_weight_exhaust",
            "i_sp_frozen",
            "i_sp_shifting",
        ],
    )
    def test_required_fields(self, field):
        """Test that all fields are required."""
        props = LiquidPropellantPropertiesFactory.build()
        data = {k: v for k, v in props.__dict__.items() if k != field}

        with pytest.raises(TypeError):
            LiquidPropellantProperties(**data)


class TestDerivedProperties:
    """Test suite for derived property calculations."""

    def test_R_chamber_calculation(self):
        """Test that R_chamber is correctly calculated from molecular weight."""
        props = SolidPropellantPropertiesFactory.build(molecular_weight_chamber=0.04)
        expected_R = scipy.constants.R / 0.04

        assert abs(props.R_chamber - expected_R) < 1e-9

    def test_R_exhaust_calculation(self):
        """Test that R_exhaust is correctly calculated from molecular weight."""
        props = SolidPropellantPropertiesFactory.build(molecular_weight_exhaust=0.041)
        expected_R = scipy.constants.R / 0.041

        assert abs(props.R_exhaust - expected_R) < 1e-9

    def test_R_properties_are_readonly(self):
        """Test that derived properties cannot be set directly."""
        props = SolidPropellantPropertiesFactory.build()

        with pytest.raises(AttributeError):
            props.R_chamber = 100.0

        with pytest.raises(AttributeError):
            props.R_exhaust = 100.0


class TestPropertyValidation:
    """Test suite for validating property value relationships and ranges."""

    @pytest.mark.parametrize(
        "props_factory",
        [SolidPropellantPropertiesFactory, LiquidPropellantPropertiesFactory],
        ids=["Solid", "Liquid"],
    )
    def test_shifting_isp_greater_than_or_equal_frozen(self, props_factory):
        """Test that shifting equilibrium Isp is >= frozen Isp."""
        props = props_factory.build()

        assert props.i_sp_shifting >= props.i_sp_frozen

    @pytest.mark.parametrize(
        "props_factory",
        [SolidPropellantPropertiesFactory, LiquidPropellantPropertiesFactory],
        ids=["Solid", "Liquid"],
    )
    def test_gamma_values_in_valid_range(self, props_factory):
        """Test that gamma values are in typical range for combustion gases."""
        props = props_factory.build()

        assert 1.0 < props.gamma_chamber < 1.7
        assert 1.0 < props.gamma_exhaust < 1.7

    @pytest.mark.parametrize(
        "props_factory",
        [SolidPropellantPropertiesFactory, LiquidPropellantPropertiesFactory],
        ids=["Solid", "Liquid"],
    )
    def test_molecular_weights_positive(self, props_factory):
        """Test that molecular weights are positive."""
        props = props_factory.build()

        assert props.molecular_weight_chamber > 0
        assert props.molecular_weight_exhaust > 0

    @pytest.mark.parametrize(
        "props_factory",
        [SolidPropellantPropertiesFactory, LiquidPropellantPropertiesFactory],
        ids=["Solid", "Liquid"],
    )
    def test_temperatures_positive(self, props_factory):
        """Test that temperatures are positive."""
        props = props_factory.build()

        assert props.adiabatic_flame_temperature > 0

    @pytest.mark.parametrize(
        "props_factory",
        [SolidPropellantPropertiesFactory, LiquidPropellantPropertiesFactory],
        ids=["Solid", "Liquid"],
    )
    def test_specific_impulse_positive(self, props_factory):
        """Test that specific impulse values are positive."""
        props = props_factory.build()

        assert props.i_sp_frozen > 0
        assert props.i_sp_shifting > 0


class TestSolidSpecificValidation:
    """Test suite for solid propellant specific validations."""

    def test_qsi_values_non_negative(self):
        """Test that qsi values are non-negative."""
        props = SolidPropellantPropertiesFactory.build()

        assert props.qsi_chamber >= 0
        assert props.qsi_exhaust >= 0


class TestLiquidSpecificValidation:
    """Test suite for liquid propellant specific validations.

    Note: Currently LiquidPropellantProperties has no additional fields beyond
    the base ChemicalPropellantProperties. Tank densities are operational
    properties stored in the BiliquidPropellant class itself.
    """

    def test_no_additional_fields(self):
        """Test that liquid properties currently has only base fields."""
        props = LiquidPropellantPropertiesFactory.build()

        # LiquidPropellantProperties should have the same fields as base class
        assert hasattr(props, "gamma_chamber")
        assert hasattr(props, "i_sp_frozen")
