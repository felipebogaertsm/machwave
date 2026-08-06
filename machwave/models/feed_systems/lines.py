"""Propellant lines and the state the integrator carries for each of them."""

import dataclasses

import machwave.models.feed_systems.tank as tank_models
import machwave.models.propellants.components as propellant_components


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class LineState:
    """
    The propellant a line still holds at one point in the integration.

    Attributes:
        fluid_mass: Mass of fluid left in the tank [kg].
        internal_energy: Internal energy of that fluid [J]. None for an
            isothermal tank, which runs no energy balance.
    """

    fluid_mass: float
    internal_energy: float | None = None

    def __post_init__(self) -> None:
        if self.fluid_mass < 0.0:
            raise ValueError(f"fluid_mass must be non-negative, got {self.fluid_mass}")


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class PropellantLine:
    """
    One propellant on its way from a tank to the injector.

    Attributes:
        name: Line name, which keys the line across the feed system, the
            injector and the simulation state.
        role: Whether the line carries an oxidizer, a fuel, or an additive such
            as a triliquid diluent or a coolant.
        tank: Tank the line draws from.
    """

    name: str
    role: propellant_components.ComponentRole
    tank: tank_models.Tank

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name must be a non-empty string")

        object.__setattr__(self, "role", propellant_components.ComponentRole(self.role))

    @property
    def initial_state(self) -> LineState:
        """The line state the integrator starts from, as the tank was loaded."""
        return LineState(
            fluid_mass=self.tank.initial_fluid_mass,
            internal_energy=(
                None if self.tank.isothermal else self.tank.initial_internal_energy
            ),
        )
