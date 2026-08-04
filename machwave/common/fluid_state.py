import dataclasses


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class FluidState:
    """
    A fluid at one thermodynamic state point.

    Density travels with the pressure and temperature rather than being derived
    from them, because on the saturation curve the two do not fix it. Whoever
    evaluated the state carries the density it landed on.

    Attributes:
        fluid_name: Name of the fluid in the CoolProp database.
        pressure: Pressure [Pa].
        temperature: Temperature [K].
        density: Density [kg/m^3].
    """

    fluid_name: str
    pressure: float
    temperature: float
    density: float
