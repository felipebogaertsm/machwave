from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence

import machwave.common.fluid_state as fluid_state_models
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

    def get_tank_volumes(self, fluid_masses: Mapping[str, float]) -> dict[str, float]:
        """
        Return the volume the fluid of every line fills [m^3].

        Each tank fills its own volume. A cycle whose tank boundaries move, such
        as a piston between two tanks, overrides this: the volumes then follow
        from the fluid masses the lines hold.

        Args:
            fluid_masses: Fluid mass of every line [kg], keyed by line name.

        Returns:
            Volume of every line's fluid [m^3], keyed by line name.
        """
        return {name: line.tank.volume for name, line in self.lines.items()}

    def get_tank_volume_rates(
        self,
        fluid_masses: Mapping[str, float],
        mass_flows: Mapping[str, float],
    ) -> dict[str, float]:
        """
        Return the rate of change of the fluid volume of every line [m^3/s].

        Zero for every line, since each tank has a fixed volume. Cycles with moving
        tank boundaries override this.

        Args:
            fluid_masses: Fluid mass of every line [kg], keyed by line name.
            mass_flows: Mass flow leaving every line [kg/s], keyed by line name.

        Returns:
            dV/dt of every line's fluid [m^3/s], keyed by line name.
        """
        return {name: 0.0 for name in self.lines}

    def get_lines_with_role(
        self, role: propellant_components.ComponentRole
    ) -> tuple[line_models.PropellantLine, ...]:
        """Return every line carrying the given role, in the order they were given."""
        return tuple(line for line in self.lines.values() if line.role == role)

    def get_inlet_states(
        self, line_states: Mapping[str, line_models.LineState]
    ) -> dict[str, fluid_state_models.FluidState]:
        """
        Return the state at the head of every feedline.

        Each state is the tank fluid at the tank temperature and density, in
        the volume `get_tank_volumes` says it fills, at the pressure the cycle
        delivers to the feedline. It is what the injector would see with nothing
        flowing: the feedline then takes its own flow-dependent loss, which the
        simulation solves together with the injector flow. A cycle that heats or
        works on a propellant on the way, such as a regenerative jacket or a
        pump, overrides this to say so.

        Args:
            line_states: Fluid mass and internal energy of every line, keyed by
                line name.

        Returns:
            Feedline head state of every line, keyed by line name.

        Raises:
            ValueError: If any line of the system has no state.
        """
        missing = [name for name in self.lines if name not in line_states]
        if missing:
            raise ValueError(f"no line state was given for {missing}")

        inlet_pressures = self.get_inlet_pressures(line_states)
        volumes = self.get_tank_volumes(
            {name: state.fluid_mass for name, state in line_states.items()}
        )

        inlet_states = {}
        for name, line in self.lines.items():
            line_state = line_states[name]
            inlet_states[name] = fluid_state_models.FluidState(
                fluid_name=line.tank.fluid_name,
                pressure=inlet_pressures[name],
                temperature=line.tank.get_temperature(
                    line_state.fluid_mass,
                    line_state.internal_energy,
                    volume=volumes[name],
                ),
                density=line.tank.get_density(
                    line_state.fluid_mass,
                    line_state.internal_energy,
                    volume=volumes[name],
                ),
            )
        return inlet_states

    @abstractmethod
    def get_inlet_pressures(
        self, line_states: Mapping[str, line_models.LineState]
    ) -> dict[str, float]:
        """
        Compute the pressure delivered to the head of every feedline [Pa].

        The feedline resistance is not taken here: it depends on the line
        flow, which the injector sets.

        Args:
            line_states: Fluid mass and internal energy of every line, keyed by
                line name.

        Returns:
            Feedline head pressure of every line [Pa], keyed by line name.
        """
        pass
