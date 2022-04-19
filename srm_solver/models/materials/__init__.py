# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.


class Material:
    def __init__(
        self,
        density: float,
        yield_strength: float,
        ultimate_strength: float,
    ) -> None:
        self.density = density
        self.yield_strength = yield_strength
        self.ultimate_strength = ultimate_strength
