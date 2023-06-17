from . import Material


class Fiberglass(Material):
    def __init__(self) -> None:
        super().__init__(
            density=1700, yield_strength=200e6, ultimate_strength=210e6
        )
