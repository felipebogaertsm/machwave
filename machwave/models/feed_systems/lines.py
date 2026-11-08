"""Propellant lines and the state the integrator carries for each of them."""

import dataclasses

import numpy as np
import numpy.typing as npt

import machwave.core.geometric as geometric
import machwave.core.mechanics as mechanics
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
class TankPlacement:
    """
    The cylinder a tank spans and where it sits along the engine axis.

    Attributes:
        inner_diameter: Tank inner diameter [m]. The tank length follows from the
            tank volume.
        nozzle_exit_to_aft_end_distance: Axial distance from the nozzle exit plane to
            the aft end of the tank, the end nearest the nozzle [m]. Shifts the
            propellant mass properties into the engine frame, whose origin is the
            nozzle exit.
    """

    inner_diameter: float
    nozzle_exit_to_aft_end_distance: float

    def __post_init__(self) -> None:
        """
        Validate the tank geometry and placement.

        Raises:
            ValueError: If the inner diameter is not strictly positive, or if the
                nozzle exit to aft end distance is negative.
        """
        if self.inner_diameter <= 0.0:
            raise ValueError(
                f"inner_diameter must be strictly positive, got {self.inner_diameter}"
            )
        if self.nozzle_exit_to_aft_end_distance < 0.0:
            raise ValueError(
                "nozzle_exit_to_aft_end_distance must be non-negative, got "
                f"{self.nozzle_exit_to_aft_end_distance}"
            )

    def get_length(self, volume: float) -> float:
        """Return the length of the tank that holds the given volume [m]."""
        return volume / geometric.get_circle_area(self.inner_diameter)


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
        tank_placement: Geometry and position of the tank in the engine. Optional,
            not used by the internal ballistics simulation.
    """

    name: str
    role: propellant_components.ComponentRole
    tank: tank_models.Tank
    tank_placement: TankPlacement | None = None

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

    def get_mass_properties(
        self, line_state: LineState
    ) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
        """
        Return the center of gravity and inertia of the propellant in the tank.

        Assumes the engine accelerates along its axis, so the liquid is settled at
        the aft end of the tank and the vapor fills the ullage ahead of it. Each
        phase is a uniform solid cylinder spanning the tank bore, with the phase
        split and liquid density from the tank model. Sloshing, tank walls, domes
        and any internal hardware are ignored. A fill denser than the saturated
        liquid, within the tank overfill tolerance, is all liquid.

        Validation status: verified against the closed-form cylinder and
        parallel axis results, not validated.

        References:
            Meriam, J. L., & Kraige, L. G. (2012). *Engineering Mechanics:
            Dynamics* (7th ed.). Wiley. Appendix B (parallel-axis theorem) and
            Appendix D, Table D/4 (circular cylinder).

        Args:
            line_state: Fluid mass and internal energy of the line.

        Returns:
            The center of gravity [m] in the engine frame, measured from the nozzle
            exit with positive x pointing away from the nozzle, and the 3x3 inertia
            tensor about it [kg-m^2]. An empty tank gives a NaN center of gravity
            and zero inertia.

        Raises:
            ValueError: If the line has no tank placement.
        """
        tank_placement = self.tank_placement
        if tank_placement is None:
            raise ValueError(f"line {self.name!r} has no tank_placement")

        fluid_mass = line_state.fluid_mass
        internal_energy = line_state.internal_energy
        tank_length = tank_placement.get_length(self.tank.volume)

        liquid_mass = min(
            self.tank.get_liquid_mass(fluid_mass, internal_energy), fluid_mass
        )
        liquid_length = 0.0
        if liquid_mass > 0.0:
            liquid_volume = liquid_mass / self.tank.get_density(
                fluid_mass, internal_energy
            )
            liquid_length = tank_length * min(liquid_volume / self.tank.volume, 1.0)

        tank_radius = tank_placement.inner_diameter / 2
        aft_end = tank_placement.nozzle_exit_to_aft_end_distance
        vapor_mass = fluid_mass - liquid_mass
        vapor_length = tank_length - liquid_length
        return mechanics.get_combined_mass_properties(
            masses=(liquid_mass, vapor_mass),
            centers_of_gravity=(
                np.array([aft_end + liquid_length / 2, 0.0, 0.0]),
                np.array([aft_end + liquid_length + vapor_length / 2, 0.0, 0.0]),
            ),
            moments_of_inertia=(
                mechanics.get_solid_cylinder_moment_of_inertia(
                    liquid_mass, liquid_length, tank_radius
                ),
                mechanics.get_solid_cylinder_moment_of_inertia(
                    vapor_mass, vapor_length, tank_radius
                ),
            ),
        )
