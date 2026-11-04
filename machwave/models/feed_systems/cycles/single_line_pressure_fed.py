from collections.abc import Mapping

import machwave.models.feed_systems.base as feed_system_base
import machwave.models.feed_systems.lines as line_models
import machwave.models.feed_systems.tank as tank
import machwave.models.propellants.components as propellant_components


class SingleLinePressureFedFeedSystem(feed_system_base.FeedSystem):
    """
    Pressure-fed feed system delivering a single propellant line.

    The tank pressurizes itself: a self-pressurized propellant rides its own
    vapor pressure while liquid remains, and blows down on the real-gas
    equation of state once none does. This is the one-line case of the feed
    system contract, which an oxidizer-only hybrid feed and a monoliquid engine
    both run on.
    """

    def __init__(self, line: line_models.PropellantLine):
        """
        Initialize the SingleLinePressureFedFeedSystem.

        Args:
            line: The propellant line the system feeds. Its feedline
                resistance sets what the line loses on the way to the
                injector.
        """
        super().__init__([line])

    @classmethod
    def from_oxidizer_tank(
        cls,
        *,
        oxidizer_tank: tank.Tank,
        line_resistance: line_models.FeedlineResistance | None = None,
    ) -> "SingleLinePressureFedFeedSystem":
        """
        Build the oxidizer-only system a hybrid motor runs on.

        Args:
            oxidizer_tank: Tank the oxidizer line draws from.
            line_resistance: Hydraulic resistance of the oxidizer feedline.
                None for a line that loses nothing.
        """
        return cls(
            line=line_models.PropellantLine(
                name="oxidizer",
                role=propellant_components.ComponentRole.OXIDIZER,
                tank=oxidizer_tank,
                resistance=line_resistance,
            )
        )

    @property
    def line(self) -> line_models.PropellantLine:
        """The one line the system feeds."""
        return next(iter(self.lines.values()))

    def get_inlet_pressures(
        self, line_states: Mapping[str, line_models.LineState]
    ) -> dict[str, float]:
        """
        Return the tank pressure [Pa], keyed by line name.

        Args:
            line_states: Fluid mass and internal energy of the line, keyed by
                line name.
        """
        line_state = line_states[self.line.name]

        return {
            self.line.name: self.line.tank.get_pressure(
                line_state.fluid_mass, line_state.internal_energy
            )
        }
