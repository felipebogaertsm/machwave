import pytest

import machwave.models.propellants as propellants_models
import machwave.models.propellants.components as propellant_components


@pytest.fixture
def lox_rp1_propellant() -> propellants_models.BiliquidPropellant:
    oxidizer = propellant_components.PropellantComponent(
        name="LOX",
        density=1141.0,
        chemical_formula={"O": 2},
        enthalpy=0.0,
        initial_temperature=298.15,
        role=propellant_components.ComponentRole.OXIDIZER,
    )
    fuel = propellant_components.PropellantComponent(
        name="RP1",
        density=820.0,
        chemical_formula={"C": 12, "H": 26},
        enthalpy=0.0,
        initial_temperature=298.15,
        role=propellant_components.ComponentRole.FUEL,
    )
    return propellants_models.BiliquidPropellant(
        name="LOX/RP1",
        components=[oxidizer, fuel],
        oxidizer_to_fuel_ratio=2.5,
    )


class TestBiliquidEvaluateMixtureRatio:
    def test_default_uses_design_ratio(self, lox_rp1_propellant):
        without_override = lox_rp1_propellant.evaluate(chamber_pressure=3e6)
        with_design_explicit = lox_rp1_propellant.evaluate(
            chamber_pressure=3e6,
            mixture_ratio=2.5,
        )
        assert without_override.adiabatic_flame_temperature == pytest.approx(
            with_design_explicit.adiabatic_flame_temperature
        )
        assert without_override.i_sp_frozen == pytest.approx(
            with_design_explicit.i_sp_frozen
        )

    def test_live_ratio_changes_properties(self, lox_rp1_propellant):
        design = lox_rp1_propellant.evaluate(chamber_pressure=3e6)
        off_design = lox_rp1_propellant.evaluate(
            chamber_pressure=3e6,
            mixture_ratio=1.5,
        )
        assert design.adiabatic_flame_temperature != pytest.approx(
            off_design.adiabatic_flame_temperature
        )
        assert design.k_chamber != pytest.approx(off_design.k_chamber)
        assert design.k_exhaust != pytest.approx(off_design.k_exhaust)
        assert design.i_sp_frozen != pytest.approx(off_design.i_sp_frozen)
        assert design.i_sp_shifting != pytest.approx(off_design.i_sp_shifting)

    def test_design_attribute_unchanged_after_evaluate(self, lox_rp1_propellant):
        lox_rp1_propellant.evaluate(chamber_pressure=3e6, mixture_ratio=1.5)
        assert lox_rp1_propellant.oxidizer_to_fuel_ratio == 2.5

    def test_nearby_mixture_ratios_share_cache_entry(self, lox_rp1_propellant):
        quantization = lox_rp1_propellant.MIXTURE_RATIO_QUANTIZATION
        first = lox_rp1_propellant.evaluate(chamber_pressure=3e6, mixture_ratio=2.5)
        second = lox_rp1_propellant.evaluate(
            chamber_pressure=3e6, mixture_ratio=2.5 + quantization / 4
        )
        assert second is first
        assert len(lox_rp1_propellant._evaluation_cache) == 1

    def test_distinct_mixture_ratios_use_separate_cache_entries(
        self, lox_rp1_propellant
    ):
        quantization = lox_rp1_propellant.MIXTURE_RATIO_QUANTIZATION
        first = lox_rp1_propellant.evaluate(chamber_pressure=3e6, mixture_ratio=2.5)
        second = lox_rp1_propellant.evaluate(
            chamber_pressure=3e6, mixture_ratio=2.5 + 2 * quantization
        )
        assert second is not first
        assert len(lox_rp1_propellant._evaluation_cache) == 2


def _biliquid_with_fuel_formula(
    fuel_formula: dict[str, int],
) -> propellants_models.BiliquidPropellant:
    oxidizer = propellant_components.PropellantComponent(
        name="LOX",
        density=1141.0,
        chemical_formula={"O": 2},
        enthalpy=0.0,
        role=propellant_components.ComponentRole.OXIDIZER,
    )
    fuel = propellant_components.PropellantComponent(
        name="FUEL",
        density=820.0,
        chemical_formula=fuel_formula,
        enthalpy=0.0,
        role=propellant_components.ComponentRole.FUEL,
    )
    return propellants_models.BiliquidPropellant(
        name="PROBE", components=[oxidizer, fuel], oxidizer_to_fuel_ratio=2.5
    )


class TestBiliquidCondensedPhase:
    def test_gaseous_only_propellant_reports_no_condensed_phase(
        self, lox_rp1_propellant
    ):
        assert lox_rp1_propellant.has_condensed_phase is False

    def test_metal_component_reports_condensed_phase(self):
        propellant = _biliquid_with_fuel_formula({"Al": 1})
        assert propellant.has_condensed_phase is True

    def test_element_matching_is_case_insensitive(self):
        # "cl" must classify as the gaseous-only element Cl.
        propellant = _biliquid_with_fuel_formula({"cl": 1, "h": 1})
        assert propellant.has_condensed_phase is False

    def test_service_inherits_no_condensed_phase_flag(self, lox_rp1_propellant):
        assert lox_rp1_propellant.thermochemical_service.has_condensed_phase is False
