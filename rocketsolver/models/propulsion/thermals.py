# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.


from rocketsolver.models.materials import Material


class ThermalLiner:
    def __init__(self, thickness: float, material: Material) -> None:
        self.thickness = thickness
        self.material = material
