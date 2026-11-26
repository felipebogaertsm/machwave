import math

import pytest

import machwave.core.incompressible_flow as incompressible_flow
import machwave.core.two_phase_flow as two_phase_flow
import machwave.models.thrust_chamber as thrust_chamber_models
import machwave.services.coolprop as coolprop_service
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


class TestInjectorElementSaturatedInletFluxMaximum:
    def test_a_given_maximum_leaves_the_flow_unchanged(
        self, saturated_nitrous_oxide_inlet
    ):
        element = InjectorElementFactory.build()
        inlet = FluidStateFactory.build(
            fluid_name="N2O",
            pressure=0.9 * saturated_nitrous_oxide_inlet.pressure,
            temperature=saturated_nitrous_oxide_inlet.temperature,
            density=saturated_nitrous_oxide_inlet.density,
        )
        chamber_pressure = 20e5

        maximum = element.get_saturated_inlet_flux_maximum(
            fluid_name="N2O",
            temperature=inlet.temperature,
            chamber_pressure=chamber_pressure,
        )

        assert maximum == two_phase_flow.get_saturated_inlet_flux_maximum(
            "N2O", inlet.temperature, chamber_pressure
        )
        assert element.get_mass_flow(
            inlet=inlet,
            chamber_pressure=chamber_pressure,
            saturated_inlet_flux_maximum=maximum,
        ) == element.get_mass_flow(inlet=inlet, chamber_pressure=chamber_pressure)

    @pytest.mark.parametrize(
        "non_equilibrium_factor,temperature,chamber_pressure",
        [
            # no equilibrium term
            (math.inf, 293.0, 20e5),
            # supercritical
            (1.0, 315.0, 20e5),
            # chamber above the saturation pressure at 293 K, about 50.6 bar
            (1.0, 293.0, 60e5),
        ],
    )
    def test_none_where_no_inlet_can_flash_in_equilibrium(
        self, non_equilibrium_factor, temperature, chamber_pressure
    ):
        element = InjectorElementFactory.build(
            non_equilibrium_factor=non_equilibrium_factor
        )

        assert (
            element.get_saturated_inlet_flux_maximum(
                fluid_name="N2O",
                temperature=temperature,
                chamber_pressure=chamber_pressure,
            )
            is None
        )


class TestInjectorElementVaporPressure:
    @pytest.mark.parametrize(
        "inlet_pressure,chamber_pressure",
        [
            # nitrous oxide flashes in the orifice
            (45e5, 20e5),
            # chamber above the saturation pressure at 293 K, about 50.6 bar
            (70e5, 60e5),
        ],
    )
    def test_a_given_vapor_pressure_leaves_the_flow_unchanged(
        self, inlet_pressure, chamber_pressure
    ):
        element = InjectorElementFactory.build()
        inlet = FluidStateFactory.build(
            fluid_name="N2O", pressure=inlet_pressure, temperature=293.0, density=780.0
        )

        vapor_pressure = element.get_vapor_pressure(
            fluid_name="N2O", temperature=inlet.temperature
        )

        assert vapor_pressure == coolprop_service.CoolPropService(
            "N2O"
        ).get_saturation_pressure(inlet.temperature)
        assert element.get_mass_flow(
            inlet=inlet,
            chamber_pressure=chamber_pressure,
            vapor_pressure=vapor_pressure,
        ) == element.get_mass_flow(inlet=inlet, chamber_pressure=chamber_pressure)

    @pytest.mark.parametrize(
        "non_equilibrium_factor,temperature",
        [
            # no equilibrium term
            (math.inf, 293.0),
            # supercritical
            (1.0, 315.0),
        ],
    )
    def test_none_where_the_flow_needs_no_vapor_pressure(
        self, non_equilibrium_factor, temperature
    ):
        element = InjectorElementFactory.build(
            non_equilibrium_factor=non_equilibrium_factor
        )

        assert (
            element.get_vapor_pressure(fluid_name="N2O", temperature=temperature)
            is None
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

    def test_given_vapor_pressures_leave_every_flow_unchanged(
        self, injector, saturated_nitrous_oxide_inlet
    ):
        inlet_states = {
            "oxidizer": saturated_nitrous_oxide_inlet,
            "fuel": FluidStateFactory.build(
                fluid_name="Ethanol", pressure=30e5, temperature=298.0, density=785.0
            ),
        }
        chamber_pressure = 20e5
        vapor_pressures = {
            name: injector.elements[name].get_vapor_pressure(
                fluid_name=inlet.fluid_name, temperature=inlet.temperature
            )
            for name, inlet in inlet_states.items()
        }

        assert injector.get_mass_flows(
            inlet_states=inlet_states,
            chamber_pressure=chamber_pressure,
            vapor_pressures=vapor_pressures,
        ) == injector.get_mass_flows(
            inlet_states=inlet_states, chamber_pressure=chamber_pressure
        )

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
            thrust_chamber_models.Injector(elements={})
