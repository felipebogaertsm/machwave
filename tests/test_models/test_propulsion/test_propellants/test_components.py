import CoolProp.CoolProp as CP
import pytest

import machwave.models.propellants as propellants_models
import machwave.models.propellants.components as propellant_components

# RocketCEA's "N2O_nbp" card: liquid N2O at its normal boiling point,
# h = 14583.0 cal/mol at 184.4 K. It is an independent route to the liquid
# enthalpy on the CEA scale.
_ROCKETCEA_N2O_NBP_ENTHALPY = 14583.0 * 4.184  # [J/mol]
_ROCKETCEA_N2O_NBP_TEMPERATURE = 184.4  # [K]


def _ethanol() -> propellant_components.PropellantComponent:
    return propellant_components.PropellantComponent(
        name="Ethanol",
        role=propellant_components.ComponentRole.FUEL,
        density=789.0,
        chemical_formula={"C": 2, "H": 6, "O": 1},
        enthalpy=0.0,
    )


def _n2o_ethanol(
    oxidizer: propellant_components.PropellantComponent,
) -> propellants_models.BiliquidPropellant:
    return propellants_models.BiliquidPropellant(
        name="N2O/Ethanol",
        components=[oxidizer, _ethanol()],
        oxidizer_to_fuel_ratio=1.95,
    )


class TestSaturatedLiquidNitrousOxide:
    def test_matches_rocketcea_normal_boiling_point_card(self):
        component = propellants_models.saturated_liquid_nitrous_oxide(
            _ROCKETCEA_N2O_NBP_TEMPERATURE
        )
        assert component.enthalpy == pytest.approx(
            _ROCKETCEA_N2O_NBP_ENTHALPY, abs=200.0
        )

    def test_density_and_state_follow_temperature(self):
        component = propellants_models.saturated_liquid_nitrous_oxide(300.0)
        assert component.density == pytest.approx(
            CP.PropsSI("D", "T", 300.0, "Q", 0, "NitrousOxide")
        )
        assert component.initial_temperature == 300.0
        assert component.chemical_formula == {"N": 2, "O": 1}
        assert component.role == propellant_components.ComponentRole.OXIDIZER
        assert component.custom_card is True

    def test_enthalpy_drops_as_liquid_cools(self):
        warm = propellants_models.saturated_liquid_nitrous_oxide(300.0)
        cold = propellants_models.saturated_liquid_nitrous_oxide(290.0)
        assert cold.enthalpy < warm.enthalpy

    @pytest.mark.parametrize("temperature", [150.0, 309.6, 320.0])
    def test_rejects_temperature_outside_saturation_range(self, temperature):
        with pytest.raises(ValueError, match="saturated-liquid temperature"):
            propellants_models.saturated_liquid_nitrous_oxide(temperature)


class TestBiliquidCustomCard:
    def test_liquid_card_burns_cooler_than_built_in_gas_card(self):
        gas = propellant_components.PropellantComponent(
            name="N2O",
            role=propellant_components.ComponentRole.OXIDIZER,
            density=745.0,
            chemical_formula={"N": 2, "O": 1},
            enthalpy=0.0,
        )
        liquid = propellants_models.saturated_liquid_nitrous_oxide(300.0)

        gas_properties = _n2o_ethanol(gas).evaluate(3.26e6, 4.0)
        liquid_properties = _n2o_ethanol(liquid).evaluate(3.26e6, 4.0)

        # About 10 kJ/mol less reactant enthalpy is worth about 77 K here.
        temperature_drop = (
            gas_properties.adiabatic_flame_temperature
            - liquid_properties.adiabatic_flame_temperature
        )
        assert 50.0 < temperature_drop < 110.0
        assert liquid_properties.i_sp_frozen < gas_properties.i_sp_frozen

    def test_custom_card_follows_mixture_ratio(self):
        # Catches cards written with the "name" keyword, which CEA burns at a
        # fixed composition whatever mixture ratio is asked for.
        propellant = _n2o_ethanol(
            propellants_models.saturated_liquid_nitrous_oxide(300.0)
        )
        lean = propellant.evaluate(3.26e6, 4.0, mixture_ratio=1.95)
        rich_in_oxidizer = propellant.evaluate(3.26e6, 4.0, mixture_ratio=4.0)
        assert (
            rich_in_oxidizer.adiabatic_flame_temperature
            > lean.adiabatic_flame_temperature + 300.0
        )

    def test_built_in_name_ignores_component_fields(self):
        base = propellant_components.PropellantComponent(
            name="N2O",
            role=propellant_components.ComponentRole.OXIDIZER,
            density=745.0,
            chemical_formula={"N": 2, "O": 1},
            enthalpy=0.0,
        )
        altered = propellant_components.PropellantComponent(
            name="N2O",
            role=propellant_components.ComponentRole.OXIDIZER,
            density=745.0,
            chemical_formula={"N": 2, "O": 1},
            enthalpy=-50000.0,
            initial_temperature=250.0,
        )
        assert _n2o_ethanol(base).evaluate(
            3.26e6, 4.0
        ).adiabatic_flame_temperature == pytest.approx(
            _n2o_ethanol(altered).evaluate(3.26e6, 4.0).adiabatic_flame_temperature
        )
