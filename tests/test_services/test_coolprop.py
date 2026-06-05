"""Tests for CoolPropService."""

import CoolProp.CoolProp as CP
import pytest

import machwave.services.coolprop as coolprop_service

FLUID_NAME = "N2O"
TEMPERATURE = 293.0


@pytest.fixture
def service() -> coolprop_service.CoolPropService:
    return coolprop_service.CoolPropService(FLUID_NAME)


def test_get_molar_mass(service):
    assert service.get_molar_mass() == CP.PropsSI("M", FLUID_NAME)


def test_get_saturation_pressure(service):
    assert service.get_saturation_pressure(TEMPERATURE) == CP.PropsSI(
        "P", "T", TEMPERATURE, "Q", 0, FLUID_NAME
    )


def test_get_saturated_liquid_density(service):
    assert service.get_saturated_liquid_density(TEMPERATURE) == CP.PropsSI(
        "D", "T", TEMPERATURE, "Q", 0, FLUID_NAME
    )


def test_get_saturated_liquid_enthalpy(service):
    assert service.get_saturated_liquid_enthalpy(TEMPERATURE) == CP.PropsSI(
        "H", "T", TEMPERATURE, "Q", 0, FLUID_NAME
    )


def test_get_saturated_liquid_entropy(service):
    assert service.get_saturated_liquid_entropy(TEMPERATURE) == CP.PropsSI(
        "S", "T", TEMPERATURE, "Q", 0, FLUID_NAME
    )


def test_get_density_at_temperature_pressure(service):
    pressure = service.get_saturation_pressure(TEMPERATURE) + 5e5
    assert service.get_density_at_temperature_pressure(
        TEMPERATURE, pressure
    ) == CP.PropsSI("D", "T", TEMPERATURE, "P", pressure, FLUID_NAME)


def test_get_enthalpy_at_temperature_pressure(service):
    pressure = service.get_saturation_pressure(TEMPERATURE) + 5e5
    assert service.get_enthalpy_at_temperature_pressure(
        TEMPERATURE, pressure
    ) == CP.PropsSI("H", "T", TEMPERATURE, "P", pressure, FLUID_NAME)


def test_get_entropy_at_temperature_pressure(service):
    pressure = service.get_saturation_pressure(TEMPERATURE) + 5e5
    assert service.get_entropy_at_temperature_pressure(
        TEMPERATURE, pressure
    ) == CP.PropsSI("S", "T", TEMPERATURE, "P", pressure, FLUID_NAME)


def test_get_density_at_pressure_entropy(service):
    pressure = service.get_saturation_pressure(TEMPERATURE)
    entropy = service.get_saturated_liquid_entropy(TEMPERATURE)
    assert service.get_density_at_pressure_entropy(pressure, entropy) == CP.PropsSI(
        "D", "P", pressure, "S", entropy, FLUID_NAME
    )


def test_get_enthalpy_at_pressure_entropy(service):
    pressure = service.get_saturation_pressure(TEMPERATURE)
    entropy = service.get_saturated_liquid_entropy(TEMPERATURE)
    assert service.get_enthalpy_at_pressure_entropy(pressure, entropy) == CP.PropsSI(
        "H", "P", pressure, "S", entropy, FLUID_NAME
    )
