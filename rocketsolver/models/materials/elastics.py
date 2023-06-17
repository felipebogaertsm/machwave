from . import Material


class EPDM(Material):
    """
    Data obtained from:
    https://www.matweb.com/search/datasheet.aspx?matguid=f8e3355cc2c541fbb0174960466819c0&ckck=1
    """

    def __init__(self) -> None:
        super().__init__(
            density=1500,
            yield_strength=None,
            ultimate_strength=17e6,
        )
