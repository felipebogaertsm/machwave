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

    def __init__(self, fluid_name, volume, temperature, initial_fluid_mass):
        """
        Initialize a two-phase tank model.

        Args:
            fluid_name:
                Name of the fluid in the CoolProp database (e.g. 'N2O', 'Oxygen',
                'Hydrogen', 'Ethanol', etc.).
            volume:
                Internal volume of the tank [m^3].
            temperature:
                Absolute temperature [K], assumed constant (isothermal).
            initial_fluid_mass:
                Initial total mass of fluid [kg].
        """
        self.fluid_name = fluid_name
        self.volume = volume
        self.temperature = temperature
        self.initial_fluid_mass = initial_fluid_mass
        self.fluid_mass = initial_fluid_mass

    def get_pressure(self) -> float:
        """
        Returns the current tank pressure [Pa], using two-phase logic:

        1) Compute the saturation pressure at the given temperature.
        2) If fluid_mass > mass_if_all_vapor(p_sat), the tank is partially liquid
           and the pressure is pinned at saturation.
        3) Otherwise, the tank is all vapor (ideal gas), and we use P = (m / M) * R * T / V.

        Returns:
            float: Tank pressure [Pa].
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

    def get_density(self) -> float:
        """
        Returns the fluid density [kg/m^3] at the current tank pressure and
        temperature, using CoolProp.  In two-phase situations (P ≃ P_sat),
        computes the mixture density based on vapor quality.

        Returns:
            float: Fluid density [kg/m^3].
        """
        # Empty tank?
        if self.fluid_mass <= 0:
            return 0.0

        # 1) Current pressure
        p = self.get_pressure()

        try:
            # 2a) Single‐phase (or off‐saturation) density
            return CP.PropsSI("D", "T", self.temperature, "P", p, self.fluid_name)

        except ValueError:
            # 2b) Two‐phase: density at saturation is ambiguous, so compute mixture
            #    via quality:  x = m_vapor / m_total
            #    ρ_mix = 1 / ( x/ρ_v + (1−x)/ρ_l )

            # saturation pressure & max vapor mass
            p_sat = CP.PropsSI("P", "T", self.temperature, "Q", 0, self.fluid_name)
            m_vap_max = self._mass_if_all_vapor(p_sat)

            if self.fluid_mass > m_vap_max:
                x = m_vap_max / self.fluid_mass
                rho_v = CP.PropsSI("D", "T", self.temperature, "Q", 1, self.fluid_name)
                rho_l = CP.PropsSI("D", "T", self.temperature, "Q", 0, self.fluid_name)
                return 1.0 / (x / rho_v + (1 - x) / rho_l)

            # If mass ≤ m_vap_max but still hit a weird error, fallback to ideal‐gas bulk
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
        """
        Returns how many kg of fluid we would have if the tank were entirely vapor
        at pressure p_vapor (Pa) and temperature self.temperature, using the ideal gas law.

        Args:
            p_vapor: Pressure of the vapor [Pa].
        Returns:
            float: Mass of vapor [kg].
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
