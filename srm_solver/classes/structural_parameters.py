# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
Stores StructuralParameters class and methods.
"""


class StructuralParameters:
    def __init__(
        self,
        casing_sf,
        nozzle_conv_t,
        nozzle_div_t,
        bulkhead_t,
        optimal_fasteners,
        max_sf_fastener,
        shear_sf,
        tear_sf,
        compression_sf
    ):
        self.casing_sf = casing_sf
        self.nozzle_conv_t = nozzle_conv_t
        self.nozzle_div_t = nozzle_div_t
        self.bulkhead_t = bulkhead_t
        self.optimal_fasteners = optimal_fasteners
        self.max_sf_fastener = max_sf_fastener
        self.shear_sf = shear_sf
        self.tear_sf = tear_sf
        self.compression_sf = compression_sf
