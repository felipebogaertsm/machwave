"""
Chemical components of a propellant formulation.

Provides classes representing the role and properties of each component.
"""

import dataclasses
import enum

import machwave.core.conversions as conversions


class ComponentRole(enum.StrEnum):
    """Role of a chemical component in the propellant formulation."""

    OXIDIZER = "oxidizer"
    FUEL = "fuel"  # Includes binders (HTPB, PBAN, etc.)
    ADDITIVE = "additive"


# CEA gives the ideal gas its heat of formation at this temperature
_CEA_REFERENCE_TEMPERATURE = 298.15  # [K]


@dataclasses.dataclass(kw_only=True)
class PropellantComponent:
    """
    Chemical component of a propellant formulation.

    Attributes:
        name: Component name (i.e., "KNO3", "LOX", "HTPB").
        role: Component role (oxidizer, fuel, additive).
        density: Component density [kg/m^3].
        chemical_formula: Element symbols to atom counts (i.e., {"H": 2, "O": 1}).
        enthalpy: Molar enthalpy at `initial_temperature`, on the CEA scale
            where each element is zero at 298.15 K, so at 298.15 K it is the
            standard enthalpy of formation [J/mol].
        initial_temperature: Initial component temperature before combustion [K].
        custom_card: Whether a biliquid propellant builds a CEA reactant card
            from this component's formula, enthalpy, initial temperature and
            density. When False, `name` is looked up in RocketCEA's built-in
            cards and those fields are ignored. Solid propellants always build
            their card from the fields.
    """

    name: str
    role: ComponentRole
    density: float
    chemical_formula: dict[str, int]
    enthalpy: float
    initial_temperature: float = _CEA_REFERENCE_TEMPERATURE
    custom_card: bool = False

    def to_cea_dict(self, *, weight_percent: float) -> dict:
        """
        Convert component to CEA-compatible dictionary format.

        Args:
            weight_percent: Component weight percent in the mixture [%].

        Returns:
            CEA format with name, formula, weight_percent,
            heat_of_formation (cal/mol), temperature [K], and density [g/cc].
        """
        heat_of_formation_cal = conversions.convert_joules_per_mol_to_cal_per_mol(
            self.enthalpy
        )
        density_gcc = conversions.convert_kgm3_to_gcc(self.density)

        return {
            "name": self.name,
            "formula": self.chemical_formula,
            "weight_percent": weight_percent,
            "heat_of_formation": heat_of_formation_cal,
            "temperature": self.initial_temperature,
            "density": density_gcc,
        }


# from the CEA thermo library (Gurvich, 1989) rather than JANAF, so the reactant
# sits on the same enthalpy scale as the combustion products
NITROUS_OXIDE_GAS_HEAT_OF_FORMATION = 81600.0  # [J/mol]

# low enough that the real-gas enthalpy matches the ideal gas to well under 1 J/mol
_IDEAL_GAS_REFERENCE_PRESSURE = 1.0  # [Pa]


def saturated_liquid_nitrous_oxide(temperature: float) -> PropellantComponent:
    """
    Build an N2O oxidizer component as saturated liquid at a tank temperature.

    RocketCEA's built-in "N2O" card is the ideal gas at 298.15 K. A self-pressurized
    tank feeds saturated liquid, whose enthalpy is lower by roughly the heat of
    vaporization, so the built-in card overstates flame temperature, characteristic
    velocity and specific impulse. The injector is taken as adiabatic, so the chamber
    receives the tank liquid enthalpy whatever the liquid flashes to on the way.

    On the CEA enthalpy scale, the molar enthalpy is the gas heat of formation at
    298.15 K plus the CoolProp enthalpy change from that ideal-gas state to saturated
    liquid at `temperature`:

        h = h_f(N2O gas, 298.15 K) + [h_sat_liq(T) - h_ideal_gas(298.15 K)]

    The card is fixed at `temperature` and does not follow a tank that cools during
    the burn.

    Validation status: verified, not validated. At 184.4 K the enthalpy is within
    about 100 J/mol of RocketCEA's independent "N2O_nbp" liquid card.

    Args:
        temperature: Liquid temperature in the tank at loading [K].

    Returns:
        Oxidizer component with `custom_card` set.

    Raises:
        ValueError: If `temperature` is not between the triple point and the
            critical point of N2O.
        MissingOptionalDependencyError: If the `liquid` extra is not installed.

    References:
        Gordon, S., & McBride, B. J. (1994). Computer Program for Calculation of
        Complex Chemical Equilibrium Compositions and Applications (NASA RP-1311),
        Eq. 4.2.
    """
    import machwave.services.coolprop as coolprop_service

    fluid = coolprop_service.CoolPropService("NitrousOxide")
    triple_point_temperature = fluid.get_triple_point_temperature()
    critical_temperature = fluid.get_critical_temperature()
    if not (triple_point_temperature <= temperature < critical_temperature):
        raise ValueError(
            "N2O saturated-liquid temperature must be between "
            f"{triple_point_temperature:.2f} K and {critical_temperature:.2f} K, "
            f"got {temperature} K"
        )

    molar_mass = fluid.get_molar_mass()
    ideal_gas_reference_enthalpy = fluid.get_enthalpy_at_temperature_pressure(
        _CEA_REFERENCE_TEMPERATURE, _IDEAL_GAS_REFERENCE_PRESSURE
    )
    liquid_enthalpy = fluid.get_saturated_liquid_enthalpy(temperature)
    enthalpy = NITROUS_OXIDE_GAS_HEAT_OF_FORMATION + molar_mass * (
        liquid_enthalpy - ideal_gas_reference_enthalpy
    )

    return PropellantComponent(
        name="N2O(L)",
        role=ComponentRole.OXIDIZER,
        density=fluid.get_saturated_liquid_density(temperature),
        chemical_formula={"N": 2, "O": 1},
        enthalpy=enthalpy,
        initial_temperature=temperature,
        custom_card=True,
    )
