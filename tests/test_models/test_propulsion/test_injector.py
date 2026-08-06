import pytest

import machwave.core.incompressible_flow as incompressible_flow
import machwave.core.two_phase_flow as two_phase_flow
import machwave.services.coolprop as coolprop_service
from machwave.models.thrust_chamber import Injector, MassFlowModel
from tests.factories import (
    FluidStateFactory,
    InjectorElementFactory,
    InjectorFactory,
)


@pytest.fixture
def injector():
    return InjectorFactory.build()


@pytest.fixture
def saturated_nitrous_oxide_inlet():
    """Nitrous oxide at the saturated liquid state, as a tank would deliver it."""
    coolprop = coolprop_service.CoolPropService("N2O")
    temperature = 293.0
    return FluidStateFactory.build(
        fluid_name="N2O",
        pressure=coolprop.get_saturation_pressure(temperature),
        temperature=temperature,
        density=coolprop.get_saturated_liquid_density(temperature),
    )


class TestInjectorElementInstantiation:
    def test_stores_the_discharge_coefficient_and_the_area(self):
        element = InjectorElementFactory.build(discharge_coefficient=0.65, area=2e-5)

        assert element.discharge_coefficient == pytest.approx(0.65)
        assert element.area == pytest.approx(2e-5)

    def test_default_mass_flow_model_is_spi(self):
        assert InjectorElementFactory.build().mass_flow_model is MassFlowModel.SPI

    def test_coerces_the_mass_flow_model_from_its_value(self):
        element = InjectorElementFactory.build(mass_flow_model="hem")

        assert element.mass_flow_model is MassFlowModel.HEM

    def test_rejects_an_unknown_mass_flow_model(self):
        with pytest.raises(ValueError, match="not a valid MassFlowModel"):
            InjectorElementFactory.build(mass_flow_model="foo")

    @pytest.mark.parametrize("area", [0.0, -1e-6])
    def test_rejects_a_non_positive_area(self, area):
        with pytest.raises(ValueError, match="area"):
            InjectorElementFactory.build(area=area)

    @pytest.mark.parametrize("discharge_coefficient", [0.0, -0.1, 1.2])
    def test_rejects_a_discharge_coefficient_out_of_range(self, discharge_coefficient):
        with pytest.raises(ValueError, match="discharge_coefficient"):
            InjectorElementFactory.build(discharge_coefficient=discharge_coefficient)


class TestInjectorElementMassFlow:
    def test_hem_predicts_lower_flow_than_spi_for_saturated_nitrous_oxide(
        self, saturated_nitrous_oxide_inlet
    ):
        """For saturated N2O, HEM under-predicts SPI."""
        kwargs = dict(inlet=saturated_nitrous_oxide_inlet, chamber_pressure=20e5)
        element_spi = InjectorElementFactory.build(mass_flow_model=MassFlowModel.SPI)
        element_hem = InjectorElementFactory.build(mass_flow_model=MassFlowModel.HEM)

        assert element_hem.get_mass_flow(**kwargs) < element_spi.get_mass_flow(**kwargs)

    def test_spi_dispatch_returns_positive_flow(self, saturated_nitrous_oxide_inlet):
        element = InjectorElementFactory.build()

        flow = element.get_mass_flow(
            inlet=saturated_nitrous_oxide_inlet, chamber_pressure=20e5
        )

        assert flow > 0.0

    def test_spi_dispatch_matches_core_orifice_helper(self):
        """SPI dispatch equals `Cd * A * sqrt(2 * rho * dP)` from the core helper."""
        inlet = FluidStateFactory.build()
        element = InjectorElementFactory.build(mass_flow_model=MassFlowModel.SPI)
        chamber_pressure = 20e5

        actual = element.get_mass_flow(inlet=inlet, chamber_pressure=chamber_pressure)

        assert actual == pytest.approx(
            incompressible_flow.get_mass_flow_orifice(
                discharge_coefficient=element.discharge_coefficient,
                area=element.area,
                density=inlet.density,
                pressure_upstream=inlet.pressure,
                pressure_downstream=chamber_pressure,
            )
        )

    def test_hem_dispatch_matches_two_phase_helper_times_discharge_and_area(
        self, saturated_nitrous_oxide_inlet
    ):
        """HEM dispatch equals `Cd * A * G_HEM` from the core helper."""
        inlet = saturated_nitrous_oxide_inlet
        element = InjectorElementFactory.build(mass_flow_model=MassFlowModel.HEM)
        chamber_pressure = 20e5

        actual = element.get_mass_flow(inlet=inlet, chamber_pressure=chamber_pressure)

        mass_flux = two_phase_flow.get_homogeneous_equilibrium_mass_flux(
            fluid_name=inlet.fluid_name,
            temperature_upstream=inlet.temperature,
            pressure_downstream=chamber_pressure,
            pressure_upstream=inlet.pressure,
        )
        assert actual == pytest.approx(
            element.discharge_coefficient * element.area * mass_flux
        )

    @pytest.mark.parametrize("chamber_pressure", [30e5, 40e5])
    def test_a_chamber_at_or_above_the_inlet_stops_the_flow(self, chamber_pressure):
        inlet = FluidStateFactory.build(pressure=30e5)
        element = InjectorElementFactory.build()

        assert (
            element.get_mass_flow(inlet=inlet, chamber_pressure=chamber_pressure) == 0.0
        )


class TestInjectorMassFlows:
    def test_every_element_gets_a_flow_in_one_call(self, injector):
        inlet_states = {
            "oxidizer": FluidStateFactory.build(pressure=40e5),
            "fuel": FluidStateFactory.build(pressure=35e5),
        }

        flows = injector.get_mass_flows(
            inlet_states=inlet_states, chamber_pressure=20e5
        )

        assert set(flows) == {"oxidizer", "fuel"}
        assert all(flow > 0.0 for flow in flows.values())

    def test_each_element_flows_on_its_own_inlet(self):
        """One line's element and inlet decide its flow, not another line's."""
        injector = InjectorFactory.build(
            elements={
                "oxidizer": InjectorElementFactory.build(
                    discharge_coefficient=0.80,
                    area=2.0e-5,
                    mass_flow_model=MassFlowModel.HEM,
                ),
                "fuel": InjectorElementFactory.build(
                    discharge_coefficient=0.40, area=5.0e-6
                ),
            }
        )
        fuel_inlet = FluidStateFactory.build(
            fluid_name="Ethanol", pressure=30e5, temperature=298.0, density=785.0
        )
        chamber_pressure = 20e5

        flows = injector.get_mass_flows(
            inlet_states={
                "oxidizer": FluidStateFactory.build(),
                "fuel": fuel_inlet,
            },
            chamber_pressure=chamber_pressure,
        )

        assert flows["fuel"] == pytest.approx(
            incompressible_flow.get_mass_flow_orifice(
                discharge_coefficient=0.40,
                area=5.0e-6,
                density=fuel_inlet.density,
                pressure_upstream=fuel_inlet.pressure,
                pressure_downstream=chamber_pressure,
            )
        )

    def test_a_third_line_is_one_more_element(self):
        injector = InjectorFactory.build(
            elements={
                "oxidizer": InjectorElementFactory.build(),
                "fuel": InjectorElementFactory.build(),
                "diluent": InjectorElementFactory.build(area=2e-6),
            }
        )

        flows = injector.get_mass_flows(
            inlet_states={
                name: FluidStateFactory.build(pressure=40e5)
                for name in ("oxidizer", "fuel", "diluent")
            },
            chamber_pressure=20e5,
        )

        assert flows["diluent"] < flows["fuel"]

    def test_a_single_element_injector_is_valid(self):
        injector = InjectorFactory.build(
            elements={"oxidizer": InjectorElementFactory.build()}
        )

        flows = injector.get_mass_flows(
            inlet_states={"oxidizer": FluidStateFactory.build()},
            chamber_pressure=20e5,
        )

        assert list(flows) == ["oxidizer"]

    def test_rejects_a_missing_inlet_state(self, injector):
        with pytest.raises(ValueError, match="fuel"):
            injector.get_mass_flows(
                inlet_states={"oxidizer": FluidStateFactory.build()},
                chamber_pressure=20e5,
            )

    def test_rejects_an_injector_without_elements(self):
        with pytest.raises(ValueError, match="at least one"):
            Injector(elements={})
