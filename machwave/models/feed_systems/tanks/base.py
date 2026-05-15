import CoolProp.CoolProp as CP
import scipy.constants


class Tank:
    """
    A generic two-phase tank model for any fluid recognized by CoolProp.

    Assumptions:
      - Constant temperature (isothermal).
      - Two-phase equilibrium if there's enough mass to form liquid + vapor.
      - If insufficient mass for liquid, treat it as an ideal gas.
      - Ignores temperature changes upon phase change (no thermal balance).
    """

    OVERFILL_TOLERANCE = 0.01

    def __init__(
        self,
        fluid_name: str,
        volume: float,
        temperature: float,
        initial_fluid_mass: float,
    ) -> None:
        """Initialize a two-phase tank model.

        Args:
            fluid_name: Name of the fluid in the CoolProp database
                (e.g. 'N2O', 'Oxygen', 'Hydrogen', 'Ethanol', etc.).
            volume: Internal volume of the tank [m^3].
            temperature: Absolute temperature [K], assumed constant.
            initial_fluid_mass: Initial total mass of fluid [kg].

        Raises:
            ValueError: If the implied bulk density exceeds the saturated
                liquid density at ``temperature`` (within
                :attr:`OVERFILL_TOLERANCE`), which is physically impossible.
        """
        self._check_not_overfilled(fluid_name, volume, temperature, initial_fluid_mass)

        self.fluid_name = fluid_name
        self.volume = volume
        self.temperature = temperature
        self.initial_fluid_mass = initial_fluid_mass
        self.fluid_mass = initial_fluid_mass

    @classmethod
    def _check_not_overfilled(
        cls,
        fluid_name: str,
        volume: float,
        temperature: float,
        initial_fluid_mass: float,
    ) -> None:
        """Raise ``ValueError`` if the tank fill is denser than liquid.

        The implied bulk density ``initial_fluid_mass / volume`` cannot exceed
        the saturated-liquid density at ``temperature`` — anything denser
        leaves no physical state for the fluid. A small tolerance
        (:attr:`OVERFILL_TOLERANCE`) absorbs property-table noise and
        thermal-expansion margin.
        """
        rho_liquid = CP.PropsSI("D", "T", temperature, "Q", 0, fluid_name)
        bulk_density = initial_fluid_mass / volume
        if bulk_density > rho_liquid * (1 + cls.OVERFILL_TOLERANCE):
            raise ValueError(
                f"Tank overfilled: implied bulk density "
                f"{bulk_density:.1f} kg/m^3 exceeds liquid density "
                f"{rho_liquid:.1f} kg/m^3 for {fluid_name} at {temperature} K"
            )

    def get_pressure(self) -> float:
        """Return the current tank pressure [Pa] using two-phase logic.

        1) Compute the saturation pressure at the given temperature.
        2) If fluid_mass > mass_if_all_vapor(p_sat), the tank is partially
           liquid and the pressure is pinned at saturation.
        3) Otherwise, the tank is all vapor (ideal gas), and we use
           P = (m / M) * R * T / V.

        Returns:
            Tank pressure [Pa].
        """
        # 1) Saturation pressure at the given T (if subcritical and property is defined).
        #    For cryogenics or other fluids, ensure T is within valid range for saturation data.
        p_sat = CP.PropsSI("P", "T", self.temperature, "Q", 0, self.fluid_name)

        # 2) Calculate how much mass we'd have if everything was vapor at p_sat.
        m_vap_max = self._mass_if_all_vapor(p_sat)

        if self.fluid_mass > m_vap_max:
            # We have enough mass that some fraction is liquid => saturation
            return p_sat
        else:
            # All vapor => ideal gas formula
            return self._pressure_if_ideal_gas(
                self.fluid_mass, self.volume, self.temperature
            )

    def get_density(self, pressure: float | None = None) -> float:
        """Return fluid density [kg/m^3] at tank pressure and temperature.

        Uses CoolProp. If pressure is provided, it is used as the tank
        pressure override (e.g., a piston-pressurized stacked-tank system).

        For a two-phase tank, returns the saturated *liquid* density: real
        feed systems pull liquid through a dip tube, so the orifice equation
        downstream needs ρ_liquid, not the bulk mixture density.

        Returns:
            Fluid density [kg/m^3].
        """
        # Empty tank?
        if self.fluid_mass <= 0:
            return 0.0

        # 1) Current pressure (or override)
        p = self.get_pressure() if pressure is None else pressure

        try:
            # 2a) Single‐phase (or off‐saturation) density
            return CP.PropsSI("D", "T", self.temperature, "P", p, self.fluid_name)

        except ValueError:
            # 2b) Two-phase: PropsSI(T, P) is ambiguous at saturation. The
            #     feed system pulls liquid from the bottom of the tank, so
            #     return the saturated liquid density at this temperature.
            m_vap_max = self._mass_if_all_vapor(p)

            if self.fluid_mass > m_vap_max:
                return CP.PropsSI("D", "T", self.temperature, "Q", 0, self.fluid_name)

            # Fallback: idealized bulk density
            return self.fluid_mass / self.volume

    def remove_propellant(self, mass: float) -> None:
        """
        Removes the specified mass of fluid [kg] from the tank.

        If the requested mass exceeds what's in the tank, sets total mass to 0.
        """
        if mass < 0:
            raise ValueError("Cannot remove a negative mass of propellant.")

        self.fluid_mass -= mass
        if self.fluid_mass < 0:
            self.fluid_mass = 0.0

    def _mass_if_all_vapor(self, p_vapor: float) -> float:
        """Return mass if tank were entirely vapor at given pressure.

        Uses ideal gas law at pressure p_vapor [Pa] and
        temperature self.temperature.

        Args:
            p_vapor: Pressure of the vapor [Pa].

        Returns:
            Mass of vapor [kg].
        """
        # Ideal gas:  m = (P * V * M) / (R_universal * T)
        molar_mass = CP.PropsSI("M", self.fluid_name)  # kg/mol
        R_universal = scipy.constants.R  # J/(mol*K)
        return (p_vapor * self.volume * molar_mass) / (R_universal * self.temperature)

    def _pressure_if_ideal_gas(
        self, mass: float, volume: float, temperature: float
    ) -> float:
        """
        Computes the pressure [Pa] if all the fluid is in the vapor phase,
        using the ideal gas law: P = (mass / M) * R * T / volume.
        """
        molar_mass = CP.PropsSI("M", self.fluid_name)  # kg/mol
        R_universal = scipy.constants.R  # J/(mol*K)
        n_moles = mass / molar_mass
        return (n_moles * R_universal * temperature) / volume
