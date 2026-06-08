"""Thermochemical service wrapper around `rocketcea` (NASA CEA)."""

import re
from uuid import uuid4

from rocketcea.cea_obj import (
    CEA_Obj,
    add_new_fuel,
    add_new_oxidizer,
    add_new_propellant,
)

import machwave.core.conversions as conversions


def normalize_custom_propellant_name(name: str) -> str:
    """
    Normalize a custom propellant name for RocketCEA registration.

    RocketCEA internally sanitizes propellant identifiers; registering a name
    containing characters like `-` or `(` can cause lookups to fail later if
    RocketCEA normalizes it differently.

    Notes:
        Use this for custom propellant registration (`propName`), not for
        built-in oxidizer/fuel names (`oxName`/`fuelName`), which can be
        case-sensitive.
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
    has_condensed_phase: bool = True,
) -> "RocketCEAService":
    """
    Create a `RocketCEAService` and register propellants if needed.

    Handles registering custom propellants, oxidizers, and fuels with RocketCEA
    and returns a thin service wrapper. Supported configurations:

    1. Solid or monopropellant: `propellant_name` (plus optional `card_string`).
    2. Biliquid: `oxidizer_name` and `fuel_name` (plus optional card strings).
    3. Custom biliquid: custom oxidizer/fuel via card strings.

    Args:
        propellant_name: Solid or monoliquid propellant name.
        card_string: CEA card string for a custom solid/monopropellant.
        oxidizer_name: Oxidizer name for a biliquid propellant.
        oxidizer_card_string: CEA card string for a custom oxidizer.
        fuel_name: Fuel name for a biliquid propellant.
        fuel_card_string: CEA card string for a custom fuel.
        oxidizer_to_fuel_ratio: O/F ratio for a biliquid propellant.
        has_condensed_phase: Whether the propellant can form a condensed combustion
            phase. When False, condensed-phase queries are assumed 0.

    Returns:
        Configured `RocketCEAService` instance.

    Raises:
        ValueError: If configuration is invalid or registration/creation fails.
    """
    effective_propellant_name = propellant_name
    if card_string and propellant_name:
        effective_propellant_name = f"{propellant_name}__{uuid4().hex[:8]}"
        try:
            add_new_propellant(effective_propellant_name, card_string)
        except Exception as e:
            raise ValueError(
                f"Failed to register propellant '{propellant_name}': {e}"
            ) from e

    effective_oxidizer_name = oxidizer_name
    if oxidizer_card_string and oxidizer_name:
        effective_oxidizer_name = f"{oxidizer_name}__{uuid4().hex[:8]}"
        try:
            add_new_oxidizer(effective_oxidizer_name, oxidizer_card_string)
        except Exception as e:
            raise ValueError(
                f"Failed to register oxidizer '{oxidizer_name}': {e}"
            ) from e

    effective_fuel_name = fuel_name
    if fuel_card_string and fuel_name:
        effective_fuel_name = f"{fuel_name}__{uuid4().hex[:8]}"
        try:
            add_new_fuel(effective_fuel_name, fuel_card_string)
        except Exception as e:
            raise ValueError(f"Failed to register fuel '{fuel_name}': {e}") from e

    # Create CEA object
    cea_obj: CEA_Obj
    if oxidizer_name and fuel_name:
        assert effective_oxidizer_name is not None
        assert effective_fuel_name is not None
        try:
            cea_obj = CEA_Obj(
                oxName=effective_oxidizer_name, fuelName=effective_fuel_name
            )
        except Exception as e:
            raise ValueError(
                f"Failed to create CEA object for oxidizer '{oxidizer_name}' "
                f"and fuel '{fuel_name}'. Ensure they exist or provide card strings: {e}"
            ) from e
    elif propellant_name:
        assert effective_propellant_name is not None
        try:
            cea_obj = CEA_Obj(propName=effective_propellant_name)
        except Exception as e:
            raise ValueError(
                f"Failed to create CEA object for propellant '{propellant_name}'. "
                f"Ensure propellant exists or provide card_string: {e}"
            ) from e
    else:
        raise ValueError(
            "Must provide either propellant_name or (oxidizer_name and fuel_name)"
        )

    return RocketCEAService(cea_obj, oxidizer_to_fuel_ratio, has_condensed_phase)


class RocketCEAService:
    """
    Thin wrapper around RocketCEA `CEA_Obj` for thermochemical queries.

    Use `create_cea_service()` to instantiate with custom propellants.
    """

    def __init__(
        self,
        cea_obj: CEA_Obj,
        oxidizer_to_fuel_ratio: float | None = None,
        has_condensed_phase: bool = True,
    ):
        """
        Initialize the service from a configured `CEA_Obj`.

        Args:
            cea_obj: RocketCEA `CEA_Obj` instance.
            oxidizer_to_fuel_ratio: O/F ratio for biliquid propellants
                (optional).
            has_condensed_phase: Whether the propellant can form a condensed combustion
                phase. When False, condensed-phase queries are assumed 0.
        """
        self.cea_obj = cea_obj
        self.oxidizer_to_fuel_ratio = oxidizer_to_fuel_ratio
        self.has_condensed_phase = has_condensed_phase

    def _resolve_mixture_ratio(self, mixture_ratio: float | None) -> float | None:
        if mixture_ratio is not None:
            return mixture_ratio
        return self.oxidizer_to_fuel_ratio

    def get_adiabatic_flame_temperature(
        self, chamber_pressure: float, mixture_ratio: float | None = None
    ) -> float:
        """Get adiabatic flame temperature [K]."""
        chamber_pressure_psi = conversions.convert_pa_to_psi(chamber_pressure)
        mr = self._resolve_mixture_ratio(mixture_ratio)
        if mr is not None:
            temp_rankine = self.cea_obj.get_Tcomb(Pc=chamber_pressure_psi, MR=mr)
        else:
            temp_rankine = self.cea_obj.get_Tcomb(Pc=chamber_pressure_psi)
        return conversions.convert_rankine_to_kelvin(temp_rankine)

    def get_chamber_properties(
        self,
        chamber_pressure: float,
        expansion_ratio: float,
        mixture_ratio: float | None = None,
    ) -> tuple[float, float]:
        """Get chamber molecular weight [kg/mol] and isentropic exponent."""
        chamber_pressure_psi = conversions.convert_pa_to_psi(chamber_pressure)
        mr = self._resolve_mixture_ratio(mixture_ratio)
        if mr is not None:
            mw_g, k = self.cea_obj.get_Chamber_MolWt_gamma(
                Pc=chamber_pressure_psi,
                MR=mr,
                eps=expansion_ratio,
            )
        else:
            mw_g, k = self.cea_obj.get_Chamber_MolWt_gamma(
                Pc=chamber_pressure_psi, eps=expansion_ratio
            )
        return mw_g / 1000.0, k

    def get_exhaust_properties(
        self,
        chamber_pressure: float,
        expansion_ratio: float,
        mixture_ratio: float | None = None,
    ) -> tuple[float, float]:
        """Get exhaust molecular weight [kg/mol] and isentropic exponent (frozen flow)."""
        chamber_pressure_psi = conversions.convert_pa_to_psi(chamber_pressure)
        mr = self._resolve_mixture_ratio(mixture_ratio)

        if mr is not None:
            mw_g, k = self.cea_obj.get_exit_MolWt_gamma(
                Pc=chamber_pressure_psi,
                MR=mr,
                eps=expansion_ratio,
                frozen=1,
            )
        else:
            mw_g, k = self.cea_obj.get_exit_MolWt_gamma(
                Pc=chamber_pressure_psi, eps=expansion_ratio, frozen=1
            )

        # RocketCEA can occasionally return k=0.0 for custom propellants when
        # requesting frozen exit k. Fall back to equilibrium exit k, and
        # if that is still invalid, fall back to throat k.
        if k <= 1.0:
            if mr is not None:
                mw_g, k = self.cea_obj.get_exit_MolWt_gamma(
                    Pc=chamber_pressure_psi,
                    MR=mr,
                    eps=expansion_ratio,
                    frozen=0,
                )
            else:
                mw_g, k = self.cea_obj.get_exit_MolWt_gamma(
                    Pc=chamber_pressure_psi, eps=expansion_ratio, frozen=0
                )
        if k <= 1.0:
            if mr is not None:
                mw_g, k = self.cea_obj.get_Throat_MolWt_gamma(
                    Pc=chamber_pressure_psi,
                    MR=mr,
                    eps=expansion_ratio,
                )
            else:
                mw_g, k = self.cea_obj.get_Throat_MolWt_gamma(
                    Pc=chamber_pressure_psi, eps=expansion_ratio
                )

        return mw_g / 1000.0, k

    def get_specific_impulse(
        self,
        chamber_pressure: float,
        expansion_ratio: float,
        mixture_ratio: float | None = None,
    ) -> tuple[float, float]:
        """Get specific impulse [s]: (frozen, shifting)."""
        chamber_pressure_psi = conversions.convert_pa_to_psi(chamber_pressure)
        mr = self._resolve_mixture_ratio(mixture_ratio)

        if mr is not None:
            isp_frozen = self.cea_obj.get_Isp(
                Pc=chamber_pressure_psi,
                MR=mr,
                eps=expansion_ratio,
                frozen=1,
            )
            isp_shifting = self.cea_obj.get_Isp(
                Pc=chamber_pressure_psi,
                MR=mr,
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
        self,
        chamber_pressure: float,
        expansion_ratio: float,
        mixture_ratio: float | None = None,
    ) -> tuple[float, float]:
        """Get condensed phase mass fractions: (chamber, exhaust)."""
        if not self.has_condensed_phase:
            return 0.0, 0.0

        chamber_pressure_psi = conversions.convert_pa_to_psi(chamber_pressure)
        mr = self._resolve_mixture_ratio(mixture_ratio)

        qsi_chamber = 0.0
        qsi_exhaust = 0.0

        try:
            kwargs = {"Pc": chamber_pressure_psi, "eps": expansion_ratio, "frozen": 0}
            if mr is not None:
                kwargs["MR"] = mr
            species_dict, mass_fractions = self.cea_obj.get_SpeciesMassFractions(
                **kwargs
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
        """Get tank densities [kg/m^3]: (oxidizer, fuel)."""
        densities_lb_per_ft3 = self.cea_obj.get_Densities()
        return (
            conversions.convert_lbft3_to_kgm3(densities_lb_per_ft3[0]),
            conversions.convert_lbft3_to_kgm3(densities_lb_per_ft3[1]),
        )
