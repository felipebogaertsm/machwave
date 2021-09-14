# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
Stores structural simulation function.
"""

import numpy as np


def run_structural_simulation(structure, ib_parameters):
    # Casing thickness assuming thin wall [m]:
    casing_sf = structure.casing_safety_factor(structure.Y_chamber, ib_parameters.P0)

    # Nozzle thickness assuming thin wall [m]:
    nozzle_conv_t, nozzle_div_t, = structure.nozzle_thickness(
        structure.Y_nozzle, structure.Div_angle, structure.Conv_angle, ib_parameters.P0)

    # Bulkhead thickness [m]:
    bulkhead_t = structure.bulkhead_thickness(structure.Y_bulkhead, ib_parameters.P0)

    # Screw safety factors and optimal quantity (shear, tear and compression):
    optimal_fasteners, max_sf_fastener, shear_sf, tear_sf, compression_sf = \
        structure.optimal_fasteners(structure.max_number_of_screws, ib_parameters.P0, structure.Y_chamber,
                                    structure.U_screw)

    return StructuralParameters(casing_sf, nozzle_conv_t, nozzle_div_t, bulkhead_t, optimal_fasteners, max_sf_fastener,
                                shear_sf, tear_sf, compression_sf)
