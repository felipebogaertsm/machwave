"""Tests for propellant properties dataclasses."""

import math

import pytest
import scipy.constants

import machwave.models.propellants.properties as propellant_properties
from tests.factories import (
    LiquidPropellantPropertiesFactory,
    SolidPropellantPropertiesFactory,
)


class TestThermochemicalPropertiesBasics:
    """Test suite for basic ThermochemicalProperties functionality."""

    def test_instantiation_and_immutability(self):
        """Test that properties can be instantiated and are immutable."""
        props = SolidPropellantPropertiesFactory.build()

        assert isinstance(props, propellant_properties.ThermochemicalProperties)

        with pytest.raises(AttributeError):
            props.k_chamber = 1.5


class TestDerivedProperties:
    """Test suite for derived property calculations."""

    def test_R_chamber_calculation(self):
        """Test that R_chamber is correctly calculated using scipy.constants.R."""
        props = SolidPropellantPropertiesFactory.build(molecular_weight_chamber=0.04)
        expected_R = scipy.constants.R / 0.04

        assert math.isclose(props.R_chamber, expected_R, rel_tol=1e-9)

    def test_R_exhaust_calculation(self):
        """Test that R_exhaust is correctly calculated using scipy.constants.R."""
        props = SolidPropellantPropertiesFactory.build(molecular_weight_exhaust=0.041)
        expected_R = scipy.constants.R / 0.041

        assert math.isclose(props.R_exhaust, expected_R, rel_tol=1e-9)


class TestIsTwoPhaseFlow:
    """Test suite for is_two_phase_flow property."""

    def test_nonzero_qsi_is_two_phase(self):
        """Test that propellants with qsi > 0 are two-phase."""
        props = SolidPropellantPropertiesFactory.build(qsi_chamber=0.3)

        assert props.is_two_phase_flow is True

    def test_zero_qsi_is_not_two_phase(self):
        """Test that propellants with qsi = 0 are single-phase."""
        props = LiquidPropellantPropertiesFactory.build()

        assert props.is_two_phase_flow is False


class TestInputValidation:
    """Test suite for input validation using tuple-based bounds."""

    def test_invalid_isentropic_exponent_raises_error(self):
        """Test that isentropic exponent outside valid range raises ValueError."""
        base_data = SolidPropellantPropertiesFactory.build().__dict__
        base_data["k_chamber"] = 0.9  # Below minimum

        with pytest.raises(ValueError, match="outside valid range"):
            propellant_properties.ThermochemicalProperties(**base_data)

    def test_invalid_molecular_weight_raises_error(self):
        """Test that molecular weight outside valid range raises ValueError."""
        base_data = SolidPropellantPropertiesFactory.build().__dict__
        base_data["molecular_weight_chamber"] = 0.0  # At minimum (exclusive)

        with pytest.raises(ValueError, match="outside valid range"):
            propellant_properties.ThermochemicalProperties(**base_data)

    def test_invalid_temperature_raises_error(self):
        """Test that temperature outside valid range raises ValueError."""
        base_data = SolidPropellantPropertiesFactory.build().__dict__
        base_data["adiabatic_flame_temperature"] = -100.0  # Below minimum

        with pytest.raises(ValueError, match="outside valid range"):
            propellant_properties.ThermochemicalProperties(**base_data)

    def test_invalid_isp_raises_error(self):
        """Test that specific impulse outside valid range raises ValueError."""
        base_data = SolidPropellantPropertiesFactory.build().__dict__
        base_data["i_sp_frozen"] = 700.0  # Above maximum

        with pytest.raises(ValueError, match="outside valid range"):
            propellant_properties.ThermochemicalProperties(**base_data)

    def test_invalid_qsi_raises_error(self):
        """Test that qsi outside valid range raises ValueError."""
        base_data = SolidPropellantPropertiesFactory.build().__dict__
        base_data["qsi_chamber"] = 1.5  # Above maximum

        with pytest.raises(ValueError, match="outside valid range"):
            propellant_properties.ThermochemicalProperties(**base_data)

    def test_shifting_less_than_frozen_raises_error(self):
        """Test that i_sp_shifting < i_sp_frozen raises ValueError."""
        base_data = SolidPropellantPropertiesFactory.build().__dict__
        base_data["i_sp_frozen"] = 300.0
        base_data["i_sp_shifting"] = 290.0  # Less than frozen

        with pytest.raises(ValueError, match="must be >="):
            propellant_properties.ThermochemicalProperties(**base_data)


class TestSolidPropellantBehavior:
    """Test suite for solid propellant specific behavior (qsi > 0)."""

    def test_solid_propellant_has_nonzero_qsi(self):
        """Test that solid propellants have qsi > 0 and are two-phase."""
        props = SolidPropellantPropertiesFactory.build()

        assert props.qsi_chamber > 0
        assert props.is_two_phase_flow is True


class TestLiquidPropellantBehavior:
    """Test suite for liquid propellant specific behavior (qsi = 0)."""

    def test_liquid_propellant_has_zero_qsi(self):
        """Test that liquid propellants have qsi = 0 and are single-phase."""
        props = LiquidPropellantPropertiesFactory.build()

        assert props.qsi_chamber == 0.0
        assert props.qsi_exhaust == 0.0
        assert props.is_two_phase_flow is False
