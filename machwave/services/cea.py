"""Interface layer to services that provide thermochemical properties through CEA
(Chemical Equilibrium with Applications).

This module defines a service protocol for thermochemical calculations and
implements a RocketCEAService that uses the rocketcea package to perform
CEA calculations for solid propellants.
"""

from typing import Protocol

from rocketcea.cea_obj import CEA_Obj, add_new_propellant

from machwave.core.conversions import (
    convert_pa_to_psi,
    convert_rankine_to_kelvin,
)
from machwave.models.propulsion.propellants.properties import (
    ChemicalPropellantProperties,
    SolidPropellantProperties,
)


class ThermochemicalService(Protocol):
    """Protocol for thermochemical calculation services."""

    def generate_card_string(self, components: list[dict]) -> str:
        """Generate CEA card string from component list.

        Args:
            components: List of component dictionaries with keys: 'name', 'formula',
                'weight_percent', 'heat_of_formation', 'temperature', 'density'.

        Returns:
            str: Engine-specific input format string.
        """
        ...

    def register_propellant(self, propellant_name: str, card_string: str) -> None:
        """Register propellant with service library.

        Args:
            propellant_name: Unique identifier for the propellant.
            card_string: Engine-specific input format string from generate_card_string().
        """
        ...

    def calculate_properties(
        self,
        propellant_name: str,
        chamber_pressure: float,
        expansion_ratio: float,
    ) -> ChemicalPropellantProperties:
        """Calculate theoretical thermochemical properties.

        Args:
            propellant_name: Name of propellant (must be registered first).
            chamber_pressure: Chamber pressure [Pa].
            expansion_ratio: Nozzle area ratio (Ae/At).

        Returns:
            ChemicalPropellantProperties: Theoretical thermochemical properties
                assuming ideal combustion. Concrete implementations may return
                subclasses (Solid/Liquid specific properties).
        """
        ...


class RocketCEAService:
    """Service for performing CEA thermochemical calculations."""

    def _get_temperature(self, cea_obj: CEA_Obj, chamber_pressure_psi: float) -> float:
        """Get adiabatic flame temperature from CEA.

        Args:
            cea_obj: CEA calculation object.
            chamber_pressure_psi: Chamber pressure [psi].

        Returns:
            float: Adiabatic flame temperature [K].
        """
        return convert_rankine_to_kelvin(cea_obj.get_Tcomb(Pc=chamber_pressure_psi))

    def _get_chamber_properties(
        self, cea_obj: CEA_Obj, chamber_pressure_psi: float, expansion_ratio: float
    ) -> tuple[float, float]:
        """Get chamber molecular weight and gamma.

        Args:
            cea_obj: CEA calculation object.
            chamber_pressure_psi: Chamber pressure [psi].
            expansion_ratio: Nozzle area ratio (Ae/At).

        Returns:
            tuple[float, float]: (molecular_weight [kg/mol], gamma)
        """
        molecular_weight_g, gamma = cea_obj.get_Chamber_MolWt_gamma(
            Pc=chamber_pressure_psi, eps=expansion_ratio
        )
        return molecular_weight_g / 1000.0, gamma

    def _get_exhaust_properties(
        self, cea_obj: CEA_Obj, chamber_pressure_psi: float, expansion_ratio: float
    ) -> tuple[float, float]:
        """Get exhaust molecular weight and gamma (frozen flow).

        Args:
            cea_obj: CEA calculation object.
            chamber_pressure_psi: Chamber pressure [psi].
            expansion_ratio: Nozzle area ratio (Ae/At).

        Returns:
            tuple[float, float]: (molecular_weight [kg/mol], gamma)
        """
        molecular_weight_g, gamma = cea_obj.get_exit_MolWt_gamma(
            Pc=chamber_pressure_psi, eps=expansion_ratio, frozen=1
        )
        return molecular_weight_g / 1000.0, gamma

    def _get_specific_impulse(
        self, cea_obj: CEA_Obj, chamber_pressure_psi: float, expansion_ratio: float
    ) -> tuple[float, float]:
        """Get frozen and shifting equilibrium specific impulse.

        Args:
            cea_obj: CEA calculation object.
            chamber_pressure_psi: Chamber pressure [psi].
            expansion_ratio: Nozzle area ratio (Ae/At).

        Returns:
            tuple[float, float]: (i_sp_frozen [s], i_sp_shifting [s])
        """
        i_sp_frozen = cea_obj.get_Isp(
            Pc=chamber_pressure_psi, eps=expansion_ratio, frozenAtThroat=1
        )
        i_sp_shifting = cea_obj.get_Isp(
            Pc=chamber_pressure_psi, eps=expansion_ratio, frozen=0
        )
        return i_sp_frozen, i_sp_shifting

    def _get_condensed_phase_fractions(
        self, cea_obj: CEA_Obj, chamber_pressure_psi: float, expansion_ratio: float
    ) -> tuple[float, float]:
        """Calculate condensed phase species content (qsi).

        Args:
            cea_obj: CEA calculation object.
            chamber_pressure_psi: Chamber pressure [psi].
            expansion_ratio: Nozzle area ratio (Ae/At).

        Returns:
            tuple[float, float]: (qsi_chamber [mol/(100g)], qsi_exhaust [mol/(100g)])
        """
        qsi_chamber = 0.0
        qsi_exhaust = 0.0
        try:
            species_dict, mass_fractions = cea_obj.get_SpeciesMassFractions(
                Pc=chamber_pressure_psi, eps=expansion_ratio, frozen=0
            )
            for species_name, fractions in zip(
                species_dict.keys(), mass_fractions.values()
            ):
                if any(phase in species_name for phase in ["(cr)", "(L)", "(s)"]):
                    qsi_chamber += fractions[0]
                    qsi_exhaust += fractions[2]
        except Exception:
            pass
        return qsi_chamber, qsi_exhaust

    def generate_card_string(self, components: list[dict]) -> str:
        """Generate CEA card string from component list.

        Args:
            components: List of component dictionaries.

        Returns:
            str: CEA-formatted card string.
        """
        if not components:
            raise ValueError("No components provided")

        card_lines = []
        for comp in components:
            formula_str = " ".join(
                f"{elem} {count}" for elem, count in comp["formula"].items()
            )
            line = (
                f"name {comp['name']}  {formula_str}  wt%={comp['weight_percent']:.1f}"
            )
            card_lines.append(line)

            thermo_line = (
                f"h,cal={comp['heat_of_formation']:.1f}  "
                f"t(k)={comp['temperature']:.2f}  "
                f"rho,g/cc={comp['density']:.4f}"
            )
            card_lines.append(thermo_line)

        return "\n".join(card_lines)

    def register_propellant(self, propellant_name: str, card_string: str) -> None:
        """Register a custom propellant with CEA.

        Args:
            propellant_name: Unique name for the propellant.
            card_string: CEA-formatted card string.
        """
        add_new_propellant(propellant_name, card_string)

    def calculate_properties(
        self,
        propellant_name: str,
        chamber_pressure: float,
        expansion_ratio: float,
    ) -> SolidPropellantProperties:
        """Calculate theoretical thermochemical properties using CEA.

        Args:
            propellant_name: Name of propellant (must be registered with CEA).
            chamber_pressure: Chamber pressure [Pa].
            expansion_ratio: Nozzle area ratio (Ae/At).

        Returns:
            SolidPropellantProperties: Theoretical thermochemical properties
                assuming ideal (100% efficient) combustion.
        """
        cea_obj = CEA_Obj(propName=propellant_name)
        chamber_pressure_psi = convert_pa_to_psi(chamber_pressure)

        # Get thermochemical properties from CEA
        adiabatic_flame_temperature = self._get_temperature(
            cea_obj, chamber_pressure_psi
        )
        molecular_weight_chamber, gamma_chamber = self._get_chamber_properties(
            cea_obj, chamber_pressure_psi, expansion_ratio
        )
        molecular_weight_exhaust, gamma_exhaust = self._get_exhaust_properties(
            cea_obj, chamber_pressure_psi, expansion_ratio
        )
        i_sp_frozen, i_sp_shifting = self._get_specific_impulse(
            cea_obj, chamber_pressure_psi, expansion_ratio
        )
        qsi_chamber, qsi_exhaust = self._get_condensed_phase_fractions(
            cea_obj, chamber_pressure_psi, expansion_ratio
        )

        return SolidPropellantProperties(
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
