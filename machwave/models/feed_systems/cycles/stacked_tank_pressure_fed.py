from collections.abc import Mapping, Sequence

import machwave.models.feed_systems.base as feed_system_base
import machwave.models.feed_systems.lines as line_models
import machwave.models.feed_systems.tank as tank
import machwave.models.propellants.components as propellant_components


class StackedTankPressureFedFeedSystem(feed_system_base.FeedSystem):
    """
    Pressure-fed feed system whose propellant tanks are stacked vertically.

    The tank at the top of the stack pressurizes every tank below it through a
    piston, so one tank sets the pressure the whole system runs on.
    """

    def __init__(
        self,
        lines: Sequence[line_models.PropellantLine],
        pressurizing_line: str,
        piston_loss: float = 0.0,
    ):
        """
        Initialize the StackedTankPressureFedFeedSystem.

        Args:
            lines: Propellant lines the system feeds, one per propellant.
            pressurizing_line: Name of the line at the top of the stack, whose
                tank pressure drives every line.
            piston_loss: Pressure loss across the piston [Pa], taken by every
                line below the top of the stack. It is the seal friction, so it
                holds whatever the flow.

        Raises:
            ValueError: If the pressurizing line is not one of the lines, or if
                the piston loss is negative.
        """
        super().__init__(lines)

        self.pressurizing_line = pressurizing_line
        self.piston_loss = piston_loss

        self._validate()

    @classmethod
    def from_oxidizer_and_fuel(
        cls,
        *,
        oxidizer_tank: tank.Tank,
        fuel_tank: tank.Tank,
        piston_loss: float = 0.0,
        oxidizer_line_resistance: line_models.FeedlineResistance | None = None,
        fuel_line_resistance: line_models.FeedlineResistance | None = None,
    ) -> "StackedTankPressureFedFeedSystem":
        """
        Build the two-line system a biliquid engine runs on.

        The oxidizer sits at the top of the stack and pressurizes the fuel
        through the piston. The lines are named "oxidizer" and "fuel", which is
        how the injector and the simulation state key them.

        Args:
            oxidizer_tank: Tank the oxidizer line draws from.
            fuel_tank: Tank the fuel line draws from.
            piston_loss: Pressure loss across the piston [Pa].
            oxidizer_line_resistance: Hydraulic resistance of the oxidizer
                feedline. None for a line that loses nothing.
            fuel_line_resistance: Hydraulic resistance of the fuel feedline.
                None for a line that loses nothing.
        """
        return cls(
            lines=[
                line_models.PropellantLine(
                    name="oxidizer",
                    role=propellant_components.ComponentRole.OXIDIZER,
                    tank=oxidizer_tank,
                    resistance=oxidizer_line_resistance,
                ),
                line_models.PropellantLine(
                    name="fuel",
                    role=propellant_components.ComponentRole.FUEL,
                    tank=fuel_tank,
                    resistance=fuel_line_resistance,
                ),
            ],
            pressurizing_line="oxidizer",
            piston_loss=piston_loss,
        )

    def _validate(self) -> None:
        if self.pressurizing_line not in self.lines:
            raise ValueError(
                f"pressurizing_line {self.pressurizing_line!r} is not one of the "
                f"lines, got {list(self.lines)}"
            )

        if self.piston_loss < 0.0:
            raise ValueError(
                f"piston_loss must be non-negative, got {self.piston_loss}"
            )

    def get_inlet_pressures(
        self, line_states: Mapping[str, line_models.LineState]
    ) -> dict[str, float]:
        """
        Return the pressure at the head of every feedline [Pa].

        The line at the top of the stack starts at its tank pressure; every
        line below the piston starts the piston pressure loss lower.

        Args:
            line_states: Fluid mass and internal energy of every line, keyed by
                line name.

        Returns:
            Feedline head pressure of every line [Pa], keyed by line name.
        """
        pressurizing_state = line_states[self.pressurizing_line]
        stack_pressure = self.lines[self.pressurizing_line].tank.get_pressure(
            pressurizing_state.fluid_mass, pressurizing_state.internal_energy
        )

        return {
            name: stack_pressure
            - (0.0 if name == self.pressurizing_line else self.piston_loss)
            for name in self.lines
        }
