import pytest

from machwave.models.propellants import BiliquidPropellant
from machwave.models.propellants.components import (
    ComponentRole,
    PropellantComponent,
)


@pytest.fixture
def lox_rp1_propellant() -> BiliquidPropellant:
    oxidizer = PropellantComponent(
        name="LOX",
        density=1141.0,
        chemical_formula={"O": 2},
        enthalpy=0.0,
        initial_temperature=298.15,
        role=ComponentRole.OXIDIZER,
    )
    fuel = PropellantComponent(
        name="RP1",
        density=820.0,
        chemical_formula={"C": 12, "H": 26},
        enthalpy=0.0,
        initial_temperature=298.15,
        role=ComponentRole.FUEL,
    )
    return BiliquidPropellant(
        name="LOX/RP1",
        components=[oxidizer, fuel],
        oxidizer_to_fuel_ratio=2.5,
    )


class TestBiliquidEvaluateOverride:
    def test_default_uses_design_ratio(self, lox_rp1_propellant):
        without_override = lox_rp1_propellant.evaluate(chamber_pressure=3e6)
        with_design_explicit = lox_rp1_propellant.evaluate(
            chamber_pressure=3e6,
            oxidizer_to_fuel_ratio=2.5,
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
            oxidizer_to_fuel_ratio=1.5,
        )
        assert design.adiabatic_flame_temperature != pytest.approx(
            off_design.adiabatic_flame_temperature
        )
        assert design.k_chamber != pytest.approx(off_design.k_chamber)
        assert design.k_exhaust != pytest.approx(off_design.k_exhaust)
        assert design.i_sp_frozen != pytest.approx(off_design.i_sp_frozen)
        assert design.i_sp_shifting != pytest.approx(off_design.i_sp_shifting)

    def test_design_attribute_unchanged_after_evaluate(self, lox_rp1_propellant):
        lox_rp1_propellant.evaluate(chamber_pressure=3e6, oxidizer_to_fuel_ratio=1.5)
        assert lox_rp1_propellant.oxidizer_to_fuel_ratio == 2.5
