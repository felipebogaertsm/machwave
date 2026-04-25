import pytest

from machwave.models.thrust_chamber.injector import BipropellantInjector


@pytest.fixture
def injector():
    return BipropellantInjector(
        discharge_coefficient_fuel=0.48,
        discharge_coefficient_oxidizer=0.48,
        area_fuel=8.2e-6 / 0.48,
        area_ox=1.4e-5 / 0.48,
    )


class TestBipropellantInjectorInstantiation:
    def test_stores_discharge_coefficients(self, injector):
        assert injector.discharge_coefficient_fuel == pytest.approx(0.48)
        assert injector.discharge_coefficient_oxidizer == pytest.approx(0.48)

    def test_stores_areas(self, injector):
        assert injector.area_fuel == pytest.approx(1.70833333333e-5, rel=1e-9)
        assert injector.area_ox == pytest.approx(2.91666666667e-5, rel=1e-9)

    def test_areas_are_positive(self, injector):
        assert injector.area_fuel > 0
        assert injector.area_ox > 0

    def test_asymmetric_discharge_coefficients(self):
        """Fuel and oxidizer sides may have different Cd values."""
        inj = BipropellantInjector(
            discharge_coefficient_fuel=0.40,
            discharge_coefficient_oxidizer=0.65,
            area_fuel=5e-6,
            area_ox=1e-5,
        )
        assert inj.discharge_coefficient_fuel != inj.discharge_coefficient_oxidizer

    def test_different_areas(self):
        """Fuel and oxidizer orifice areas are independently configurable."""
        inj = BipropellantInjector(
            discharge_coefficient_fuel=0.48,
            discharge_coefficient_oxidizer=0.48,
            area_fuel=5e-6,
            area_ox=2e-5,
        )
        assert inj.area_fuel != inj.area_ox
