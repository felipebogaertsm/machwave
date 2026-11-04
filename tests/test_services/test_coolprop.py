"""Tests for CoolPropService."""

import copy
import pickle

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


class TestStateAtDensityInternalEnergy:
    """One AbstractState flash against the PropsSI calls it replaces."""

    @staticmethod
    def props_reference(density, internal_energy):
        temperature = CP.PropsSI("T", "D", density, "U", internal_energy, FLUID_NAME)
        return dict(
            temperature=temperature,
            pressure=CP.PropsSI("P", "D", density, "U", internal_energy, FLUID_NAME),
            saturated_liquid_density=CP.PropsSI(
                "D", "T", temperature, "Q", 0, FLUID_NAME
            ),
            saturated_vapor_density=CP.PropsSI(
                "D", "T", temperature, "Q", 1, FLUID_NAME
            ),
            saturated_liquid_enthalpy=CP.PropsSI(
                "H", "T", temperature, "Q", 0, FLUID_NAME
            ),
            saturated_vapor_enthalpy=CP.PropsSI(
                "H", "T", temperature, "Q", 1, FLUID_NAME
            ),
            enthalpy=CP.PropsSI("H", "T", temperature, "D", density, FLUID_NAME),
        )

    @pytest.mark.parametrize(
        "temperature, density, is_two_phase",
        [
            (290.0, 500.0, True),  # Inside the dome.
            (300.0, 731.58, False),  # Compressed liquid, a 1% overfill.
            (290.0, 50.0, False),  # Superheated vapor below the vapor fill.
        ],
    )
    def test_matches_props_si(self, service, temperature, density, is_two_phase):
        internal_energy = CP.PropsSI("U", "T", temperature, "D", density, FLUID_NAME)

        state = service.get_state_at_density_internal_energy(density, internal_energy)

        assert state.is_two_phase is is_two_phase
        for name, value in self.props_reference(density, internal_energy).items():
            assert getattr(state, name) == pytest.approx(value, rel=1e-12), name

    def test_a_state_off_the_chart_raises(self, service):
        with pytest.raises(ValueError):
            service.get_state_at_density_internal_energy(500.0, -1e12)

    def test_the_service_survives_a_copy_and_a_pickle(self, service):
        internal_energy = CP.PropsSI("U", "T", 290.0, "D", 500.0, FLUID_NAME)
        expected = service.get_state_at_density_internal_energy(500.0, internal_energy)

        for clone in (copy.deepcopy(service), pickle.loads(pickle.dumps(service))):
            assert (
                clone.get_state_at_density_internal_energy(500.0, internal_energy)
                == expected
            )


class TestAStateTheFlashGetsWrong:
    """
    CoolProp 6.8.0's (D, U) flash puts this N2O state at 270.37 K and 1.45 MPa,
    flagged single-phase. It is two-phase at 291.031 K and 4.814 MPa: the
    saturated mix at that temperature and quality gives back the density and
    internal energy to round-off, which the flashed state does not.
    """

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

    def test_the_service_resolves_it_on_the_dome(self, service):
        state = service.get_state_at_density_internal_energy(
            self.DENSITY, self.INTERNAL_ENERGY
        )

        assert state.is_two_phase
        assert state.temperature == pytest.approx(self.TEMPERATURE, abs=1e-6)
        assert state.pressure == pytest.approx(
            CP.PropsSI("P", "T", self.TEMPERATURE, "Q", 0, FLUID_NAME), rel=1e-9
        )
        assert state.pressure == pytest.approx(4.814e6, rel=1e-3)
        assert service.dome_solve_count == 1

    def test_a_state_the_flash_gets_right_skips_the_dome_solve(self, service):
        internal_energy = CP.PropsSI("U", "T", 290.0, "D", 500.0, FLUID_NAME)

        service.get_state_at_density_internal_energy(500.0, internal_energy)

        assert service.dome_solve_count == 0


def test_get_molar_mass(service):
    assert service.get_molar_mass() == CP.PropsSI("M", FLUID_NAME)
