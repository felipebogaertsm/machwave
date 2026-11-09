import warnings
from collections.abc import Mapping, Sequence

import machwave.models.feed_systems.base as feed_system_base
import machwave.models.feed_systems.lines as line_models
import machwave.models.feed_systems.tank as tank
import machwave.models.propellants.components as propellant_components


LINE_LOSSES_DEPRECATION_MESSAGE = (
    "fixed line losses are deprecated and will be removed; give each line a "
    "FeedlineResistance, whose loss grows with the square of the flow"
)


class StackedTankPressureFedFeedSystem(feed_system_base.FeedSystem):
    """
    Pressure-fed feed system whose propellant tanks are stacked vertically.

    The tank at the top of the stack pressurizes every tank below it through a
    piston, so one tank sets the pressure the whole system runs on.

    As the lines below the piston drain, the fluid at the top of the stack fills its
    tank volume plus the liquid volume pushed out below. The top tank does boundary
    work on the piston. Tanks below the piston must be isothermal, because they stay
    liquid-full at their loading temperature.

    References:
        Cengel, Y. A., & Boles, M. A. (2015). Thermodynamics: An Engineering
        Approach, 8th ed., Ch. 5.
    """

    def __init__(
        self,
        lines: Sequence[line_models.PropellantLine],
        pressurizing_line: str,
        piston_loss: float = 0.0,
        line_losses: Mapping[str, float] | None = None,
    ):
        """
        Initialize the StackedTankPressureFedFeedSystem.

        Args:
            lines: Propellant lines the system feeds, one per propellant.
            pressurizing_line: Name of the line at the top of the stack, whose
                tank pressure drives every line.
            piston_loss: Pressure loss across the piston [Pa], taken by every
                line below the top of the stack.
            line_losses: Deprecated. Fixed pressure loss along each feedline [Pa],
                keyed by line name. A line left out takes no loss. Give each line a
                `FeedlineResistance` instead.

        Raises:
            ValueError: If the pressurizing line is not one of the lines, if a
                loss is keyed by an unknown line, if any pressure loss is
                negative, or if a tank below the piston is not isothermal.
        """
        super().__init__(lines)

        self.pressurizing_line = pressurizing_line
        self.piston_loss = piston_loss
        self.line_losses = {name: 0.0 for name in self.lines}
        if line_losses is not None:
            warnings.warn(
                LINE_LOSSES_DEPRECATION_MESSAGE, DeprecationWarning, stacklevel=2
            )
            self.line_losses |= dict(line_losses)

        self._validate_pressure_losses()

        for name in self.lower_line_names:
            if not self.lines[name].tank.isothermal:
                raise ValueError(
                    f"line {name!r} is below the piston, which holds it "
                    "liquid-full at its loading temperature; its tank must be "
                    "built with isothermal=True"
                )

    @classmethod
    def from_oxidizer_and_fuel(
        cls,
        *,
        oxidizer_tank: tank.Tank,
        fuel_tank: tank.Tank,
        piston_loss: float = 0.0,
        oxidizer_line_resistance: line_models.FeedlineResistance | None = None,
        fuel_line_resistance: line_models.FeedlineResistance | None = None,
        oxidizer_line_loss: float | None = None,
        fuel_line_loss: float | None = None,
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
            oxidizer_line_resistance: Hydraulic resistance of the oxidizer feedline.
                None for a line that loses nothing.
            fuel_line_resistance: Hydraulic resistance of the fuel feedline. None for
                a line that loses nothing.
            oxidizer_line_loss: Deprecated. Fixed pressure loss along the oxidizer
                feedline [Pa]. Use `oxidizer_line_resistance` instead.
            fuel_line_loss: Deprecated. Fixed pressure loss along the fuel feedline
                [Pa]. Use `fuel_line_resistance` instead.

        Raises:
            ValueError: If any pressure loss is negative.
        """
        feed_system = cls(
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
        if oxidizer_line_loss is not None or fuel_line_loss is not None:
            warnings.warn(
                LINE_LOSSES_DEPRECATION_MESSAGE, DeprecationWarning, stacklevel=2
            )
            feed_system.line_losses = {
                "oxidizer": oxidizer_line_loss or 0.0,
                "fuel": fuel_line_loss or 0.0,
            }
            feed_system._validate_pressure_losses()
        return feed_system

    def _validate_pressure_losses(self) -> None:
        if self.pressurizing_line not in self.lines:
            raise ValueError(
                f"pressurizing_line {self.pressurizing_line!r} is not one of the "
                f"lines, got {list(self.lines)}"
            )

        unknown = [name for name in self.line_losses if name not in self.lines]
        if unknown:
            raise ValueError(f"line_losses names {unknown} are not lines of the system")

        if self.piston_loss < 0.0:
            raise ValueError(
                f"piston_loss must be non-negative, got {self.piston_loss}"
            )
        for name, loss in self.line_losses.items():
            if loss < 0.0:
                raise ValueError(
                    f"line_losses[{name!r}] must be non-negative, got {loss}"
                )

    @property
    def lower_line_names(self) -> tuple[str, ...]:
        """Names of the lines below the piston, in the order they were given."""
        return tuple(name for name in self.lines if name != self.pressurizing_line)

    def get_tank_volumes(self, fluid_masses: Mapping[str, float]) -> dict[str, float]:
        """
        Return the volume the fluid of every line fills [m^3].

        A line below the piston fills the volume of its liquid. The top of the
        stack fills its tank volume plus the liquid volume pushed out below it.

        Args:
            fluid_masses: Fluid mass of every line [kg], keyed by line name.

        Returns:
            Volume of every line's fluid [m^3], keyed by line name.
        """
        volumes: dict[str, float] = {}
        swept_volume = 0.0
        for name in self.lower_line_names:
            lower_tank = self.lines[name].tank
            liquid_density = lower_tank.saturated_liquid_density
            volumes[name] = fluid_masses[name] / liquid_density
            swept_volume += (
                lower_tank.initial_fluid_mass - fluid_masses[name]
            ) / liquid_density

        volumes[self.pressurizing_line] = (
            self.lines[self.pressurizing_line].tank.volume + swept_volume
        )
        return volumes

    def get_inlet_pressures(
        self, line_states: Mapping[str, line_models.LineState]
    ) -> dict[str, float]:
        """
        Return the pressure at the head of every feedline [Pa].

        The top line gets its tank pressure at the volume the piston has swept to.
        Every line below the piston takes the piston pressure loss. The feedline
        resistance is not taken here. A deprecated fixed line loss is.

        Args:
            line_states: Fluid mass and internal energy of every line, keyed by
                line name.

        Returns:
            Feedline head pressure of every line [Pa], keyed by line name.
        """
        pressurizing_state = line_states[self.pressurizing_line]
        top_volume = self.get_tank_volumes(
            {name: state.fluid_mass for name, state in line_states.items()}
        )[self.pressurizing_line]
        stack_pressure = self.lines[self.pressurizing_line].tank.get_pressure(
            pressurizing_state.fluid_mass,
            pressurizing_state.internal_energy,
            volume=top_volume,
        )

        return {
            name: stack_pressure
            - (0.0 if name == self.pressurizing_line else self.piston_loss)
            - self.line_losses[name]
            for name in self.lines
        }
