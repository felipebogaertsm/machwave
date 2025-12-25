"""Base formulation loader with JSON support."""

import json
from pathlib import Path

from .. import categories as propellant_categories
from .. import components as propellant_components
from .. import properties as propellant_properties


def _parse_mixture_type(data: dict) -> propellant_categories.MixtureType:
    """Parse and validate mixture_type from JSON data.

    Args:
        data: JSON data dictionary.

    Returns:
        MixtureType enum value.

    Raises:
        ValueError: If mixture_type missing or invalid.
    """
    mixture_type_str = data.get("mixture_type")
    if not mixture_type_str:
        raise ValueError("JSON must contain 'mixture_type' field")

    try:
        return propellant_categories.MixtureType(mixture_type_str.lower())
    except ValueError:
        raise ValueError(
            f"Invalid mixture_type '{mixture_type_str}'. "
            f"Must be one of: {[e.value for e in propellant_categories.MixtureType]}"
        )


def _parse_component(comp_data: dict) -> propellant_components.PropellantComponent:
    """Parse single component from JSON data.

    Args:
        comp_data: Component dictionary from JSON.

    Returns:
        PropellantComponent instance.

    Raises:
        ValueError: If component role invalid.
        KeyError: If required fields missing.
    """
    role_str = comp_data["role"].lower()
    try:
        role = propellant_components.ComponentRole(role_str)
    except ValueError:
        raise ValueError(
            f"Invalid component role '{role_str}'. "
            f"Must be one of: {[e.value for e in propellant_components.ComponentRole]}"
        )

    return propellant_components.PropellantComponent(
        name=comp_data["name"],
        role=role,
        density=comp_data["density"],
        chemical_formula=comp_data["chemical_formula"],
        enthalpy=comp_data["enthalpy"],
        initial_temperature=comp_data.get("temperature", 298.15),
    )


def _parse_components(
    data: dict, *, mixture_type: propellant_categories.MixtureType
) -> tuple[list[propellant_components.PropellantComponent], list[float] | None]:
    """Parse all components from JSON data.

    Args:
        data: JSON data dictionary.

    Returns:
        (components, mass_fractions)

        - For SOLID: mass_fractions is a list[float] aligned with components.
        - For BILIQUID: mass_fractions is None (O/F defines mixture).

    Raises:
        ValueError: If component data invalid.
    """
    components_data = data.get("components", [])
    components = [_parse_component(comp_data) for comp_data in components_data]

    if mixture_type == propellant_categories.MixtureType.SOLID:
        mass_fractions: list[float] = [
            comp_data["mass_fraction"] for comp_data in components_data
        ]
        return components, mass_fractions

    return components, None


def _parse_properties(
    data: dict,
) -> propellant_properties.ThermochemicalProperties | None:
    """Parse thermochemical properties from JSON data.

    Args:
        data: JSON data dictionary.

    Returns:
        ThermochemicalProperties instance or None if not present.

    Raises:
        KeyError: If required property fields missing.
    """
    if "properties" not in data:
        return None

    props_data = data["properties"]
    return propellant_properties.ThermochemicalProperties(
        gamma_chamber=props_data["gamma_chamber"],
        gamma_exhaust=props_data["gamma_exhaust"],
        adiabatic_flame_temperature=props_data["adiabatic_flame_temperature"],
        molecular_weight_chamber=props_data["molecular_weight_chamber"],
        molecular_weight_exhaust=props_data["molecular_weight_exhaust"],
        i_sp_frozen=props_data["i_sp_frozen"],
        i_sp_shifting=props_data["i_sp_shifting"],
        qsi_chamber=props_data["qsi_chamber"],
        qsi_exhaust=props_data["qsi_exhaust"],
    )


def _create_propellant(
    mixture_type: propellant_categories.MixtureType,
    data: dict,
    components: list[propellant_components.PropellantComponent],
    mass_fractions: list[float] | None,
    properties: propellant_properties.ThermochemicalProperties | None,
) -> propellant_categories.SolidPropellant | propellant_categories.BiliquidPropellant:
    """Create propellant instance based on mixture type.

    Args:
        mixture_type: Type of propellant mixture.
        data: JSON data dictionary.
        components: Parsed components.
        properties: Parsed properties or None.

    Returns:
        SolidPropellant or BiliquidPropellant instance.

    Raises:
        ValueError: If mixture_type unsupported.
    """
    if mixture_type == propellant_categories.MixtureType.SOLID:
        return propellant_categories.SolidPropellant(
            name=data["name"],
            components=components,
            mass_fractions=mass_fractions,
            combustion_efficiency=data.get("combustion_efficiency", 0.95),
            properties=properties,
            burn_rate_map=data.get("burn_rate_map", data.get("burn_rate", [])),
        )
    elif mixture_type == propellant_categories.MixtureType.BILIQUID:
        return propellant_categories.BiliquidPropellant(
            name=data["name"],
            components=components,
            combustion_efficiency=data.get("combustion_efficiency", 0.98),
            properties=properties,
            of_ratio=data.get("of_ratio"),
        )
    else:
        raise ValueError(f"Unsupported mixture_type: {mixture_type}")


def get_propellant_from_json(
    filepath: str | Path,
) -> propellant_categories.SolidPropellant | propellant_categories.BiliquidPropellant:
    """Load propellant formulation from JSON file.

    Args:
        filepath: Path to JSON file.

    Returns:
        SolidPropellant or BiliquidPropellant instance.

    Raises:
        ValueError: If JSON data invalid.
        FileNotFoundError: If file doesn't exist.
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"Propellant JSON file not found: {filepath}")

    with open(filepath, "r") as f:
        data = json.load(f)

    mixture_type = _parse_mixture_type(data)
    components, mass_fractions = _parse_components(data, mixture_type=mixture_type)
    properties = _parse_properties(data)
    return _create_propellant(
        mixture_type, data, components, mass_fractions, properties
    )
