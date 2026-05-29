import scipy.constants


def get_pressure(
    mass: float,
    volume: float,
    temperature: float,
    molar_mass: float,
) -> float:
    """
    Get the pressure of an ideal gas occupying a fixed volume.

    Args:
        mass: Mass of gas [kg].
        volume: Volume available to the gas [m^3].
        temperature: Absolute temperature [K].
        molar_mass: Molar mass of the gas [kg/mol].

    Returns:
        Pressure [Pa].
    """
    moles = mass / molar_mass
    return moles * scipy.constants.R * temperature / volume


def get_mass(
    pressure: float,
    volume: float,
    temperature: float,
    molar_mass: float,
) -> float:
    """
    Get the mass of an ideal gas filling a volume at a given pressure.

    Args:
        pressure: Gas pressure [Pa].
        volume: Volume available to the gas [m^3].
        temperature: Absolute temperature [K].
        molar_mass: Molar mass of the gas [kg/mol].

    Returns:
        Mass [kg].
    """
    return pressure * volume * molar_mass / (scipy.constants.R * temperature)
