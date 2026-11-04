"""Fluid property service wrapper around CoolProp."""

import dataclasses
import typing

import scipy.optimize

import machwave.common.extras as extras

try:
    import CoolProp.CoolProp as CP
except ImportError as e:  # pragma: no cover - exercised only without coolprop
    raise extras.MissingOptionalDependencyError("CoolProp", extras.LIQUID) from e


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class DensityInternalEnergyState:
    """
    The fluid at one density and specific internal energy.

    Attributes:
        temperature: Temperature [K].
        pressure: Pressure [Pa].
        is_two_phase: Whether the state lies inside the saturation dome.
        saturated_liquid_density: Saturated liquid density at the temperature
            [kg/m^3].
        saturated_vapor_density: Saturated vapor density at the temperature
            [kg/m^3].
        saturated_liquid_enthalpy: Saturated liquid specific enthalpy at the
            temperature [J/kg].
        saturated_vapor_enthalpy: Saturated vapor specific enthalpy at the
            temperature [J/kg].
        enthalpy: Specific enthalpy of the state itself [J/kg].
    """

    temperature: float
    pressure: float
    is_two_phase: bool
    saturated_liquid_density: float
    saturated_vapor_density: float
    saturated_liquid_enthalpy: float
    saturated_vapor_enthalpy: float
    enthalpy: float


# How far a (D, U) flash may miss the internal energy it was asked for before
# it is rejected [J/kg]. CoolProp lands within 1e-8 J/kg when it converges; the
# failures this catches miss by tens of kJ/kg.
INTERNAL_ENERGY_TOLERANCE = 1.0


class CoolPropService:
    """
    Thin wrapper around CoolProp bound to a single fluid.

    Point lookups go through `PropsSI`. The (D, U) state a tank running an
    energy balance needs every step, and the (P, s) state of the HEM flux,
    go through an `AbstractState` instead, which flashes once and hands back
    everything read off that flash.
    """

    def __init__(self, fluid_name: str) -> None:
        """
        Initialize the service.

        Args:
            fluid_name: Name of the fluid in the CoolProp database.
        """
        self.fluid_name = fluid_name
        # Built on first use: an AbstractState cannot be pickled or deep
        # copied, and a service that is never asked for a (D, U) state should
        # not pay for one.
        self._state: typing.Any = None
        self._saturation_state: typing.Any = None
        self._check_state: typing.Any = None
        self._pressure_entropy_state: typing.Any = None
        self._triple_point_temperature = 0.0
        self._critical_temperature = 0.0
        # How many (D, U) states the flash got wrong and the dome solve
        # resolved instead.
        self.dome_solve_count = 0

    def __getstate__(self) -> dict[str, typing.Any]:
        """Leave the CoolProp states out of a copy; they rebuild on first use."""
        return {"fluid_name": self.fluid_name}

    def __setstate__(self, state: dict[str, typing.Any]) -> None:
        """Restore a copy with no CoolProp state built yet."""
        self.__init__(state["fluid_name"])

    def get_state_at_density_internal_energy(
        self, density: float, internal_energy: float
    ) -> DensityInternalEnergyState:
        """
        Resolve the fluid at a density and specific internal energy.

        One (D, U) update gives the state, and the saturation curve checks it.
        CoolProp 6.8 can return a single-phase state for a point inside the
        dome without saying so (N2O at 454.5 kg/m^3 and 228.6 kJ/kg flashes to
        270.4 K and 1.45 MPa; the equilibrium state is 291.0 K and 4.81 MPa).
        A two-phase answer must satisfy the dome relation at its temperature,
        and a single-phase one must lie outside the saturation densities at
        its temperature and give back the internal energy on a (D, T) update.
        Anything else is solved on the dome instead, see
        `_solve_on_the_dome`.

        Args:
            density: Density [kg/m^3].
            internal_energy: Specific internal energy [J/kg].

        Returns:
            The state at that density and internal energy.

        Raises:
            ValueError: If CoolProp cannot resolve the state, or if the
                temperature is outside the range the saturation curve spans.
        """
        if self._state is None:
            self._state = CP.AbstractState("HEOS", self.fluid_name)
            self._saturation_state = CP.AbstractState("HEOS", self.fluid_name)
            self._triple_point_temperature = self.get_triple_point_temperature()
            self._critical_temperature = self.get_critical_temperature()

        state = self._state
        saturation = self._saturation_state
        try:
            state.update(CP.DmassUmass_INPUTS, density, internal_energy)
        except ValueError:
            return self._solve_on_the_dome(density, internal_energy)

        temperature = state.T()
        if state.phase() == CP.iphase_twophase:
            if not self._is_on_the_dome(state, density, internal_energy):
                return self._solve_on_the_dome(density, internal_energy)
            return self._read_state(state, state, is_two_phase=True)

        if temperature >= self._critical_temperature:
            return self._read_state(state, None, is_two_phase=False)

        saturation.update(CP.QT_INPUTS, 0.0, temperature)
        inside_the_dome = (
            saturation.saturated_vapor_keyed_output(CP.iDmass)
            < density
            < saturation.saturated_liquid_keyed_output(CP.iDmass)
        )
        if inside_the_dome or not self._is_single_phase_at(
            temperature, density, internal_energy
        ):
            return self._solve_on_the_dome(density, internal_energy)
        return self._read_state(state, saturation, is_two_phase=False)

    def _is_on_the_dome(
        self, saturation: typing.Any, density: float, internal_energy: float
    ) -> bool:
        """Whether the dome relation holds at a saturation state's temperature."""
        return (
            abs(self._get_dome_residual(saturation, density, internal_energy)[0])
            <= INTERNAL_ENERGY_TOLERANCE
        )

    def _is_single_phase_at(
        self, temperature: float, density: float, internal_energy: float
    ) -> bool:
        """Whether a (D, T) update gives back the internal energy asked for."""
        if self._check_state is None:
            self._check_state = CP.AbstractState("HEOS", self.fluid_name)
        check = self._check_state
        check.update(CP.DmassT_INPUTS, density, temperature)
        return abs(check.umass() - internal_energy) <= INTERNAL_ENERGY_TOLERANCE

    @staticmethod
    def _get_dome_residual(
        saturation: typing.Any, density: float, internal_energy: float
    ) -> tuple[float, float]:
        """
        How far a two-phase mix at the density misses the internal energy.

        The quality follows from 1/rho = v_l + x (v_v - v_l), and the mix holds
        u = u_l + x (u_v - u_l), both at the saturation state's temperature.

        Returns:
            The residual [J/kg] and the quality.
        """
        liquid_volume = 1.0 / saturation.saturated_liquid_keyed_output(CP.iDmass)
        vapor_volume = 1.0 / saturation.saturated_vapor_keyed_output(CP.iDmass)
        liquid_energy = saturation.saturated_liquid_keyed_output(CP.iUmass)
        vapor_energy = saturation.saturated_vapor_keyed_output(CP.iUmass)
        quality = (1.0 / density - liquid_volume) / (vapor_volume - liquid_volume)
        residual = (
            liquid_energy + quality * (vapor_energy - liquid_energy) - internal_energy
        )
        return residual, quality

    def _solve_on_the_dome(
        self, density: float, internal_energy: float
    ) -> DensityInternalEnergyState:
        """
        Solve the two-phase relation for the temperature, bracketed.

        Along an isochore the mix's internal energy rises with temperature, so
        the root is bracketed between the triple point and just under the
        critical point. The state is two-phase only if the quality there lies
        in [0, 1].

        Raises:
            ValueError: If no two-phase state at that density holds that
                internal energy.
        """
        saturation = self._saturation_state

        def residual(temperature: float) -> float:
            saturation.update(CP.QT_INPUTS, 0.0, temperature)
            return self._get_dome_residual(saturation, density, internal_energy)[0]

        lower = self._triple_point_temperature
        upper = self._critical_temperature * (1.0 - 1e-8)
        if residual(lower) * residual(upper) > 0.0:
            raise ValueError(
                f"{self.fluid_name} at {density} kg/m^3 and {internal_energy} "
                "J/kg is neither a converged single-phase state nor on the dome"
            )

        temperature = scipy.optimize.brentq(residual, lower, upper, xtol=1e-10)
        saturation.update(CP.QT_INPUTS, 0.0, temperature)
        _, quality = self._get_dome_residual(saturation, density, internal_energy)
        if not 0.0 <= quality <= 1.0:
            raise ValueError(
                f"{self.fluid_name} at {density} kg/m^3 and {internal_energy} "
                "J/kg is neither a converged single-phase state nor on the dome"
            )

        self.dome_solve_count += 1
        state = self._state
        state.update(CP.QT_INPUTS, quality, temperature)
        return self._read_state(state, state, is_two_phase=True)

    @staticmethod
    def _read_state(
        state: typing.Any, saturation: typing.Any | None, *, is_two_phase: bool
    ) -> DensityInternalEnergyState:
        """Read a resolved state and the saturation curve at its temperature."""
        if saturation is None:
            # Supercritical: no saturation curve at this temperature.
            liquid_density = vapor_density = liquid_enthalpy = vapor_enthalpy = float(
                "nan"
            )
        else:
            liquid_density = saturation.saturated_liquid_keyed_output(CP.iDmass)
            vapor_density = saturation.saturated_vapor_keyed_output(CP.iDmass)
            liquid_enthalpy = saturation.saturated_liquid_keyed_output(CP.iHmass)
            vapor_enthalpy = saturation.saturated_vapor_keyed_output(CP.iHmass)

        return DensityInternalEnergyState(
            temperature=state.T(),
            pressure=state.p(),
            is_two_phase=is_two_phase,
            saturated_liquid_density=liquid_density,
            saturated_vapor_density=vapor_density,
            saturated_liquid_enthalpy=liquid_enthalpy,
            saturated_vapor_enthalpy=vapor_enthalpy,
            enthalpy=state.hmass(),
        )

    def get_triple_point_temperature(self) -> float:
        """
        Get the triple point temperature of the fluid.

        Returns:
            Triple point temperature [K].
        """
        return CP.PropsSI("Ttriple", self.fluid_name)

    def get_molar_mass(self) -> float:
        """
        Get the molar mass of the fluid.

        Returns:
            Molar mass [kg/mol].
        """
        return CP.PropsSI("M", self.fluid_name)

    def get_critical_temperature(self) -> float:
        """
        Get the critical temperature of the fluid.

        Returns:
            Critical temperature [K].
        """
        return CP.PropsSI("Tcrit", self.fluid_name)

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

    def get_temperature_at_density_internal_energy(
        self, density: float, internal_energy: float
    ) -> float:
        """
        Get the temperature at a given density and specific internal energy.

        Args:
            density: Density [kg/m^3].
            internal_energy: Specific internal energy [J/kg].

        Returns:
            Temperature [K].
        """
        return CP.PropsSI("T", "D", density, "U", internal_energy, self.fluid_name)

    def get_pressure_at_density_internal_energy(
        self, density: float, internal_energy: float
    ) -> float:
        """
        Get the pressure at a given density and specific internal energy.

        Args:
            density: Density [kg/m^3].
            internal_energy: Specific internal energy [J/kg].

        Returns:
            Pressure [Pa].
        """
        return CP.PropsSI("P", "D", density, "U", internal_energy, self.fluid_name)

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
        Get the density and specific enthalpy at a pressure and entropy.

        One (P, s) flash gives both, where `get_density_at_pressure_entropy`
        and `get_enthalpy_at_pressure_entropy` flash once each. The values are
        the same to the last bit.

        Args:
            pressure: Pressure [Pa].
            entropy: Specific entropy [J/(kg K)].

        Returns:
            Tuple of density [kg/m^3] and specific enthalpy [J/kg].

        Raises:
            ValueError: If CoolProp cannot resolve the state.
        """
        if self._pressure_entropy_state is None:
            self._pressure_entropy_state = CP.AbstractState("HEOS", self.fluid_name)
        state = self._pressure_entropy_state
        state.update(CP.PSmass_INPUTS, pressure, entropy)
        return state.rhomass(), state.hmass()
