from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence

import numpy as np
import numpy.typing as npt

import machwave.common.fluid_state as fluid_state_models
import machwave.core.mechanics as mechanics
import machwave.models.feed_systems.lines as line_models
import machwave.models.propellants.components as propellant_components


class FeedSystem(ABC):
    """
    Abstract base class for the feed system of a rocket engine.

    The system delivers one `PropellantLine` per propellant, keyed by line
    name, and solves every line together: a cycle couples its lines
    physically, as the stacked-tank piston ties the fuel pressure to the
    oxidizer ullage pressure.
    """

    def __init__(self, lines: Sequence[line_models.PropellantLine]):
        """
        Initialize the feed system with the lines it delivers.

        Args:
            lines: Propellant lines the system feeds, one per propellant.

        Raises:
            ValueError: If no line was given, or if two lines share a name.
        """
        self.lines: dict[str, line_models.PropellantLine] = {
            line.name: line for line in lines
        }

        if not lines:
            raise ValueError("lines must hold at least one propellant line")
        if len(self.lines) != len(lines):
            raise ValueError(
                f"line names must be unique, got {[line.name for line in lines]}"
            )

    def get_initial_propellant_mass(self) -> float:
        """Compute and return the initial propellant mass in the system [kg]."""
        return sum(line.tank.initial_fluid_mass for line in self.lines.values())

    def get_lines_with_role(
        self, role: propellant_components.ComponentRole
    ) -> tuple[line_models.PropellantLine, ...]:
        """Return every line carrying the given role, in the order they were given."""
        return tuple(line for line in self.lines.values() if line.role == role)

    def get_propellant_mass_properties(
        self, line_states: Mapping[str, line_models.LineState]
    ) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
        """
        Return the center of gravity and inertia of the propellant in every tank.

        Args:
            line_states: Fluid mass and internal energy of every line, keyed by
                line name.

        Returns:
            The center of gravity [m] in the engine frame, measured from the nozzle
            exit with positive x pointing away from the nozzle, and the 3x3 inertia
            tensor about it [kg-m^2]. With every tank empty, the center of gravity
            is NaN and the inertia zero.

        Raises:
            ValueError: If any line has no tank placement.
        """
        names = list(self.lines)
        line_mass_properties = [
            self.lines[name].get_mass_properties(line_states[name]) for name in names
        ]
        return mechanics.get_combined_mass_properties(
            masses=[line_states[name].fluid_mass for name in names],
            centers_of_gravity=[cog for cog, _ in line_mass_properties],
            moments_of_inertia=[moi for _, moi in line_mass_properties],
        )

    def get_inlet_states(
        self, line_states: Mapping[str, line_models.LineState]
    ) -> dict[str, fluid_state_models.FluidState]:
        """
        Return the state delivered to the injector inlet on every line.

        Each state is the tank fluid at the tank temperature and density, at
        the pressure that survives the path to the injector. A cycle that heats
        or works on a propellant on the way — a regenerative jacket, a pump —
        overrides this to say so.

        Args:
            line_states: Fluid mass and internal energy of every line, keyed by
                line name.

        Returns:
            Injector inlet state of every line, keyed by line name.

        Raises:
            ValueError: If any line of the system has no state.
        """
        missing = [name for name in self.lines if name not in line_states]
        if missing:
            raise ValueError(f"no line state was given for {missing}")

        inlet_pressures = self.get_inlet_pressures(line_states)

        inlet_states = {}
        for name, line in self.lines.items():
            line_state = line_states[name]
            inlet_states[name] = fluid_state_models.FluidState(
                fluid_name=line.tank.fluid_name,
                pressure=inlet_pressures[name],
                temperature=line.tank.get_temperature(
                    line_state.fluid_mass, line_state.internal_energy
                ),
                density=line.tank.get_density(
                    line_state.fluid_mass, line_state.internal_energy
                ),
            )
        return inlet_states

    @abstractmethod
    def get_inlet_pressures(
        self, line_states: Mapping[str, line_models.LineState]
    ) -> dict[str, float]:
        """
        Compute the pressure delivered to the injector inlet on every line [Pa].

        Args:
            line_states: Fluid mass and internal energy of every line, keyed by
                line name.

        Returns:
            Injector inlet pressure of every line [Pa], keyed by line name.
        """
        pass
