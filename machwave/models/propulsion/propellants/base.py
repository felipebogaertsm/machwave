import abc
import dataclasses


import rocketcea.cea_obj as cea


@dataclasses.dataclass
class PropellantProperties:
    gamma_chamber: float
    gamma_exhaust: float
    adiabatic_flame_temperature: float
    molecular_weight_chamber: float
    molecular_weight_exhaust: float
    i_sp_frozen: float
    i_sp_shifting: float


class Propellant(abc.ABC):
    """
    Base class for propellants. To update the propellant parameters, use the
    `evaluate` method.

    TODO: Still need to define how to compose different propellant with
    different mixture ratios, solid and liquid.
    """

    def __init__(self, combustion_efficiency: float = 0.95):
        self.combustion_efficiency = combustion_efficiency

        self._initial_pressure = 1000  # psi
        self._initial_expansion_ratio = 8

        # CEA object to be defined
        self.cea_obj = None

        self.evaluate()

    def evaluate(self, *args, **kwargs) -> PropellantProperties:
        """
        Calculate propellant properties given the current state.

        Returns:
            PropellantProperties: The calculated propellant properties.
        """
        self.cea_obj = cea.CEA_Obj(oxName="LOX", fuelName="RP-1")
