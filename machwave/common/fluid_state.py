import dataclasses


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class FluidState:
    """
    A fluid at a thermodynamic state point.

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
