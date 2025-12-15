"""Solid propellant type classes."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from machwave.services import RocketCEAService

from ..properties import ThermochemicalProperties
from .base import BurnRateOutOfBoundsError, Propellant


class SolidPropellant(Propellant):
    """Base class for solid propellants.

    Provides common interface for solid propellant burn rate calculations.

    Attributes:
        burn_rate: List of dictionaries describing burn rate behavior (St.
            Robert's law parameters) with keys: "min", "max", "a", and "n".
    """

    def __init__(
        self,
        burn_rate: list[dict[str, float | int]],
        combustion_efficiency: float,
    ):
        super().__init__(combustion_efficiency)
        self.burn_rate = burn_rate

    def get_burn_rate(self, chamber_pressure: float) -> float:
        """Calculate instantaneous burn rate using St. Robert's law.

        Args:
            chamber_pressure: Chamber pressure [Pa].

        Returns:
            float: Burn rate [m/s].

        Raises:
            BurnRateOutOfBoundsError: If chamber pressure is outside valid range.
        """
        for item in self.burn_rate:
            if item["min"] <= chamber_pressure <= item["max"]:
                a = item["a"]
                n = item["n"]
                # Convert pressure from Pa to MPa, apply St. Robert's law,
                # then convert from mm/s to m/s
                return (a * (chamber_pressure * 1e-6) ** n) * 1e-3

        raise BurnRateOutOfBoundsError(chamber_pressure)


class FixedSolidPropellant(SolidPropellant):
    """Solid propellant with pre-defined thermochemical properties.

    Used for propellants with empirical data from literature or testing.
    Properties are immutable after initialization.

    Args:
        name: Propellant name for identification.
        burn_rate: Burn rate parameters (St. Robert's law).
        properties: Thermochemical properties.
        combustion_efficiency: Combustion efficiency (0 to 1).
    """

    def __init__(
        self,
        name: str,
        burn_rate: list[dict[str, float | int]],
        properties: ThermochemicalProperties,
        combustion_efficiency: float,
    ):
        super().__init__(burn_rate, combustion_efficiency)
        self.name = name
        self.properties = properties

    def evaluate(
        self, chamber_pressure: float, expansion_ratio: float = 8.0
    ) -> ThermochemicalProperties:
        """Return pre-defined properties (no calculation needed).

        Args:
            chamber_pressure: Chamber pressure [Pa] (unused for fixed propellants).
            expansion_ratio: Nozzle area ratio (unused for fixed propellants).

        Returns:
            ThermochemicalProperties: Pre-defined thermochemical properties.
        """
        return self.properties


class FormulationBasedSolidPropellant(SolidPropellant):
    """Solid propellant built from modular chemical components with CEA calculation.

    Allows building custom propellant formulations by adding components with their
    chemical formulas, percentages, and thermochemical properties. Uses CEA to
    calculate thermochemical properties from the composition.

    Args:
        name: Propellant formulation name for identification.
        burn_rate: Burn rate parameters (St. Robert's law).
        ideal_density: Theoretical propellant density [kg/m³].
        combustion_efficiency: Combustion efficiency (0 to 1).

    Example:
        >>> propellant = FormulationBasedSolidPropellant(
        ...     name="KNSU",
        ...     burn_rate=[{"min": 0, "max": 100e6, "a": 8.26, "n": 0.319}],
        ...     ideal_density=1899.5,
        ...     combustion_efficiency=0.95
        ... )
        >>> propellant.add_component(
        ...     name="KNO3",
        ...     formula={"K": 1.0, "N": 1.0, "O": 3.0},
        ...     weight_percent=65.0,
        ...     heat_of_formation=-118200.0,
        ...     density=2.109
        ... )
        >>> propellant.add_component(
        ...     name="Sucrose",
        ...     formula={"C": 12.0, "H": 22.0, "O": 11.0},
        ...     weight_percent=35.0,
        ...     heat_of_formation=-532000.0,
        ...     density=1.5879
        ... )
        >>> props = propellant.evaluate(chamber_pressure=7e6, expansion_ratio=8.0)
    """

    def __init__(
        self,
        name: str,
        burn_rate: list[dict[str, float | int]],
        ideal_density: float,
        combustion_efficiency: float = 0.95,
        thermochem_service: "RocketCEAService | None" = None,
    ):
        super().__init__(burn_rate, combustion_efficiency)
        self.name = name
        self.ideal_density = ideal_density
        self.components = []
        self._cea_propellant_name = None
        self.thermochem_service = thermochem_service

    def add_component(
        self,
        name: str,
        formula: dict[str, float],
        weight_percent: float,
        heat_of_formation: float,
        density: float,
        temperature: float = 298.15,
    ) -> None:
        """Add a chemical component to the propellant formulation.

        Args:
            name: Component name (e.g., "KNO3", "HTPB", "AL").
            formula: Chemical formula as dict (e.g., {"K": 1.0, "N": 1.0, "O": 3.0}).
            weight_percent: Weight percentage in formulation (0-100).
            heat_of_formation: Standard heat of formation [cal/mol].
            density: Component density [g/cc].
            temperature: Reference temperature [K] (default: 298.15).
        """
        component = {
            "name": name,
            "formula": formula,
            "weight_percent": weight_percent,
            "heat_of_formation": heat_of_formation,
            "density": density,
            "temperature": temperature,
        }
        self.components.append(component)

    def generate_cea_card_string(self) -> str:
        """Generate CEA card string from components.

        Returns:
            str: CEA-formatted card string for the formulation.

        Raises:
            ValueError: If no components have been added.
        """
        from machwave.services.cea import generate_card_string

        return generate_card_string(self.components)

    def combustion_temperature(self) -> float:
        """Calculate real combustion temperature applying combustion efficiency.

        Returns:
            float: Real combustion temperature [K].

        Raises:
            ValueError: If properties have not been evaluated yet.
        """
        if self.properties is None:
            raise ValueError(
                "Must call evaluate() before accessing combustion_temperature"
            )
        return self.properties.adiabatic_flame_temperature * self.combustion_efficiency

    def evaluate(
        self, chamber_pressure: float, expansion_ratio: float = 8.0
    ) -> ThermochemicalProperties:
        """Calculate thermochemical properties using CEA from component formulation.

        Args:
            chamber_pressure: Chamber pressure [Pa].
            expansion_ratio: Nozzle area ratio (Ae/At).

        Returns:
            ThermochemicalProperties: Calculated thermochemical properties.

        Raises:
            ValueError: If no components added or weight percentages don't sum to 100%.
        """
        if not self.components:
            raise ValueError("No components added to formulation")

        # Validate weight percentages
        total_weight = sum(comp["weight_percent"] for comp in self.components)
        if abs(total_weight - 100.0) > 0.1:
            raise ValueError(
                f"Component weight percentages must sum to 100%, got {total_weight:.2f}%"
            )

        # Generate CEA card string and register with CEA
        card_str = self.generate_cea_card_string()
        self._cea_propellant_name = f"{self.name}_CEA"

        # Create service instance for this propellant
        if self.thermochem_service is None:
            from machwave.services import create_cea_service

            service = create_cea_service(
                propellant_name=self._cea_propellant_name, card_string=card_str
            )
        else:
            service = self.thermochem_service

        # Get thermochemical properties
        adiabatic_flame_temperature = service.get_adiabatic_flame_temperature(
            chamber_pressure=chamber_pressure
        )

        molecular_weight_chamber, gamma_chamber = service.get_chamber_properties(
            chamber_pressure=chamber_pressure, expansion_ratio=expansion_ratio
        )

        molecular_weight_exhaust, gamma_exhaust = service.get_exhaust_properties(
            chamber_pressure=chamber_pressure, expansion_ratio=expansion_ratio
        )

        i_sp_frozen, i_sp_shifting = service.get_specific_impulse(
            chamber_pressure=chamber_pressure, expansion_ratio=expansion_ratio
        )

        # Get condensed phase fractions
        qsi_chamber, qsi_exhaust = service.get_condensed_phase_fractions(
            chamber_pressure=chamber_pressure, expansion_ratio=expansion_ratio
        )

        # Construct solid propellant properties
        self.properties = ThermochemicalProperties(
            gamma_chamber=gamma_chamber,
            gamma_exhaust=gamma_exhaust,
            adiabatic_flame_temperature=adiabatic_flame_temperature,
            molecular_weight_chamber=molecular_weight_chamber,
            molecular_weight_exhaust=molecular_weight_exhaust,
            i_sp_frozen=i_sp_frozen,
            i_sp_shifting=i_sp_shifting,
            qsi_chamber=qsi_chamber,
            qsi_exhaust=qsi_exhaust,
        )

        return self.properties
