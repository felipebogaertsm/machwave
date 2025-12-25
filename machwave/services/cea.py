"""This module defines a service for thermochemical calculations, RocketCEAService.
It uses that uses the rocketcea package to perform Chemical Equilibrium calculations
for solid propellants, based on the widely accepted NASA's CEA code.
"""

import re

from rocketcea.cea_obj import (
    CEA_Obj,
    add_new_fuel,
    add_new_oxidizer,
    add_new_propellant,
)

from machwave.core.conversions import (
    convert_lbft3_to_kgm3,
    convert_pa_to_psi,
    convert_rankine_to_kelvin,
)


def normalize_custom_propellant_name(name: str) -> str:
    """Normalize a *custom* propellant name for RocketCEA registration.

    RocketCEA internally sanitizes propellant identifiers; if we register a
    propellant with a name containing characters like '-' or '(', the lookup can
    fail later if RocketCEA normalizes it differently.

    Notes:
        This should be used for custom propellant registration (propName), not for
        built-in oxidizer/fuel names (oxName/fuelName), which can be case-sensitive.
    """
    normalized = name.strip().upper()
    normalized = re.sub(r"\s+", "_", normalized)
    normalized = re.sub(r"[^A-Z0-9_]", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    if not normalized:
        raise ValueError("Propellant name cannot be empty")
    return normalized


def generate_card_string(components: list[dict]) -> str:
    """Generate CEA card string from component list."""
    if not components:
        raise ValueError("No components provided")

    card_lines = []
    for comp in components:
        formula_str = " ".join(
            f"{elem} {count}" for elem, count in comp["formula"].items()
        )
        line = f"name {comp['name']}  {formula_str}  wt%={comp['weight_percent']:.1f}"
        card_lines.append(line)

        thermo_line = (
            f"h,cal={comp['heat_of_formation']:.1f}  "
            f"t(k)={comp['temperature']:.2f}  "
            f"rho,g/cc={comp['density']:.4f}"
        )
        card_lines.append(thermo_line)

    return "\n".join(card_lines)


def create_cea_service(
    propellant_name: str | None = None,
    card_string: str | None = None,
    oxidizer_name: str | None = None,
    oxidizer_card_string: str | None = None,
    fuel_name: str | None = None,
    fuel_card_string: str | None = None,
    oxidizer_to_fuel_ratio: float | None = None,
) -> "RocketCEAService":
    """Factory function to create RocketCEAService with propellant registration.

    This function handles all the complexity of registering custom
    propellants/oxidizers/fuels with RocketCEA and returns a simple service wrapper.

    Configuration modes:
    1. Solid/monopropellant: propellant_name (+ optional card_string)
    2. Biliquid: oxidizer_name + fuel_name (+ optional card strings)
    3. Custom biliquid: Custom oxidizer/fuel via card strings

    Args:
        propellant_name: Name of solid/monoliquid propellant.
        card_string: CEA card string for custom solid/monopropellant.
        oxidizer_name: Oxidizer name for biliquid propellant.
        oxidizer_card_string: CEA card string for custom oxidizer.
        fuel_name: Fuel name for biliquid propellant.
        fuel_card_string: CEA card string for custom fuel.
        oxidizer_to_fuel_ratio: O/F ratio for biliquid propellant.

    Returns:
        Configured RocketCEAService instance.

    Raises:
        ValueError: If configuration is invalid or registration/creation fails.
    """
    # Register custom propellant (solid/monopropellant)
    if card_string and propellant_name:
        try:
            add_new_propellant(propellant_name, card_string)
        except Exception as e:
            raise ValueError(
                f"Failed to register propellant '{propellant_name}': {e}"
            ) from e

    # Register custom oxidizer
    if oxidizer_card_string and oxidizer_name:
        try:
            add_new_oxidizer(oxidizer_name, oxidizer_card_string)
        except Exception as e:
            raise ValueError(
                f"Failed to register oxidizer '{oxidizer_name}': {e}"
            ) from e

    # Register custom fuel
    if fuel_card_string and fuel_name:
        try:
            add_new_fuel(fuel_name, fuel_card_string)
        except Exception as e:
            raise ValueError(f"Failed to register fuel '{fuel_name}': {e}") from e

    # Create CEA object
    cea_obj: CEA_Obj
    if oxidizer_name and fuel_name:
        try:
            cea_obj = CEA_Obj(oxName=oxidizer_name, fuelName=fuel_name)
        except Exception as e:
            raise ValueError(
                f"Failed to create CEA object for oxidizer '{oxidizer_name}' "
                f"and fuel '{fuel_name}'. Ensure they exist or provide card strings: {e}"
            ) from e
    elif propellant_name:
        try:
            cea_obj = CEA_Obj(propName=propellant_name)
        except Exception as e:
            raise ValueError(
                f"Failed to create CEA object for propellant '{propellant_name}'. "
                f"Ensure propellant exists or provide card_string: {e}"
            ) from e
    else:
        raise ValueError(
            "Must provide either propellant_name or (oxidizer_name and fuel_name)"
        )

    return RocketCEAService(cea_obj, oxidizer_to_fuel_ratio)


class RocketCEAService:
    """Thin wrapper around RocketCEA CEA_Obj for thermochemical queries.

    This class provides a clean interface for fetching thermochemical properties.
    Use create_cea_service() factory function to instantiate with custom propellants.
    """

    def __init__(self, cea_obj: CEA_Obj, oxidizer_to_fuel_ratio: float | None = None):
        """Initialize service with CEA object.

        Args:
            cea_obj: RocketCEA CEA_Obj instance.
            oxidizer_to_fuel_ratio: O/F ratio for biliquid propellants (optional).
        """
        self.cea_obj = cea_obj
        self.oxidizer_to_fuel_ratio = oxidizer_to_fuel_ratio

    def get_adiabatic_flame_temperature(self, chamber_pressure: float) -> float:
        """Get adiabatic flame temperature [K]."""
        chamber_pressure_psi = convert_pa_to_psi(chamber_pressure)
        if self.oxidizer_to_fuel_ratio is not None:
            temp_rankine = self.cea_obj.get_Tcomb(
                Pc=chamber_pressure_psi, MR=self.oxidizer_to_fuel_ratio
            )
        else:
            temp_rankine = self.cea_obj.get_Tcomb(Pc=chamber_pressure_psi)
        return convert_rankine_to_kelvin(temp_rankine)

    def get_chamber_properties(
        self, chamber_pressure: float, expansion_ratio: float
    ) -> tuple[float, float]:
        """Get chamber molecular weight [kg/mol] and gamma."""
        chamber_pressure_psi = convert_pa_to_psi(chamber_pressure)
        if self.oxidizer_to_fuel_ratio is not None:
            mw_g, gamma = self.cea_obj.get_Chamber_MolWt_gamma(
                Pc=chamber_pressure_psi,
                MR=self.oxidizer_to_fuel_ratio,
                eps=expansion_ratio,
            )
        else:
            mw_g, gamma = self.cea_obj.get_Chamber_MolWt_gamma(
                Pc=chamber_pressure_psi, eps=expansion_ratio
            )
        return mw_g / 1000.0, gamma

    def get_exhaust_properties(
        self, chamber_pressure: float, expansion_ratio: float
    ) -> tuple[float, float]:
        """Get exhaust molecular weight [kg/mol] and gamma (frozen flow)."""
        chamber_pressure_psi = convert_pa_to_psi(chamber_pressure)

        if self.oxidizer_to_fuel_ratio is not None:
            mw_g, gamma = self.cea_obj.get_exit_MolWt_gamma(
                Pc=chamber_pressure_psi,
                MR=self.oxidizer_to_fuel_ratio,
                eps=expansion_ratio,
                frozen=1,
            )
        else:
            mw_g, gamma = self.cea_obj.get_exit_MolWt_gamma(
                Pc=chamber_pressure_psi, eps=expansion_ratio, frozen=1
            )

        # RocketCEA can occasionally return gamma=0.0 for custom propellants when
        # requesting frozen exit gamma. Fall back to equilibrium exit gamma, and
        # if that is still invalid, fall back to throat gamma.
        if gamma <= 1.0:
            if self.oxidizer_to_fuel_ratio is not None:
                mw_g, gamma = self.cea_obj.get_exit_MolWt_gamma(
                    Pc=chamber_pressure_psi,
                    MR=self.oxidizer_to_fuel_ratio,
                    eps=expansion_ratio,
                    frozen=0,
                )
            else:
                mw_g, gamma = self.cea_obj.get_exit_MolWt_gamma(
                    Pc=chamber_pressure_psi, eps=expansion_ratio, frozen=0
                )
        if gamma <= 1.0:
            if self.oxidizer_to_fuel_ratio is not None:
                mw_g, gamma = self.cea_obj.get_Throat_MolWt_gamma(
                    Pc=chamber_pressure_psi,
                    MR=self.oxidizer_to_fuel_ratio,
                    eps=expansion_ratio,
                )
            else:
                mw_g, gamma = self.cea_obj.get_Throat_MolWt_gamma(
                    Pc=chamber_pressure_psi, eps=expansion_ratio
                )

        return mw_g / 1000.0, gamma

    def get_specific_impulse(
        self, chamber_pressure: float, expansion_ratio: float
    ) -> tuple[float, float]:
        """Get specific impulse [s]: (frozen, shifting)."""
        chamber_pressure_psi = convert_pa_to_psi(chamber_pressure)

        if self.oxidizer_to_fuel_ratio is not None:
            isp_frozen = self.cea_obj.get_Isp(
                Pc=chamber_pressure_psi,
                MR=self.oxidizer_to_fuel_ratio,
                eps=expansion_ratio,
                frozen=1,
            )
            isp_shifting = self.cea_obj.get_Isp(
                Pc=chamber_pressure_psi,
                MR=self.oxidizer_to_fuel_ratio,
                eps=expansion_ratio,
                frozen=0,
            )
        else:
            isp_frozen = self.cea_obj.get_Isp(
                Pc=chamber_pressure_psi, eps=expansion_ratio, frozenAtThroat=1
            )
            isp_shifting = self.cea_obj.get_Isp(
                Pc=chamber_pressure_psi, eps=expansion_ratio, frozen=0
            )
        return isp_frozen, isp_shifting

    def get_condensed_phase_fractions(
        self, chamber_pressure: float, expansion_ratio: float
    ) -> tuple[float, float]:
        """Get condensed phase fractions [mol/100g]: (chamber, exhaust)."""
        chamber_pressure_psi = convert_pa_to_psi(chamber_pressure)

        qsi_chamber = 0.0
        qsi_exhaust = 0.0

        try:
            species_dict, mass_fractions = self.cea_obj.get_SpeciesMassFractions(
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

    def get_tank_densities(self) -> tuple[float, float]:
        """Get tank densities [kg/m³]: (oxidizer, fuel)."""
        densities_lb_per_ft3 = self.cea_obj.get_Densities()
        return (
            convert_lbft3_to_kgm3(densities_lb_per_ft3[0]),
            convert_lbft3_to_kgm3(densities_lb_per_ft3[1]),
        )
