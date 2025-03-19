from machwave.operations.internal_ballistics.base import MotorOperation
from machwave.models.propulsion.motors import LiquidEngine


class LiquidEngineOperation(MotorOperation):
    """
    Operation for a Liquid Rocket Engine.

    The variable names correspond to what they are commonly referred to in books and papers related to
    Rocket Propulsion. Therefore, PEP8's snake_case will not be followed rigorously.
    """

    def __init__(
        self,
        motor: LiquidEngine,
        initial_pressure: float,
        initial_atmospheric_pressure: float,
    ) -> None:
        """
        Initial parameters for a SRM operation.
        """
        super().__init__(
            motor=motor,
            initial_pressure=initial_pressure,
            initial_atmospheric_pressure=initial_atmospheric_pressure,
        )

    def iterate(
        self,
        d_t: float,
        P_ext: float,
    ) -> None:
        """
        Iterate liquid engine operation.

        TODO: implement this method.
        """

    def print_results(self) -> None:
        """
        TODO: implement this method.
        """
