import scipy.constants


def convert_pa_to_psi(pressure_pa: float) -> float:
    """
    Converts pressure in Pascal to psi.

    Args:
        pressure_pa: Pressure [Pa].

    Returns:
        Pressure [psi].
    """
    return pressure_pa / scipy.constants.psi


def convert_pa_to_mpa(pressure_pa: float) -> float:
    """
    Converts pressure in Pascal to MPa.

    Args:
        pressure_pa: Pressure [Pa].

    Returns:
        Pressure [MPa].
    """
    return pressure_pa * 1e-6


def convert_mpa_to_pa(pressure_mpa: float) -> float:
    """
    Converts pressure in MPa to Pascal.

    Args:
        pressure_mpa: Pressure [MPa].

    Returns:
        Pressure [Pa].
    """
    return pressure_mpa / 1e-6


def convert_mass_flux_metric_to_imperial(mass_flux_metric: float) -> float:
    """
    Converts mass flux in kg/s-m-m to lb/s-in-in.

    Args:
        mass_flux_metric: Mass flux [kg/s-m-m].

    Returns:
        Mass flux [lb/s-in-in].
    """
    return mass_flux_metric * 1.42233e-3


def convert_burn_rate_coefficient_to_metric(a_imperial: float, n: float) -> float:
    """
    Converts burn rate coefficient from imperial to metric units.

    Args:
        a_imperial: Burn rate coefficient in imperial units [in/s/(lb/in^2)^n].
        n: Burn rate exponent.

    Returns:
        Burn rate coefficient in metric units [m/s/(kg/m^2)^n].
    """
    return a_imperial * 25.4 / (0.0069**n)


def convert_rankine_to_kelvin(temperature_rankine: float) -> float:
    """
    Converts temperature in Rankine to Kelvin.

    Args:
        temperature_rankine: Temperature [R].

    Returns:
        Temperature [K].
    """
    return temperature_rankine * 5 / 9


def convert_lbft3_to_kgm3(density_lbft3: float) -> float:
    """
    Converts density in lb/ft³ to kg/m³.

    Args:
        density_lbft3: Density [lb/ft³].

    Returns:
        Density [kg/m³].
    """
    return density_lbft3 * 16.01846337


def convert_meter_to_inch(measure: float) -> float:
    """
    Converts distance in meters to inches.

    Args:
        measure: Distance [m].

    Returns:
        Distance in inches.
    """
    return measure / 0.0254


def convert_meter_to_micrometer(measure: float) -> float:
    """
    Converts distance in meters to micrometers.

    Args:
        measure: Distance [m].

    Returns:
        Distance in micrometers.
    """
    return measure * 1e6


def convert_joules_per_mol_to_cal_per_mol(enthalpy_j_per_mol: float) -> float:
    """
    Converts enthalpy in J/mol to cal/mol.

    Args:
        enthalpy_j_per_mol: Enthalpy [J/mol].

    Returns:
        Enthalpy in cal/mol.
    """
    return enthalpy_j_per_mol / 4.184


def convert_kgm3_to_gcc(density_kgm3: float) -> float:
    """
    Converts density in kg/m^3 to g/cc.

    Args:
        density_kgm3: Density [kg/m^3].

    Returns:
        Density in g/cc.
    """
    return density_kgm3 / 1000.0
