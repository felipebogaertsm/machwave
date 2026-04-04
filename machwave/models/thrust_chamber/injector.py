class BipropellantInjector:
    """
    A simple injector class for a liquid rocket engine.
    """

    def __init__(
        self,
        discharge_coefficient_fuel: float,
        discharge_coefficient_oxidizer: float,
        area_fuel: float,
        area_ox: float,
    ):
        """
        Initialize an Injector instance.

        Args:
            discharge_coefficient_fuel:
                Discharge coefficient for the fuel side (dimensionless).
            discharge_coefficient_oxidizer:
                Discharge coefficient for the oxidizer side (dimensionless).
            area_fuel:
                Effective flow area of the fuel injector [m^2].
            area_ox:
                Effective flow area of the oxidizer injector [m^2].
        """
        self.discharge_coefficient_fuel = discharge_coefficient_fuel
        self.discharge_coefficient_oxidizer = discharge_coefficient_oxidizer
        self.area_fuel = area_fuel
        self.area_ox = area_ox
