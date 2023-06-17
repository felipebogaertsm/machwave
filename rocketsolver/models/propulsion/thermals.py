from rocketsolver.models.materials import Material


class ThermalLiner:
    def __init__(self, thickness: float, material: Material) -> None:
        """
        Initializes a ThermalLiner object.

        Args:
            thickness (float): The thickness of the thermal liner, in meters.
            material (Material): The material used for the thermal liner.
        """
        self.thickness = thickness
        self.material = material
