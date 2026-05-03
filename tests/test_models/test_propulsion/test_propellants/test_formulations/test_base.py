"""Tests for formulation base loader private functions."""

import pytest

from machwave.models.propellants.categories import MixtureType
from machwave.models.propellants.components import ComponentRole
from machwave.models.propellants.formulations.base import (
    _create_propellant,
    _parse_component,
    _parse_components,
    _parse_mixture_type,
    _parse_properties,
)


class TestParseMixtureType:
    """Tests for _parse_mixture_type function."""

    def test_parse_solid_mixture_type(self):
        data = {"mixture_type": "solid"}
        result = _parse_mixture_type(data)
        assert result == MixtureType.SOLID

    def test_parse_biliquid_mixture_type(self):
        data = {"mixture_type": "biliquid"}
        result = _parse_mixture_type(data)
        assert result == MixtureType.BILIQUID

    def test_parse_uppercase_mixture_type(self):
        data = {"mixture_type": "SOLID"}
        result = _parse_mixture_type(data)
        assert result == MixtureType.SOLID

    def test_missing_mixture_type_raises_error(self):
        data = {}
        with pytest.raises(ValueError, match="must contain 'mixture_type'"):
            _parse_mixture_type(data)

    def test_invalid_mixture_type_raises_error(self):
        data = {"mixture_type": "invalid"}
        with pytest.raises(ValueError, match="Invalid mixture_type"):
            _parse_mixture_type(data)


class TestParseComponent:
    """Tests for _parse_component function."""

    def test_parse_oxidizer_component(self):
        comp_data = {
            "name": "KNO3",
            "mass_fraction": 0.65,
            "role": "oxidizer",
            "density": 2109.0,
            "chemical_formula": {"K": 1, "N": 1, "O": 3},
            "enthalpy": -494600.0,
            "temperature": 298.15,
        }
        result = _parse_component(comp_data)

        assert result.name == "KNO3"
        assert result.role == ComponentRole.OXIDIZER
        assert result.density == 2109.0
        assert result.chemical_formula == {"K": 1, "N": 1, "O": 3}
        assert result.enthalpy == -494600.0
        assert result.initial_temperature == 298.15

    def test_parse_fuel_component(self):
        comp_data = {
            "name": "RP1",
            "mass_fraction": 0.35,
            "role": "fuel",
            "density": 820.0,
            "chemical_formula": {"C": 1, "H": 1.95},
            "enthalpy": -23500.0,
        }
        result = _parse_component(comp_data)

        assert result.name == "RP1"
        assert result.role == ComponentRole.FUEL
        assert result.density == 820.0

    def test_parse_additive_component(self):
        comp_data = {
            "name": "Aluminum",
            "mass_fraction": 0.14,
            "role": "additive",
            "density": 2700.0,
            "chemical_formula": {"Al": 1},
            "enthalpy": 0.0,
        }
        result = _parse_component(comp_data)
        assert result.role == ComponentRole.ADDITIVE

    def test_parse_component_with_default_temperature(self):
        comp_data = {
            "name": "Test",
            "mass_fraction": 1.0,
            "role": "fuel",
            "density": 1000.0,
            "chemical_formula": {"H": 2},
            "enthalpy": 0.0,
        }
        result = _parse_component(comp_data)

        assert result.initial_temperature == 298.15

    def test_missing_density_raises_error(self):
        comp_data = {
            "name": "KNO3",
            "mass_fraction": 1.0,
            "role": "oxidizer",
            # Missing density
            "chemical_formula": {"K": 1, "N": 1, "O": 3},
            "enthalpy": -494600.0,
        }
        with pytest.raises(KeyError):
            _parse_component(comp_data)

    def test_invalid_role_raises_error(self):
        comp_data = {
            "name": "Test",
            "mass_fraction": 1.0,
            "role": "invalid",
            "density": 1000.0,
        }
        with pytest.raises(ValueError, match="Invalid component role"):
            _parse_component(comp_data)

    def test_missing_required_field_raises_error(self):
        comp_data = {
            "name": "Test",
            "role": "fuel",
            "density": 1000.0,
            "enthalpy": 0.0,
            # Missing mass_fraction and chemical_formula
        }
        with pytest.raises(KeyError):
            _parse_component(comp_data)


class TestParseComponents:
    """Tests for _parse_components function."""

    def test_parse_empty_components(self):
        data = {}
        components, mass_fractions = _parse_components(
            data, mixture_type=MixtureType.SOLID
        )
        assert components == []
        assert mass_fractions == []

    def test_parse_single_component(self):
        data = {
            "components": [
                {
                    "name": "KNO3",
                    "mass_fraction": 1.0,
                    "role": "oxidizer",
                    "density": 2109.0,
                    "chemical_formula": {"K": 1, "N": 1, "O": 3},
                    "enthalpy": -494600.0,
                }
            ]
        }
        components, mass_fractions = _parse_components(
            data, mixture_type=MixtureType.SOLID
        )

        assert len(components) == 1
        assert components[0].name == "KNO3"
        assert mass_fractions == [1.0]

    def test_parse_multiple_components(self):
        data = {
            "components": [
                {
                    "name": "KNO3",
                    "mass_fraction": 0.65,
                    "role": "oxidizer",
                    "density": 2109.0,
                    "chemical_formula": {"K": 1, "N": 1, "O": 3},
                    "enthalpy": -494600.0,
                },
                {
                    "name": "Sucrose",
                    "mass_fraction": 0.35,
                    "role": "fuel",
                    "density": 1587.0,
                    "chemical_formula": {"C": 12, "H": 22, "O": 11},
                    "enthalpy": -2226100.0,
                },
            ]
        }
        components, mass_fractions = _parse_components(
            data, mixture_type=MixtureType.SOLID
        )

        assert len(components) == 2
        assert components[0].name == "KNO3"
        assert components[1].name == "Sucrose"
        assert mass_fractions == [0.65, 0.35]


class TestParseProperties:
    """Tests for _parse_properties function."""

    def test_parse_properties_when_present(self):
        data = {
            "properties": {
                "k_chamber": 1.24,
                "k_exhaust": 1.23,
                "adiabatic_flame_temperature": 3580.0,
                "molecular_weight_chamber": 0.0225,
                "molecular_weight_exhaust": 0.0230,
                "i_sp_frozen": 325.0,
                "i_sp_shifting": 345.0,
                "qsi_chamber": 0.0,
                "qsi_exhaust": 0.0,
            }
        }
        result = _parse_properties(data)

        assert result is not None
        assert result.k_chamber == 1.24
        assert result.k_exhaust == 1.23
        assert result.adiabatic_flame_temperature == 3580.0
        assert result.i_sp_frozen == 325.0
        assert result.qsi_chamber == 0.0

    def test_parse_properties_when_absent(self):
        data = {}
        result = _parse_properties(data)
        assert result is None

    def test_missing_required_property_raises_error(self):
        data = {
            "properties": {
                "k_chamber": 1.24,
                # Missing other required fields
            }
        }
        with pytest.raises(KeyError):
            _parse_properties(data)


class TestCreatePropellant:
    """Tests for _create_propellant function."""

    def test_create_solid_propellant(self):
        from machwave.models.propellants.categories import SolidPropellant

        data = {
            "name": "Test Solid",
            "combustion_efficiency": 0.95,
            "burn_rate_map": [{"min": 0, "max": 1e7, "a": 5.0, "n": 0.5}],
        }
        components = []
        mass_fractions = []
        properties = None

        result = _create_propellant(
            MixtureType.SOLID, data, components, mass_fractions, properties
        )

        assert isinstance(result, SolidPropellant)
        assert result.name == "Test Solid"
        assert result.combustion_efficiency == 0.95
        assert len(result.burn_rate_map) == 1

    def test_create_biliquid_propellant(self):
        from machwave.models.propellants.categories import BiliquidPropellant

        data = {
            "name": "Test Biliquid",
            "combustion_efficiency": 0.98,
            "of_ratio": 2.5,
        }
        components = []
        mass_fractions = None
        properties = None

        result = _create_propellant(
            MixtureType.BILIQUID, data, components, mass_fractions, properties
        )

        assert isinstance(result, BiliquidPropellant)
        assert result.name == "Test Biliquid"
        assert result.combustion_efficiency == 0.98
        assert result.of_ratio == 2.5

    def test_create_solid_with_default_efficiency(self):
        from machwave.models.propellants.categories import SolidPropellant

        data = {"name": "Test"}
        result = _create_propellant(MixtureType.SOLID, data, [], [], None)

        assert isinstance(result, SolidPropellant)
        assert result.combustion_efficiency == 0.95

    def test_create_biliquid_with_default_efficiency(self):
        from machwave.models.propellants.categories import BiliquidPropellant

        data = {"name": "Test"}
        result = _create_propellant(MixtureType.BILIQUID, data, [], None, None)

        assert isinstance(result, BiliquidPropellant)
        assert result.combustion_efficiency == 0.98
