import math

import pytest

import machwave.core.incompressible_flow as incompressible_flow
import machwave.core.two_phase_flow as two_phase_flow
import machwave.services.coolprop as coolprop_service
from machwave.models.thrust_chamber import Injector
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


def get_incompressible_mass_flow(element, inlet, chamber_pressure):
    return incompressible_flow.get_mass_flow_orifice(
        discharge_coefficient=element.discharge_coefficient,
        area=element.area,
        density=inlet.density,
        pressure_upstream=inlet.pressure,
        pressure_downstream=chamber_pressure,
    )


class TestInjectorElementInstantiation:
    def test_stores_the_discharge_coefficient_and_the_area(self):
        element = InjectorElementFactory.build(discharge_coefficient=0.65, area=2e-5)

        assert element.discharge_coefficient == pytest.approx(0.65)
        assert element.area == pytest.approx(2e-5)

    def test_the_default_non_equilibrium_factor_is_one(self):
        assert InjectorElementFactory.build().non_equilibrium_factor == 1.0

    @pytest.mark.parametrize("non_equilibrium_factor", [0.0, -1.0, math.nan])
    def test_rejects_a_non_positive_non_equilibrium_factor(
        self, non_equilibrium_factor
    ):
        with pytest.raises(ValueError, match="non_equilibrium_factor"):
            InjectorElementFactory.build(non_equilibrium_factor=non_equilibrium_factor)

    @pytest.mark.parametrize("area", [0.0, -1e-6])
    def test_rejects_a_non_positive_area(self, area):
        with pytest.raises(ValueError, match="area"):
            InjectorElementFactory.build(area=area)

    @pytest.mark.parametrize("discharge_coefficient", [0.0, -0.1, 1.2])
    def test_rejects_a_discharge_coefficient_out_of_range(self, discharge_coefficient):
        with pytest.raises(ValueError, match="discharge_coefficient"):
            InjectorElementFactory.build(discharge_coefficient=discharge_coefficient)


class TestInjectorElementMassFlow:
    def test_matches_the_dyer_flux_times_discharge_and_area(
        self, saturated_nitrous_oxide_inlet
    ):
        inlet = saturated_nitrous_oxide_inlet
        element = InjectorElementFactory.build(non_equilibrium_factor=0.7)
        chamber_pressure = 20e5

        actual = element.get_mass_flow(inlet=inlet, chamber_pressure=chamber_pressure)

        mass_flux = two_phase_flow.get_dyer_mass_flux(
            fluid_name=inlet.fluid_name,
            temperature_upstream=inlet.temperature,
            density_upstream=inlet.density,
            pressure_upstream=inlet.pressure,
            pressure_downstream=chamber_pressure,
            non_equilibrium_factor=0.7,
        )
        assert actual == pytest.approx(
            element.discharge_coefficient * element.area * mass_flux
        )

    def test_a_liquid_above_its_vapor_pressure_flows_the_incompressible_orifice_flow(
        self,
    ):
        inlet = FluidStateFactory.build(
            fluid_name="Ethanol", pressure=30e5, temperature=298.0, density=785.0
        )
        element = InjectorElementFactory.build()
        chamber_pressure = 20e5

        actual = element.get_mass_flow(inlet=inlet, chamber_pressure=chamber_pressure)

        assert actual == pytest.approx(
            get_incompressible_mass_flow(element, inlet, chamber_pressure)
        )

    def test_a_larger_non_equilibrium_factor_flows_more_saturated_nitrous_oxide(
        self, saturated_nitrous_oxide_inlet
    ):
        kwargs = dict(inlet=saturated_nitrous_oxide_inlet, chamber_pressure=20e5)
        flows = [
            InjectorElementFactory.build(non_equilibrium_factor=factor).get_mass_flow(
                **kwargs
            )
            for factor in (0.5, 1.0, 4.0, math.inf)
        ]

        assert 0.0 < flows[0] < flows[1] < flows[2] < flows[3]
        assert flows[3] == pytest.approx(
            get_incompressible_mass_flow(InjectorElementFactory.build(), **kwargs)
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
                    discharge_coefficient=0.80, area=2.0e-5
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
