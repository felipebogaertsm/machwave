def convert_pa_to_psi(pressure_pa: float) -> float:
    """
    Converts Pascal pressure to PSI.

    Args:
        pressure_pa (float): Pressure in Pascal.

    Returns:
        float: Pressure in PSI.
    """
    return pressure_pa * 1.45e-4


def convert_pa_to_mpa(pressure_pa: float) -> float:
    """
    Converts Pascal pressure to MPa.

    Args:
        pressure_pa (float): Pressure in Pascal.

    Returns:
        float: Pressure in MPa.
    """
    return pressure_pa * 1e-6


def convert_mpa_to_pa(pressure_mpa: float) -> float:
    """
    Converts MPa pressure to Pascal.

    Args:
        pressure_mpa (float): Pressure in MPa.

    Returns:
        float: Pressure in Pascal.
    """
    return pressure_mpa / 1e-6


def convert_mass_flux_metric_to_imperial(mass_flux_metric: float) -> float:
    """
    Converts a mass flux in kg/s-m-m to lb/s-in-in.

    Args:
        mass_flux_metric (float): Mass flux in kg/s-m-m.

    Returns:
        float: Mass flux in lb/s-in-in.
    """
    return mass_flux_metric * 1.42233e-3


def convert_burn_rate_coefficient_to_metric(a_imperial: float, n: float) -> float:
    """
    Converts the burn rate coefficient from imperial to metric units.

    Args:
        a_imperial (float): Burn rate coefficient in imperial units.
        n (float): Burn rate exponent.

    Returns:
        float: Burn rate coefficient in metric units.
    """
    return a_imperial * 25.4 / (0.0069**n)


def convert_rankine_to_kelvin(temperature_rankine: float) -> float:
    """
    Converts temperature from Rankine to Kelvin.

    Args:
        temperature_rankine (float): Temperature in Rankine.

    Returns:
        float: Temperature in Kelvin.
    """
    return temperature_rankine * 5 / 9


def convert_lbft3_to_kgm3(density_lbft3: float) -> float:
    """
    Converts density from lb/ft³ to kg/m³.

    Args:
        density_lbft3 (float): Density in lb/ft³.

    Returns:
        float: Density in kg/m³.
    """
    return density_lbft3 * 16.01846337


def convert_meter_to_inch(measure: float) -> float:
    """
    Converts length from meters to inches.

    Args:
        measure (float): Length in meters.

    Returns:
        float: Size in inches.
    """
    return measure / 0.0254


def convert_meter_to_micrometer(measure: float) -> float:
    """
    Converts from meters to micrometers.

    Args:
        measure (float): Size in meters.
    Returns:
        float: Length in micrometers.
    """
    return measure * 1e6


def convert_joules_per_mol_to_cal_per_mol(enthalpy_j_per_mol: float) -> float:
    """
    Converts enthalpy from J/mol to cal/mol.

    Args:
        enthalpy_j_per_mol (float): Enthalpy in J/mol.

    Returns:
        float: Enthalpy in cal/mol.
    """
    return enthalpy_j_per_mol / 4.184


def convert_kgm3_to_gcc(density_kgm3: float) -> float:
    """
    Converts density from kg/m³ to g/cc.

    Args:
        density_kgm3 (float): Density in kg/m³.

    Returns:
        float: Density in g/cc.
    """
    return density_kgm3 / 1000.0
