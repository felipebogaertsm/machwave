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


def convert_burn_rate_coefficient_to_metric(
    a_imperial: float, n: float
) -> float:
    """
    Converts the burn rate coefficient from imperial to metric units.

    Args:
        a_imperial (float): Burn rate coefficient in imperial units.
        n (float): Burn rate exponent.

    Returns:
        float: Burn rate coefficient in metric units.
    """
    return a_imperial * 25.4 / (0.0069**n)
