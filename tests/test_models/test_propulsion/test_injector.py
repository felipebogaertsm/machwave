import pytest

import machwave.models.feed_systems.tank as tank_models
from machwave.models.thrust_chamber import MassFlowModel
from tests.factories import BipropellantInjectorFactory


@pytest.fixture
def injector():
    return BipropellantInjectorFactory.build()


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
        inj = BipropellantInjectorFactory.build(
            discharge_coefficient_fuel=0.40,
            discharge_coefficient_oxidizer=0.65,
            area_fuel=5e-6,
            area_ox=1e-5,
        )
        assert inj.discharge_coefficient_fuel != inj.discharge_coefficient_oxidizer

    def test_different_areas(self):
        """Fuel and oxidizer orifice areas are independently configurable."""
        inj = BipropellantInjectorFactory.build(area_fuel=5e-6, area_ox=2e-5)
        assert inj.area_fuel != inj.area_ox

    def test_default_mass_flow_model_is_spi(self, injector):
        assert injector.mass_flow_model_fuel is MassFlowModel.SPI
        assert injector.mass_flow_model_oxidizer is MassFlowModel.SPI

    def test_per_side_mass_flow_model_overrides(self):
        """Mass flow models are configurable independently per side."""
        inj = BipropellantInjectorFactory.build(
            mass_flow_model_fuel=MassFlowModel.SPI,
            mass_flow_model_oxidizer=MassFlowModel.HEM,
        )
        assert inj.mass_flow_model_fuel is MassFlowModel.SPI
        assert inj.mass_flow_model_oxidizer is MassFlowModel.HEM

    def test_invalid_mass_flow_model_raises_value_error(self):
        with pytest.raises(ValueError, match="not a valid MassFlowModel"):
            BipropellantInjectorFactory.build(mass_flow_model_fuel="foo")


class TestBipropellantInjectorMassFlow:
    def test_hem_predicts_lower_oxidizer_flow_than_spi_for_saturated_n2o(self):
        """For saturated N2O, HEM under-predicts SPI."""
        oxidizer_mass = 5.0
        oxidizer_tank = tank_models.Tank(
            fluid_name="N2O",
            volume=0.01,
            temperature=293.0,
            initial_fluid_mass=oxidizer_mass,
        )
        kwargs = dict(
            tank=oxidizer_tank,
            pressure_upstream=oxidizer_tank.get_pressure(oxidizer_mass),
            chamber_pressure=20e5,
            fluid_mass=oxidizer_mass,
        )
        injector_spi = BipropellantInjectorFactory.build(
            mass_flow_model_oxidizer=MassFlowModel.SPI,
        )
        injector_hem = BipropellantInjectorFactory.build(
            mass_flow_model_oxidizer=MassFlowModel.HEM,
        )

        flow_spi = injector_spi.get_mass_flow_ox(**kwargs)
        flow_hem = injector_hem.get_mass_flow_ox(**kwargs)

        assert flow_hem < flow_spi

    def test_spi_dispatch_returns_positive_flow(self):
        oxidizer_mass = 5.0
        oxidizer_tank = tank_models.Tank(
            fluid_name="N2O",
            volume=0.01,
            temperature=293.0,
            initial_fluid_mass=oxidizer_mass,
        )
        injector = BipropellantInjectorFactory.build()
        flow = injector.get_mass_flow_ox(
            tank=oxidizer_tank,
            pressure_upstream=oxidizer_tank.get_pressure(oxidizer_mass),
            chamber_pressure=20e5,
            fluid_mass=oxidizer_mass,
        )
        assert flow > 0.0

    def test_spi_dispatch_matches_core_orifice_helper(self):
        """SPI dispatch equals `Cd * A * sqrt(2 * rho * dP)` from the core helper."""
        import machwave.core.incompressible_flow as incompressible_flow

        oxidizer_mass = 5.0
        oxidizer_tank = tank_models.Tank(
            fluid_name="N2O",
            volume=0.01,
            temperature=293.0,
            initial_fluid_mass=oxidizer_mass,
        )
        injector = BipropellantInjectorFactory.build(
            mass_flow_model_oxidizer=MassFlowModel.SPI,
        )
        pressure_upstream = oxidizer_tank.get_pressure(oxidizer_mass)
        chamber_pressure = 20e5

        actual = injector.get_mass_flow_ox(
            tank=oxidizer_tank,
            pressure_upstream=pressure_upstream,
            chamber_pressure=chamber_pressure,
            fluid_mass=oxidizer_mass,
        )
        expected = incompressible_flow.get_mass_flow_orifice(
            discharge_coefficient=injector.discharge_coefficient_oxidizer,
            area=injector.area_ox,
            density=oxidizer_tank.get_density(oxidizer_mass),
            pressure_upstream=pressure_upstream,
            pressure_downstream=chamber_pressure,
        )
        assert actual == pytest.approx(expected)

    def test_hem_dispatch_matches_two_phase_helper_times_cd_and_area(self):
        """HEM dispatch equals `Cd * A * G_HEM` from the core helper."""
        import machwave.core.two_phase_flow as two_phase_flow

        oxidizer_mass = 5.0
        oxidizer_tank = tank_models.Tank(
            fluid_name="N2O",
            volume=0.01,
            temperature=293.0,
            initial_fluid_mass=oxidizer_mass,
        )
        injector = BipropellantInjectorFactory.build(
            mass_flow_model_oxidizer=MassFlowModel.HEM,
        )
        pressure_upstream = oxidizer_tank.get_pressure(oxidizer_mass)
        chamber_pressure = 20e5

        actual = injector.get_mass_flow_ox(
            tank=oxidizer_tank,
            pressure_upstream=pressure_upstream,
            chamber_pressure=chamber_pressure,
            fluid_mass=oxidizer_mass,
        )
        mass_flux = two_phase_flow.get_homogeneous_equilibrium_mass_flux(
            fluid_name=oxidizer_tank.fluid_name,
            temperature_upstream=oxidizer_tank.temperature,
            pressure_downstream=chamber_pressure,
            pressure_upstream=pressure_upstream,
        )
        expected = (
            injector.discharge_coefficient_oxidizer * injector.area_ox * mass_flux
        )
        assert actual == pytest.approx(expected)

    def test_fuel_side_dispatch_uses_fuel_attributes(self):
        """Fuel dispatch uses fuel-side Cd, area, and model — not the ox-side ones."""
        fuel_mass = 2.0
        fuel_tank = tank_models.Tank(
            fluid_name="Ethanol",
            volume=0.005,
            temperature=298.0,
            initial_fluid_mass=fuel_mass,
        )
        injector = BipropellantInjectorFactory.build(
            discharge_coefficient_fuel=0.40,
            discharge_coefficient_oxidizer=0.80,
            area_fuel=5.0e-6,
            area_ox=2.0e-5,
            mass_flow_model_fuel=MassFlowModel.SPI,
            mass_flow_model_oxidizer=MassFlowModel.HEM,
        )
        pressure_upstream = 30e5
        chamber_pressure = 20e5

        flow = injector.get_mass_flow_fuel(
            tank=fuel_tank,
            pressure_upstream=pressure_upstream,
            chamber_pressure=chamber_pressure,
            fluid_mass=fuel_mass,
        )

        import machwave.core.incompressible_flow as incompressible_flow

        expected = incompressible_flow.get_mass_flow_orifice(
            discharge_coefficient=0.40,
            area=5.0e-6,
            density=fuel_tank.get_density(fuel_mass),
            pressure_upstream=pressure_upstream,
            pressure_downstream=chamber_pressure,
        )
        assert flow == pytest.approx(expected)
