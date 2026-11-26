"""Fluid property service wrapper around CoolProp."""

import dataclasses
import functools
import typing

import scipy.optimize

import machwave.common.extras as extras

try:
    import CoolProp.CoolProp as CP
except ImportError as e:  # pragma: no cover - exercised only without coolprop
    raise extras.MissingOptionalDependencyError("CoolProp", extras.LIQUID) from e

# a converged flash is off by under 1e-8 J/kg, a wrong one by tens of kJ/kg
INTERNAL_ENERGY_TOLERANCE = 1.0  # [J/kg]
# the saturation curve is undefined at the critical point itself
CRITICAL_TEMPERATURE_BRACKET_MARGIN = 1e-8  # [-]
DOME_TEMPERATURE_TOLERANCE = 1e-10  # [K]


@functools.cache
def _get_fluid_constant(key: str, fluid_name: str) -> float:
    return CP.PropsSI(key, fluid_name)


@dataclasses.dataclass(frozen=True, slots=True)
class EquilibriumState:
    """
    A single fluid in equilibrium at one density and internal energy.

    Attributes:
        temperature: Fluid temperature [K].
        pressure: Fluid pressure [Pa].
        saturated_liquid_density: Saturated liquid density at the temperature
            [kg/m^3].
        saturated_vapor_density: Saturated vapor density at the temperature
            [kg/m^3].
    """

    temperature: float
    pressure: float
    saturated_liquid_density: float
    saturated_vapor_density: float


class CoolPropService:
    """Thin wrapper around CoolProp bound to a single fluid."""

    def __init__(self, fluid_name: str) -> None:
        """
        Initialize the service.

        Args:
            fluid_name: Name of the fluid in the CoolProp database.
        """
        self.fluid_name = fluid_name
        # created on first use, so an unknown fluid name fails where it is used
        self._abstract_state: CP.AbstractState | None = None

    def __getstate__(self) -> dict[str, typing.Any]:
        """
        Return the state to copy or pickle, without the CoolProp state.

        A CoolProp `AbstractState` cannot be copied or pickled. The copy makes
        its own on first use.
        """
        return {**self.__dict__, "_abstract_state": None}

    def _get_abstract_state(self) -> CP.AbstractState:
        """Return the CoolProp state the flashes run on, made on first use."""
        if self._abstract_state is None:
            self._abstract_state = CP.AbstractState("HEOS", self.fluid_name)
        return self._abstract_state

    def get_triple_point_temperature(self) -> float:
        """
        Get the triple point temperature of the fluid.

        Returns:
            Triple point temperature [K].
        """
        return _get_fluid_constant("Ttriple", self.fluid_name)

    def get_molar_mass(self) -> float:
        """
        Get the molar mass of the fluid.

        Returns:
            Molar mass [kg/mol].
        """
        return _get_fluid_constant("M", self.fluid_name)

    def get_critical_temperature(self) -> float:
        """
        Get the critical temperature of the fluid.

        Returns:
            Critical temperature [K].
        """
        return _get_fluid_constant("Tcrit", self.fluid_name)

    def get_saturation_pressure(self, temperature: float) -> float:
        """
        Get the saturation pressure on the liquid side of the saturation curve.

        Args:
            temperature: Temperature [K].

        Returns:
            Saturation pressure [Pa].
        """
        return CP.PropsSI("P", "T", temperature, "Q", 0, self.fluid_name)

    def get_saturated_liquid_density(self, temperature: float) -> float:
        """
        Get the saturated-liquid density at a given temperature.

        Args:
            temperature: Temperature [K].

        Returns:
            Saturated-liquid density [kg/m^3].
        """
        return CP.PropsSI("D", "T", temperature, "Q", 0, self.fluid_name)

    def get_saturated_vapor_density(self, temperature: float) -> float:
        """
        Get the saturated-vapor density at a given temperature.

        Args:
            temperature: Temperature [K].

        Returns:
            Saturated-vapor density [kg/m^3].
        """
        return CP.PropsSI("D", "T", temperature, "Q", 1, self.fluid_name)

    def get_saturated_liquid_enthalpy(self, temperature: float) -> float:
        """
        Get the saturated-liquid specific enthalpy at a given temperature.

        Args:
            temperature: Temperature [K].

        Returns:
            Saturated-liquid specific enthalpy [J/kg].
        """
        return CP.PropsSI("H", "T", temperature, "Q", 0, self.fluid_name)

    def get_saturated_vapor_enthalpy(self, temperature: float) -> float:
        """
        Get the saturated-vapor specific enthalpy at a given temperature.

        Args:
            temperature: Temperature [K].

        Returns:
            Saturated-vapor specific enthalpy [J/kg].
        """
        return CP.PropsSI("H", "T", temperature, "Q", 1, self.fluid_name)

    def get_saturated_liquid_entropy(self, temperature: float) -> float:
        """
        Get the saturated-liquid specific entropy at a given temperature.

        Args:
            temperature: Temperature [K].

        Returns:
            Saturated-liquid specific entropy [J/(kg K)].
        """
        return CP.PropsSI("S", "T", temperature, "Q", 0, self.fluid_name)

    def get_pressure_at_temperature_density(
        self, temperature: float, density: float
    ) -> float:
        """
        Get the single-phase pressure at a given temperature and density.

        Args:
            temperature: Temperature [K].
            density: Density [kg/m^3].

        Returns:
            Pressure [Pa].
        """
        return CP.PropsSI("P", "T", temperature, "D", density, self.fluid_name)

    def get_internal_energy_at_temperature_density(
        self, temperature: float, density: float
    ) -> float:
        """
        Get the specific internal energy at a given temperature and density.

        Args:
            temperature: Temperature [K].
            density: Density [kg/m^3].

        Returns:
            Specific internal energy [J/kg].
        """
        return CP.PropsSI("U", "T", temperature, "D", density, self.fluid_name)

    def get_equilibrium_state(
        self, density: float, internal_energy: float
    ) -> EquilibriumState:
        """
        Get the equilibrium state at a density and specific internal energy.

        CoolProp 6.8 can silently return a single-phase state for a point inside the
        saturation dome. The flash is kept only if its temperature gives back the
        internal energy. Otherwise the state is solved on the dome.

        Args:
            density: Density [kg/m^3].
            internal_energy: Specific internal energy [J/kg].

        Returns:
            Temperature, pressure and saturation densities at that state.

        Raises:
            ValueError: If the state is supercritical, or if it is neither a
                converged single-phase state nor on the saturation dome.
        """
        abstract_state = self._get_abstract_state()
        try:
            abstract_state.update(CP.DmassUmass_INPUTS, density, internal_energy)
        except ValueError:
            return self._solve_on_the_dome(density, internal_energy)
        temperature = abstract_state.T()
        pressure = abstract_state.p()

        critical_temperature = self.get_critical_temperature()
        if temperature >= critical_temperature:
            raise ValueError(
                f"{self.fluid_name} at {density} kg/m^3 and {internal_energy} J/kg "
                f"is supercritical at {temperature} K; the saturation model holds "
                f"only below the critical temperature {critical_temperature} K"
            )

        state = EquilibriumState(
            temperature=temperature,
            pressure=pressure,
            saturated_liquid_density=self.get_saturated_liquid_density(temperature),
            saturated_vapor_density=self.get_saturated_vapor_density(temperature),
        )
        if state.saturated_vapor_density < density < state.saturated_liquid_density:
            residual, _ = self._get_dome_residual(
                temperature,
                density,
                internal_energy,
                saturated_liquid_density=state.saturated_liquid_density,
                saturated_vapor_density=state.saturated_vapor_density,
            )
            is_consistent = abs(residual) <= INTERNAL_ENERGY_TOLERANCE
        else:
            is_consistent = (
                abs(
                    self.get_internal_energy_at_temperature_density(
                        temperature, density
                    )
                    - internal_energy
                )
                <= INTERNAL_ENERGY_TOLERANCE
            )

        if is_consistent:
            return state
        return self._solve_on_the_dome(density, internal_energy)

    def _get_dome_residual(
        self,
        temperature: float,
        density: float,
        internal_energy: float,
        *,
        saturated_liquid_density: float,
        saturated_vapor_density: float,
    ) -> tuple[float, float]:
        """
        Get the internal energy residual of a two-phase mix at the density.

        Args:
            temperature: Saturation temperature [K].
            density: Bulk density [kg/m^3].
            internal_energy: Specific internal energy [J/kg].
            saturated_liquid_density: Saturated liquid density at the
                temperature [kg/m^3].
            saturated_vapor_density: Saturated vapor density at the
                temperature [kg/m^3].

        Returns:
            The residual [J/kg] and the quality [-].
        """
        liquid_volume = 1.0 / saturated_liquid_density
        vapor_volume = 1.0 / saturated_vapor_density
        liquid_energy = CP.PropsSI("U", "T", temperature, "Q", 0, self.fluid_name)
        vapor_energy = CP.PropsSI("U", "T", temperature, "Q", 1, self.fluid_name)
        quality = (1.0 / density - liquid_volume) / (vapor_volume - liquid_volume)
        residual = (
            liquid_energy + quality * (vapor_energy - liquid_energy) - internal_energy
        )
        return residual, quality

    def _solve_on_the_dome(
        self, density: float, internal_energy: float
    ) -> EquilibriumState:
        """
        Solve for the two-phase state at a density and internal energy.

        At constant density the mix internal energy rises with temperature. The root
        is bracketed between the triple point and just under the critical point.

        Args:
            density: Bulk density [kg/m^3].
            internal_energy: Specific internal energy [J/kg].

        Returns:
            The saturated state, at the saturation pressure.

        Raises:
            ValueError: If no two-phase state at that density holds that
                internal energy.
        """

        def get_residual(temperature: float) -> float:
            return self._get_dome_residual(
                temperature,
                density,
                internal_energy,
                saturated_liquid_density=self.get_saturated_liquid_density(temperature),
                saturated_vapor_density=self.get_saturated_vapor_density(temperature),
            )[0]

        not_on_the_dome = ValueError(
            f"{self.fluid_name} at {density} kg/m^3 and {internal_energy} J/kg is "
            "neither a converged single-phase state nor on the saturation dome"
        )
        lower_temperature = self.get_triple_point_temperature()
        upper_temperature = self.get_critical_temperature() * (
            1.0 - CRITICAL_TEMPERATURE_BRACKET_MARGIN
        )
        if get_residual(lower_temperature) * get_residual(upper_temperature) > 0.0:
            raise not_on_the_dome

        temperature = typing.cast(
            float,
            scipy.optimize.brentq(
                get_residual,
                lower_temperature,
                upper_temperature,
                xtol=DOME_TEMPERATURE_TOLERANCE,
            ),
        )
        state = EquilibriumState(
            temperature=temperature,
            pressure=self.get_saturation_pressure(temperature),
            saturated_liquid_density=self.get_saturated_liquid_density(temperature),
            saturated_vapor_density=self.get_saturated_vapor_density(temperature),
        )
        _, quality = self._get_dome_residual(
            temperature,
            density,
            internal_energy,
            saturated_liquid_density=state.saturated_liquid_density,
            saturated_vapor_density=state.saturated_vapor_density,
        )
        if not 0.0 <= quality <= 1.0:
            raise not_on_the_dome

        return state

    def get_enthalpy_at_temperature_density(
        self, temperature: float, density: float
    ) -> float:
        """
        Get the specific enthalpy at a given temperature and density.

        Args:
            temperature: Temperature [K].
            density: Density [kg/m^3].

        Returns:
            Specific enthalpy [J/kg].
        """
        return CP.PropsSI("H", "T", temperature, "D", density, self.fluid_name)

    def get_enthalpy_at_temperature_pressure(
        self, temperature: float, pressure: float
    ) -> float:
        """
        Get the specific enthalpy at a given temperature and pressure.

        Args:
            temperature: Temperature [K].
            pressure: Pressure [Pa].

        Returns:
            Specific enthalpy [J/kg].
        """
        return CP.PropsSI("H", "T", temperature, "P", pressure, self.fluid_name)

    def get_entropy_at_temperature_pressure(
        self, temperature: float, pressure: float
    ) -> float:
        """
        Get the specific entropy at a given temperature and pressure.

        Args:
            temperature: Temperature [K].
            pressure: Pressure [Pa].

        Returns:
            Specific entropy [J/(kg K)].
        """
        return CP.PropsSI("S", "T", temperature, "P", pressure, self.fluid_name)

    def get_density_at_pressure_entropy(self, pressure: float, entropy: float) -> float:
        """
        Get the density at a given pressure and specific entropy.

        Args:
            pressure: Pressure [Pa].
            entropy: Specific entropy [J/(kg K)].

        Returns:
            Density [kg/m^3].
        """
        return CP.PropsSI("D", "P", pressure, "S", entropy, self.fluid_name)

    def get_enthalpy_at_pressure_entropy(
        self, pressure: float, entropy: float
    ) -> float:
        """
        Get the specific enthalpy at a given pressure and specific entropy.

        Args:
            pressure: Pressure [Pa].
            entropy: Specific entropy [J/(kg K)].

        Returns:
            Specific enthalpy [J/kg].
        """
        return CP.PropsSI("H", "P", pressure, "S", entropy, self.fluid_name)

    def get_density_and_enthalpy_at_pressure_entropy(
        self, pressure: float, entropy: float
    ) -> tuple[float, float]:
        """
        Get the density and specific enthalpy at a pressure and specific entropy.

        Uses a single flash, so it is cheaper than calling
        `get_density_at_pressure_entropy` and `get_enthalpy_at_pressure_entropy`.

        Args:
            pressure: Pressure [Pa].
            entropy: Specific entropy [J/(kg K)].

        Returns:
            Tuple of density [kg/m^3] and specific enthalpy [J/kg].

        Raises:
            ValueError: If CoolProp cannot resolve the state.
        """
        state = self._get_abstract_state()
        state.update(CP.PSmass_INPUTS, pressure, entropy)
        return state.rhomass(), state.hmass()
