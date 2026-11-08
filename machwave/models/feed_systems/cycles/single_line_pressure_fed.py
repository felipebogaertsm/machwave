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

    def __init__(
        self,
        line: line_models.PropellantLine,
        line_loss: float = 0.0,
    ):
        """
        Initialize the SingleLinePressureFedFeedSystem.

        Args:
            line: The propellant line the system feeds.
            line_loss: Pressure loss along the feedline [Pa], stated for the
                design flow rather than computed from it.

        Raises:
            ValueError: If the pressure loss is negative.
        """
        super().__init__([line])

        self.line_loss = line_loss

        if line_loss < 0.0:
            raise ValueError(f"line_loss must be non-negative, got {line_loss}")

    @classmethod
    def from_oxidizer_tank(
        cls,
        *,
        oxidizer_tank: tank.Tank,
        line_loss: float = 0.0,
    ) -> "SingleLinePressureFedFeedSystem":
        """
        Build the oxidizer-only system a hybrid motor runs on.

        Args:
            oxidizer_tank: Tank the oxidizer line draws from.
            line_loss: Pressure loss along the feedline [Pa].
        """
        return cls(
            line=line_models.PropellantLine(
                name="oxidizer",
                role=propellant_components.ComponentRole.OXIDIZER,
                tank=oxidizer_tank,
            ),
            line_loss=line_loss,
        )

    @property
    def line(self) -> line_models.PropellantLine:
        """The one line the system feeds."""
        return next(iter(self.lines.values()))

    def get_inlet_pressures(
        self, line_states: Mapping[str, line_models.LineState]
    ) -> dict[str, float]:
        """
        Return the tank pressure less the feedline loss [Pa], keyed by line name.

        Args:
            line_states: Fluid mass and internal energy of the line, keyed by
                line name.
        """
        line_state = line_states[self.line.name]

        return {
            self.line.name: self.line.tank.get_pressure(
                line_state.fluid_mass, line_state.internal_energy
            )
            - self.line_loss
        }
