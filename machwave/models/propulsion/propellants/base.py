import abc


class Propellant(abc.ABC):
    """
    Base class for propellants. To update the propellant parameters, use the
    `evaluate` method.

    Still need to define how to compose different propellant with
    different mixture ratios, solid and liquid.

    Attributes:
        combustion_efficiency: Combustion efficiency (0 to 1).
        gamma_chamber: Isentropic exponent for the combustion chamber.
        gamma_exhaust: Isentropic exponent for the exhaust.
        adiabatic_flame_temperature: Adiabatic flame temperature [K].
        molecular_weight_chamber: Molar weight in the chamber [kg/mol].
        molecular_weight_exhaust: Molar weight in the exhaust [kg/mol].
        specific_impulse_frozen: Frozen specific impulse [s].
        specific_impulse_shifting: Shifting specific impulse [s].
    """

    def __init__(self, combustion_efficiency: float = 0.95):
        self.combustion_efficiency = combustion_efficiency

        self._initial_pressure = 1000  # psi
        self._initial_expansion_ratio = 8

        self.evaluate()

    def evaluate(self, *args, **kwargs) -> None:
        """Calculate propellant properties given the current state."""

        self.gamma_chamber = 0.0
        self.gamma_exhaust = 0.0
        self.adiabatic_flame_temperature = 0.0
        self.molecular_weight_chamber = 0.0
        self.molecular_weight_exhaust = 0.0
        self.specific_impulse_frozen = 0.0
        self.specific_impulse_shifting = 0.0
