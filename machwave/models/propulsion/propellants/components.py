"""
This module contains classes representing the chemical components of a propellant
formulation, including their roles and properties.
"""

import dataclasses
import enum

from machwave.core.conversions import (
    convert_joules_per_mol_to_cal_per_mol,
    convert_kgm3_to_gcc,
)


class ComponentRole(enum.StrEnum):
    """Role of a chemical component in the propellant formulation."""

    OXIDIZER = "oxidizer"
    FUEL = "fuel"  # Includes binders (HTPB, PBAN, etc.)
    ADDITIVE = "additive"


@dataclasses.dataclass(frozen=True, kw_only=True)
class PropellantComponent:
    """Chemical component of a propellant formulation.

    Attributes:
        name: Component name (i.e., "KNO3", "LOX", "HTPB").
        mass_fraction: Mass fraction in formulation.
        role: Component role (oxidizer, fuel, additive).
        density: Component density [kg/m³].
        chemical_formula: Element symbols to atom counts (i.e., {"H": 2, "O": 1}).
        enthalpy: Standard enthalpy of formation [J/mol].
        initial_temperature: Initial component temperature before combustion [K].
    """

    name: str
    mass_fraction: float
    role: ComponentRole
    density: float
    chemical_formula: dict[str, int]
    enthalpy: float
    initial_temperature: float = 298.15

    def to_cea_dict(self) -> dict:
        """Convert component to CEA-compatible dictionary format.

        Returns:
            dict: CEA format with name, formula, weight_percent, heat_of_formation (cal/mol),
                  temperature (K), and density (g/cc).
        """
        heat_of_formation_cal = convert_joules_per_mol_to_cal_per_mol(self.enthalpy)
        density_gcc = convert_kgm3_to_gcc(self.density)

        return {
            "name": self.name,
            "formula": self.chemical_formula,
            "weight_percent": self.mass_fraction * 100,
            "heat_of_formation": heat_of_formation_cal,
            "temperature": self.initial_temperature,
            "density": density_gcc,
        }
