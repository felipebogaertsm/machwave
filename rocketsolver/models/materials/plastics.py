# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from . import Material


class EpoxiResin(Material):
    def __init__(self) -> None:
        super().__init__(
            density=1100, yield_strength=60e6, ultimate_strength=60e6
        )
