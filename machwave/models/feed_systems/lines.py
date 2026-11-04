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
class FeedlineResistance:
    """
    Hydraulic resistance of the plumbing between a tank and the injector.

    The line loses pressure with the square of its flow, as a turbulent
    liquid line does:

        dP = K * mdot^2 / (2 * rho * A^2)

    K lumps the friction of the run (f * L / D) and the minor losses of every
    fitting and valve on it, all referred to the same flow area A.

    Attributes:
        loss_coefficient: Total loss coefficient K, referred to the flow area
            (dimensionless).
        flow_area: Flow area the loss coefficient is referred to [m^2].
    """

    loss_coefficient: float
    flow_area: float

    def __post_init__(self) -> None:
        if self.loss_coefficient < 0.0:
            raise ValueError(
                f"loss_coefficient must be non-negative, got {self.loss_coefficient}"
            )
        if self.flow_area <= 0.0:
            raise ValueError(
                f"flow_area must be strictly positive, got {self.flow_area}"
            )

    @classmethod
    def from_design_point(
        cls,
        *,
        pressure_drop: float,
        mass_flow: float,
        density: float,
        flow_area: float,
    ) -> "FeedlineResistance":
        """
        Build the resistance that drops a stated pressure at a design flow.

        Away from that flow the drop scales as (mdot / mdot_design)^2 *
        rho_design / rho.

        Args:
            pressure_drop: Line pressure drop at the design point [Pa].
            mass_flow: Design mass flow [kg/s].
            density: Fluid density at the design point [kg/m^3].
            flow_area: Flow area the loss coefficient is referred to [m^2].

        Raises:
            ValueError: If the pressure drop is negative, or if the design
                mass flow, the density or the flow area is not strictly
                positive.
        """
        if pressure_drop < 0.0:
            raise ValueError(f"pressure_drop must be non-negative, got {pressure_drop}")
        if mass_flow <= 0.0:
            raise ValueError(f"mass_flow must be strictly positive, got {mass_flow}")
        if density <= 0.0:
            raise ValueError(f"density must be strictly positive, got {density}")

        return cls(
            loss_coefficient=2.0
            * density
            * flow_area**2
            * pressure_drop
            / mass_flow**2,
            flow_area=flow_area,
        )

    def get_pressure_drop(self, mass_flow: float, density: float) -> float:
        """
        Pressure the line loses at the given flow [Pa].

        Args:
            mass_flow: Mass flow through the line [kg/s].
            density: Density of the fluid in the line [kg/m^3].

        Returns:
            Pressure drop along the line [Pa]. Zero when the line is not
            flowing.

        Raises:
            ValueError: If the mass flow is negative, or if the density is not
                strictly positive while the line is flowing.
        """
        if mass_flow < 0.0:
            raise ValueError(f"mass_flow must be non-negative, got {mass_flow}")
        if mass_flow == 0.0:
            return 0.0
        if density <= 0.0:
            raise ValueError(f"density must be strictly positive, got {density}")

        return (
            self.loss_coefficient * mass_flow**2 / (2.0 * density * self.flow_area**2)
        )


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
        resistance: Hydraulic resistance of the feedline from the tank to the
            injector. None for a line that loses nothing on the way.
    """

    name: str
    role: propellant_components.ComponentRole
    tank: tank_models.Tank
    resistance: FeedlineResistance | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name must be a non-empty string")

        object.__setattr__(self, "role", propellant_components.ComponentRole(self.role))

    def get_pressure_drop(self, mass_flow: float, density: float) -> float:
        """
        Pressure the feedline loses at the given flow [Pa].

        Args:
            mass_flow: Mass flow through the line [kg/s].
            density: Density of the fluid in the line [kg/m^3].
        """
        if self.resistance is None:
            return 0.0
        return self.resistance.get_pressure_drop(mass_flow, density)

    @property
    def initial_state(self) -> LineState:
        """The line state the integrator starts from, as the tank was loaded."""
        return LineState(
            fluid_mass=self.tank.initial_fluid_mass,
            internal_energy=(
                None if self.tank.isothermal else self.tank.initial_internal_energy
            ),
        )
