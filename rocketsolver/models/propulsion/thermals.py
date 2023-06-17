from rocketsolver.models.materials import Material


class ThermalLiner:
    def __init__(self, thickness: float, material: Material) -> None:
        self.thickness = thickness
        self.material = material
