"""
This module contains classes representing the chemical components of a propellant
mixture, including their roles and properties.
"""

from dataclasses import dataclass
from enum import Enum


class ComponentRole(str, Enum):
    """Role of a chemical component in the propellant mixture."""

    OXIDIZER = "oxidizer"
    FUEL = "fuel"  # Includes binders (HTPB, PBAN, etc.)
    ADDITIVE = "additive"


@dataclass
class PropellantComponent:
    """Chemical component of a propellant mixture.

    Attributes:
        name: Chemical name (e.g., "KNO3", "LOX", "HTPB").
        mass_fraction: Mass fraction in mixture (0-1).
        role: Component role (oxidizer, fuel, additive).
        density: Component density [kg/m³].
        chemical_formula: Element symbols to atom counts (e.g., {"H": 2, "O": 1}).
        enthalpy: Standard enthalpy of formation [J/mol].
        temperature: Initial component temperature before combustion [K].
    """

    name: str
    mass_fraction: float
    role: ComponentRole
    density: float
    chemical_formula: dict[str, int]
    enthalpy: float
    temperature: float = 298.15

    def to_cea_dict(self) -> dict:
        """Convert component to CEA-compatible dictionary format.

        Returns:
            dict: CEA format with name, formula, weight_percent, heat_of_formation,
                  temperature, and density.
        """
        return {
            "name": self.name,
            "formula": self.chemical_formula,
            "weight_percent": self.mass_fraction * 100,
            "heat_of_formation": self.enthalpy,
            "temperature": self.temperature,
            "density": self.density,
        }
