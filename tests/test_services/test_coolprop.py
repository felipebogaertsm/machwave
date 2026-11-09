"""Tests for CoolPropService."""

import CoolProp.CoolProp as CP
import pytest

import machwave.services.coolprop as coolprop_service

FLUID_NAME = "N2O"
TEMPERATURE = 293.0


@pytest.fixture
def service() -> coolprop_service.CoolPropService:
    return coolprop_service.CoolPropService(FLUID_NAME)


def test_get_triple_point_temperature(service):
    assert service.get_triple_point_temperature() == CP.PropsSI("Ttriple", FLUID_NAME)


def test_get_critical_temperature(service):
    assert service.get_critical_temperature() == CP.PropsSI("Tcrit", FLUID_NAME)


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


@pytest.mark.parametrize(
    "temperature, density",
    [
        (290.0, 500.0),  # inside the dome
        (300.0, 731.58),  # compressed liquid, a 1% overfill
        (290.0, 50.0),  # superheated vapor
    ],
)
def test_a_flash_coolprop_gets_right_is_kept(service, temperature, density):
    internal_energy = CP.PropsSI("U", "T", temperature, "D", density, FLUID_NAME)

    assert service.get_temperature_at_density_internal_energy(
        density, internal_energy
    ) == CP.PropsSI("T", "D", density, "U", internal_energy, FLUID_NAME)
    assert service.get_pressure_at_density_internal_energy(
        density, internal_energy
    ) == CP.PropsSI("P", "D", density, "U", internal_energy, FLUID_NAME)


def test_a_supercritical_state_raises(service):
    density = 454.0
    internal_energy = CP.PropsSI("U", "T", 320.0, "D", density, FLUID_NAME)

    with pytest.raises(ValueError, match="is supercritical at 320"):
        service.get_pressure_at_density_internal_energy(density, internal_energy)


def test_a_state_off_the_chart_raises(service):
    with pytest.raises(ValueError, match="nor on the saturation dome"):
        service.get_temperature_at_density_internal_energy(500.0, -1e12)


class TestAStateTheFlashGetsWrong:
    """CoolProp 6.8 flashes this two-phase N2O state to a single-phase 270.37 K."""

    DENSITY = 454.50072100174214
    INTERNAL_ENERGY = 228590.2487156092
    TEMPERATURE = 291.03099264302705
    QUALITY = 0.17165274259158367

    def test_the_reference_is_the_state_asked_for(self):
        assert CP.PropsSI(
            "D", "T", self.TEMPERATURE, "Q", self.QUALITY, FLUID_NAME
        ) == pytest.approx(self.DENSITY, rel=1e-12)
        assert CP.PropsSI(
            "U", "T", self.TEMPERATURE, "Q", self.QUALITY, FLUID_NAME
        ) == pytest.approx(self.INTERNAL_ENERGY, rel=1e-12)

    def test_the_temperature_is_on_the_dome(self, service):
        # 1e-6 K leaves room for round-off in the reference state
        assert service.get_temperature_at_density_internal_energy(
            self.DENSITY, self.INTERNAL_ENERGY
        ) == pytest.approx(self.TEMPERATURE, abs=1e-6)

    def test_the_pressure_is_the_saturation_pressure(self, service):
        # a 1e-6 K error moves the saturation pressure by about 1e-8 relative
        assert service.get_pressure_at_density_internal_energy(
            self.DENSITY, self.INTERNAL_ENERGY
        ) == pytest.approx(
            CP.PropsSI("P", "T", self.TEMPERATURE, "Q", 0, FLUID_NAME), rel=1e-7
        )


def test_get_molar_mass(service):
    assert service.get_molar_mass() == CP.PropsSI("M", FLUID_NAME)


@pytest.mark.parametrize(
    "pressure_ratio",
    [
        1.0,  # saturated liquid
        0.7,  # two-phase
    ],
)
def test_get_density_and_enthalpy_at_pressure_entropy(service, pressure_ratio):
    """One flash reads the same bits as the two point lookups."""
    pressure = pressure_ratio * service.get_saturation_pressure(TEMPERATURE)
    entropy = service.get_saturated_liquid_entropy(TEMPERATURE)

    assert service.get_density_and_enthalpy_at_pressure_entropy(pressure, entropy) == (
        CP.PropsSI("D", "P", pressure, "S", entropy, FLUID_NAME),
        CP.PropsSI("H", "P", pressure, "S", entropy, FLUID_NAME),
    )


def test_get_density_and_enthalpy_at_pressure_entropy_raises_when_unresolvable(
    service,
):
    with pytest.raises(ValueError, match="unable to solve"):
        service.get_density_and_enthalpy_at_pressure_entropy(-1.0, 0.0)
