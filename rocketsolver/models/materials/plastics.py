from . import Material


class EpoxiResin(Material):
    def __init__(self) -> None:
        super().__init__(
            density=1100, yield_strength=60e6, ultimate_strength=60e6
        )
