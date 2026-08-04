import pytest

import machwave.core.incompressible_flow as incompressible_flow
import machwave.core.two_phase_flow as two_phase_flow
import machwave.services.coolprop as coolprop_service
from machwave.models.thrust_chamber import MassFlowModel
from tests.factories import BipropellantInjectorFactory, InjectorInletStateFactory


@pytest.fixture
def injector():
    return BipropellantInjectorFactory.build()


@pytest.fixture
def saturated_nitrous_oxide_inlet():
    """Nitrous oxide at the saturated liquid state, as a tank would deliver it."""
    coolprop = coolprop_service.CoolPropService("N2O")
    temperature = 293.0
    return InjectorInletStateFactory.build(
        fluid_name="N2O",
        pressure=coolprop.get_saturation_pressure(temperature),
        temperature=temperature,
        density=coolprop.get_saturated_liquid_density(temperature),
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


class TestBipropellantInjectorValidation:
    @pytest.mark.parametrize("area_fuel", [0.0, -1e-6])
    def test_non_positive_fuel_area(self, area_fuel):
        with pytest.raises(ValueError, match="area_fuel"):
            BipropellantInjectorFactory.build(area_fuel=area_fuel)

    @pytest.mark.parametrize("area_ox", [0.0, -1e-6])
    def test_non_positive_oxidizer_area(self, area_ox):
        with pytest.raises(ValueError, match="area_ox"):
            BipropellantInjectorFactory.build(area_ox=area_ox)

    @pytest.mark.parametrize("discharge_coefficient_fuel", [0.0, -0.1, 1.2])
    def test_fuel_discharge_coefficient_out_of_range(self, discharge_coefficient_fuel):
        with pytest.raises(ValueError, match="discharge_coefficient_fuel"):
            BipropellantInjectorFactory.build(
                discharge_coefficient_fuel=discharge_coefficient_fuel
            )

    @pytest.mark.parametrize("discharge_coefficient_oxidizer", [0.0, -0.1, 1.2])
    def test_oxidizer_discharge_coefficient_out_of_range(
        self, discharge_coefficient_oxidizer
    ):
        with pytest.raises(ValueError, match="discharge_coefficient_oxidizer"):
            BipropellantInjectorFactory.build(
                discharge_coefficient_oxidizer=discharge_coefficient_oxidizer
            )


class TestBipropellantInjectorMassFlow:
    def test_hem_predicts_lower_oxidizer_flow_than_spi_for_saturated_n2o(
        self, saturated_nitrous_oxide_inlet
    ):
        """For saturated N2O, HEM under-predicts SPI."""
        kwargs = dict(inlet=saturated_nitrous_oxide_inlet, chamber_pressure=20e5)
        injector_spi = BipropellantInjectorFactory.build(
            mass_flow_model_oxidizer=MassFlowModel.SPI,
        )
        injector_hem = BipropellantInjectorFactory.build(
            mass_flow_model_oxidizer=MassFlowModel.HEM,
        )

        flow_spi = injector_spi.get_mass_flow_ox(**kwargs)
        flow_hem = injector_hem.get_mass_flow_ox(**kwargs)

        assert flow_hem < flow_spi

    def test_spi_dispatch_returns_positive_flow(self, saturated_nitrous_oxide_inlet):
        injector = BipropellantInjectorFactory.build()
        flow = injector.get_mass_flow_ox(
            inlet=saturated_nitrous_oxide_inlet,
            chamber_pressure=20e5,
        )
        assert flow > 0.0

    def test_spi_dispatch_matches_core_orifice_helper(self):
        """SPI dispatch equals `Cd * A * sqrt(2 * rho * dP)` from the core helper."""
        inlet = InjectorInletStateFactory.build()
        injector = BipropellantInjectorFactory.build(
            mass_flow_model_oxidizer=MassFlowModel.SPI,
        )
        chamber_pressure = 20e5

        actual = injector.get_mass_flow_ox(
            inlet=inlet,
            chamber_pressure=chamber_pressure,
        )
        expected = incompressible_flow.get_mass_flow_orifice(
            discharge_coefficient=injector.discharge_coefficient_oxidizer,
            area=injector.area_ox,
            density=inlet.density,
            pressure_upstream=inlet.pressure,
            pressure_downstream=chamber_pressure,
        )
        assert actual == pytest.approx(expected)

    def test_hem_dispatch_matches_two_phase_helper_times_cd_and_area(
        self, saturated_nitrous_oxide_inlet
    ):
        """HEM dispatch equals `Cd * A * G_HEM` from the core helper."""
        inlet = saturated_nitrous_oxide_inlet
        injector = BipropellantInjectorFactory.build(
            mass_flow_model_oxidizer=MassFlowModel.HEM,
        )
        chamber_pressure = 20e5

        actual = injector.get_mass_flow_ox(
            inlet=inlet,
            chamber_pressure=chamber_pressure,
        )
        mass_flux = two_phase_flow.get_homogeneous_equilibrium_mass_flux(
            fluid_name=inlet.fluid_name,
            temperature_upstream=inlet.temperature,
            pressure_downstream=chamber_pressure,
            pressure_upstream=inlet.pressure,
        )
        expected = (
            injector.discharge_coefficient_oxidizer * injector.area_ox * mass_flux
        )
        assert actual == pytest.approx(expected)

    def test_fuel_side_dispatch_uses_fuel_attributes(self):
        """Fuel dispatch uses fuel-side Cd, area, and model — not the ox-side ones."""
        inlet = InjectorInletStateFactory.build(
            fluid_name="Ethanol",
            pressure=30e5,
            temperature=298.0,
            density=785.0,
        )
        injector = BipropellantInjectorFactory.build(
            discharge_coefficient_fuel=0.40,
            discharge_coefficient_oxidizer=0.80,
            area_fuel=5.0e-6,
            area_ox=2.0e-5,
            mass_flow_model_fuel=MassFlowModel.SPI,
            mass_flow_model_oxidizer=MassFlowModel.HEM,
        )
        chamber_pressure = 20e5

        flow = injector.get_mass_flow_fuel(
            inlet=inlet,
            chamber_pressure=chamber_pressure,
        )

        expected = incompressible_flow.get_mass_flow_orifice(
            discharge_coefficient=0.40,
            area=5.0e-6,
            density=inlet.density,
            pressure_upstream=inlet.pressure,
            pressure_downstream=chamber_pressure,
        )
        assert flow == pytest.approx(expected)
