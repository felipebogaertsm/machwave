"""Tests for JSON-based propellant formulations."""

import json
from pathlib import Path

import pytest

from machwave.models.propellants.categories import (
    BiliquidPropellant,
    MixtureType,
    SolidPropellant,
)
from machwave.models.propellants.components import ComponentRole
from machwave.models.propellants.formulations import (
    get_propellant_from_json,
)

# Get paths to formulation directories
FORMULATIONS_DIR = (
    Path(__file__).parent.parent.parent.parent.parent.parent
    / "machwave"
    / "models"
    / "propellants"
    / "formulations"
)
SOLID_DIR = FORMULATIONS_DIR / "solid"
BILIQUID_DIR = FORMULATIONS_DIR / "biliquid"


class TestJSONFormulationLoading:
    """Test loading propellants from JSON files."""

    def test_formulation_directories_exist(self):
        """Test that formulation directories exist."""
        assert FORMULATIONS_DIR.exists(), "Formulations directory not found"
        assert SOLID_DIR.exists(), "Solid formulations directory not found"
        assert BILIQUID_DIR.exists(), "Biliquid formulations directory not found"

    def test_solid_json_files_exist(self):
        """Test that solid propellant JSON files exist."""
        solid_files = list(SOLID_DIR.glob("*.json"))
        assert len(solid_files) > 0, "No solid propellant JSON files found"
        assert len(solid_files) == 8, (
            f"Expected 8 solid JSON files, found {len(solid_files)}"
        )

    def test_biliquid_json_files_exist(self):
        """Test that biliquid propellant JSON files exist."""
        biliquid_files = list(BILIQUID_DIR.glob("*.json"))
        assert len(biliquid_files) > 0, "No biliquid propellant JSON files found"
        assert len(biliquid_files) == 1, (
            f"Expected 1 biliquid JSON file, found {len(biliquid_files)}"
        )

    @pytest.mark.parametrize(
        "json_file",
        list(SOLID_DIR.glob("*.json")) if SOLID_DIR.exists() else [],
        ids=lambda p: p.stem,
    )
    def test_load_all_solid_formulations(self, json_file):
        """Test loading each solid propellant JSON file."""
        # Load the propellant
        propellant = get_propellant_from_json(json_file)

        # Verify it's a SolidPropellant
        assert isinstance(propellant, SolidPropellant), (
            f"{json_file.stem}: Not a SolidPropellant instance"
        )

        # Verify mixture type
        assert propellant.mixture_type == MixtureType.SOLID, (
            f"{json_file.stem}: Wrong mixture_type"
        )

        # Verify basic fields
        assert propellant.name, f"{json_file.stem}: Missing name"
        assert len(propellant.components) > 0, f"{json_file.stem}: No components"
        assert 0 < propellant.combustion_efficiency <= 1.0, (
            f"{json_file.stem}: Invalid combustion_efficiency"
        )

        # Verify components have required fields
        for comp in propellant.components:
            assert comp.name, f"{json_file.stem}: Component missing name"
            assert comp.density > 0, f"{json_file.stem}: Invalid density"
            assert isinstance(comp.role, ComponentRole), (
                f"{json_file.stem}: Invalid component role"
            )
            assert hasattr(comp, "chemical_formula"), (
                f"{json_file.stem}: Missing chemical_formula"
            )
            assert hasattr(comp, "enthalpy"), f"{json_file.stem}: Missing enthalpy"
            assert comp.initial_temperature > 0, (
                f"{json_file.stem}: Invalid temperature"
            )

        # Verify burn rate if present
        if propellant.burn_rate_map:
            for rate_segment in propellant.burn_rate_map:
                assert "min" in rate_segment, (
                    f"{json_file.stem}: Burn rate missing 'min'"
                )
                assert "max" in rate_segment, (
                    f"{json_file.stem}: Burn rate missing 'max'"
                )
                assert "a" in rate_segment, f"{json_file.stem}: Burn rate missing 'a'"
                assert "n" in rate_segment, f"{json_file.stem}: Burn rate missing 'n'"
                assert rate_segment["min"] < rate_segment["max"], (
                    f"{json_file.stem}: Invalid burn rate range"
                )

        # Verify properties if present
        if propellant.properties:
            props = propellant.properties
            assert props.k_chamber > 1.0, f"{json_file.stem}: Invalid k_chamber"
            assert props.k_exhaust > 1.0, f"{json_file.stem}: Invalid k_exhaust"
            assert props.adiabatic_flame_temperature > 0, (
                f"{json_file.stem}: Invalid temperature"
            )
            assert props.molecular_weight_chamber > 0, (
                f"{json_file.stem}: Invalid MW chamber"
            )
            assert props.molecular_weight_exhaust > 0, (
                f"{json_file.stem}: Invalid MW exhaust"
            )
            assert props.i_sp_frozen > 0, f"{json_file.stem}: Invalid Isp frozen"
            assert props.i_sp_shifting > 0, f"{json_file.stem}: Invalid Isp shifting"

    @pytest.mark.parametrize(
        "json_file",
        list(BILIQUID_DIR.glob("*.json")) if BILIQUID_DIR.exists() else [],
        ids=lambda p: p.stem,
    )
    def test_load_all_biliquid_formulations(self, json_file):
        """Test loading each liquid propellant JSON file."""
        # Load the propellant
        propellant = get_propellant_from_json(json_file)

        # Verify it's a BiliquidPropellant
        assert isinstance(propellant, BiliquidPropellant), (
            f"{json_file.stem}: Not a BiliquidPropellant instance"
        )

        # Verify mixture type
        assert propellant.mixture_type == MixtureType.BILIQUID, (
            f"{json_file.stem}: Wrong mixture_type"
        )

        # Verify basic fields
        assert propellant.name, f"{json_file.stem}: Missing name"
        assert len(propellant.components) == 2, (
            f"{json_file.stem}: Biliquid must have exactly 2 components"
        )
        assert 0 < propellant.combustion_efficiency <= 1.0, (
            f"{json_file.stem}: Invalid combustion_efficiency"
        )
        assert propellant.oxidizer_to_fuel_ratio is not None, (
            f"{json_file.stem}: Missing O/F ratio"
        )
        assert propellant.oxidizer_to_fuel_ratio > 0, (
            f"{json_file.stem}: Invalid O/F ratio"
        )

        # Verify components have required fields
        has_oxidizer = False
        has_fuel = False
        for comp in propellant.components:
            assert comp.name, f"{json_file.stem}: Component missing name"
            assert comp.density > 0, f"{json_file.stem}: Invalid density"
            assert isinstance(comp.role, ComponentRole), (
                f"{json_file.stem}: Invalid component role"
            )
            assert hasattr(comp, "chemical_formula"), (
                f"{json_file.stem}: Missing chemical_formula"
            )
            assert hasattr(comp, "enthalpy"), f"{json_file.stem}: Missing enthalpy"
            assert comp.initial_temperature > 0, (
                f"{json_file.stem}: Invalid temperature"
            )

            if comp.role == ComponentRole.OXIDIZER:
                has_oxidizer = True
            elif comp.role == ComponentRole.FUEL:
                has_fuel = True

        assert has_oxidizer and has_fuel, (
            f"{json_file.stem}: Must have both oxidizer and fuel"
        )

    def test_json_schema_validation(self):
        """Test that all JSON files have valid structure."""
        all_files = list(SOLID_DIR.glob("*.json")) + list(BILIQUID_DIR.glob("*.json"))

        for json_file in all_files:
            with open(json_file, "r") as f:
                data = json.load(f)

            # Required fields
            assert "mixture_type" in data, f"{json_file.stem}: Missing mixture_type"
            assert "name" in data, f"{json_file.stem}: Missing name"
            assert "components" in data, f"{json_file.stem}: Missing components"

            # Validate components structure
            assert isinstance(data["components"], list), (
                f"{json_file.stem}: Components must be a list"
            )
            assert len(data["components"]) > 0, (
                f"{json_file.stem}: No components defined"
            )

            for i, comp in enumerate(data["components"]):
                assert "name" in comp, f"{json_file.stem}: Component {i} missing name"
                assert "mass_fraction" in comp, (
                    f"{json_file.stem}: Component {i} missing mass_fraction"
                )
                assert "role" in comp, f"{json_file.stem}: Component {i} missing role"
                # density is optional when properties are pre-defined

    def test_evaluate_with_predefined_properties(self):
        """Test that propellants with pre-defined properties evaluate correctly."""
        # Load a solid propellant
        kndx = get_propellant_from_json(SOLID_DIR / "kndx.json")

        # Verify it has pre-defined properties
        assert kndx.properties is not None, "KNDX should have pre-defined properties"

        # Evaluate
        result = kndx.evaluate(5e6, 8.0)

        # Should return the pre-defined properties
        assert result == kndx.properties, "Should return pre-defined properties"
        assert result.k_chamber == 1.1308
        assert result.i_sp_frozen == 152.4

    def test_component_to_cea_dict(self):
        """Test that components can be converted to CEA dict format."""
        # Load any propellant
        prop = get_propellant_from_json(SOLID_DIR / "kndx.json")

        # Test to_cea_dict on first component
        comp = prop.components[0]
        cea_dict = comp.to_cea_dict(weight_percent=50.0)

        # Verify CEA dict structure
        assert "name" in cea_dict
        assert "weight_percent" in cea_dict
        assert "heat_of_formation" in cea_dict
        assert "formula" in cea_dict
        assert "temperature" in cea_dict
        assert "density" in cea_dict

        # Verify values
        assert cea_dict["name"] == comp.name
        assert cea_dict["weight_percent"] == 50.0
        # Heat of formation is converted from J/mol to cal/mol
        from machwave.core.conversions import convert_joules_per_mol_to_cal_per_mol

        assert cea_dict["heat_of_formation"] == convert_joules_per_mol_to_cal_per_mol(
            comp.enthalpy
        )
        assert cea_dict["formula"] == comp.chemical_formula

    def test_solid_burn_rate_calculation(self):
        """Test burn rate calculation for solid propellants."""
        # Load KNDX which has burn rate data
        kndx = get_propellant_from_json(SOLID_DIR / "kndx.json")

        # Calculate burn rate at 5 MPa
        burn_rate = kndx.get_burn_rate(5e6)

        # Verify burn rate is positive
        assert burn_rate > 0, "Burn rate must be positive"
        assert burn_rate < 0.1, "Burn rate seems unreasonably high"

    def test_invalid_json_raises_error(self, tmp_path):
        """Test that invalid JSON raises appropriate errors."""
        # Create invalid JSON file (missing mixture_type)
        invalid_json = tmp_path / "invalid.json"
        with open(invalid_json, "w") as f:
            json.dump({"name": "Invalid", "components": []}, f)

        with pytest.raises(ValueError, match="mixture_type"):
            get_propellant_from_json(invalid_json)

    def test_nonexistent_file_raises_error(self):
        """Test that loading non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            get_propellant_from_json("nonexistent_file.json")

    def test_mass_fractions_sum_approximately_to_one(self):
        """Test that component mass fractions sum to approximately 1.0."""
        all_files = list(SOLID_DIR.glob("*.json")) + list(BILIQUID_DIR.glob("*.json"))

        for json_file in all_files:
            prop = get_propellant_from_json(json_file)
            if isinstance(prop, SolidPropellant):
                total_mass_fraction = sum(prop.mass_fractions)
                assert 0.99 <= total_mass_fraction <= 1.01, (
                    f"{json_file.stem}: Mass fractions sum to {total_mass_fraction}, expected ~1.0"
                )

    @pytest.mark.parametrize(
        "json_file",
        list(SOLID_DIR.glob("*.json")) if SOLID_DIR.exists() else [],
        ids=lambda p: p.stem,
    )
    def test_solid_formulations_can_be_evaluated_with_cea(self, json_file):
        """Ensure a CEA-backed evaluation can run for each solid formulation.

        The formulation JSONs may include fixed properties; this test explicitly
        bypasses those to validate that the component-based CEA path still works.
        """
        loaded = get_propellant_from_json(json_file)
        assert isinstance(loaded, SolidPropellant)
        assert loaded.components, f"{json_file.stem}: expected components"
        assert loaded.mass_fractions, f"{json_file.stem}: expected mass_fractions"

        cea_propellant = SolidPropellant(
            name=f"{loaded.name}__CEA__{json_file.stem}",
            components=loaded.components,
            mass_fractions=loaded.mass_fractions,
            combustion_efficiency=loaded.combustion_efficiency,
            properties=None,
            burn_rate_map=loaded.burn_rate_map,
        )

        props = cea_propellant.evaluate(5e6, 8.0)
        assert 1.0 < props.k_chamber <= 2.0
        assert props.adiabatic_flame_temperature > 0
        assert props.molecular_weight_chamber > 0
        assert props.i_sp_frozen > 0

    @pytest.mark.parametrize(
        "json_stem",
        ["kndx", "knsb", "knsu"],
    )
    def test_fixed_properties_are_reasonably_close_to_cea_for_selected_solids(
        self, json_stem
    ):
        """Compare fixed JSON properties to a CEA reconstruction for a few solids.

        The fixed properties in JSON are treated as canonical reference values.
        This check is intentionally limited to a small representative set where
        the CEA reconstruction is expected to be in the same ballpark.
        """
        json_file = SOLID_DIR / f"{json_stem}.json"
        loaded = get_propellant_from_json(json_file)
        assert isinstance(loaded, SolidPropellant)
        assert loaded.properties is not None, f"{json_stem}: expected fixed properties"

        cea_propellant = SolidPropellant(
            name=f"{loaded.name}__CEA__{json_stem}",
            components=loaded.components,
            mass_fractions=loaded.mass_fractions,
            combustion_efficiency=loaded.combustion_efficiency,
            properties=None,
            burn_rate_map=loaded.burn_rate_map,
        )
        cea = cea_propellant.evaluate(5e6, 8.0)
        fixed = loaded.properties

        def rel_diff(a: float, b: float) -> float:
            return abs(a - b) / abs(b) if b else float("inf")

        assert rel_diff(cea.k_chamber, fixed.k_chamber) < 0.10
        assert (
            rel_diff(cea.adiabatic_flame_temperature, fixed.adiabatic_flame_temperature)
            < 0.10
        )
        assert rel_diff(cea.i_sp_frozen, fixed.i_sp_frozen) < 0.20
