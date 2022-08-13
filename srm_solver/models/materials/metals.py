# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from . import NozzleMaterial


class Steel(NozzleMaterial):
    """
    Data obtained from:
    https://www.thyssenkrupp-materials.co.uk/stainless-steel-304-14301.html
    """

    def __init__(self) -> None:
        super().__init__(
            density=8000,
            yield_strength=210e6,
            ultimate_strength=520e6,
            C1=0.00506,
            C2=0.0,
        )


class Al6063T5(NozzleMaterial):
    """
    Data obtained from:
    https://www.makeitfrom.com/material-properties/6063-T5-Aluminum
    """

    def __init__(self) -> None:
        super().__init__(
            density=2700,
            yield_strength=170e6,
            ultimate_strength=180e6,
            C1=0.00506,
            C2=0.0,
        )


class Al6061T6(NozzleMaterial):
    """
    Data obtained from:
    https://matweb.com/search/DataSheet.aspx?MatGUID=b8d536e0b9b54bd7b69e4124d8f1d20a&ckck=1
    """

    def __init__(self) -> None:
        super().__init__(
            density=2700,
            yield_strength=262e6,
            ultimate_strength=290e6,
            C1=0.00506,
            C2=0.0,
        )
