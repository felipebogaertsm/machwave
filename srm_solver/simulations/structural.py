# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
Stores structural simulation function.
"""

from simulations.dataclasses.structural_parameters import StructuralParameters


def run_structural_simulation(structure, ib_parameters):
    # Casing thickness assuming thin wall [m]:
    casing_sf = structure.get_casing_safety_factor(
        structure.casing_yield_strength,
        ib_parameters.P0,
    )

    # Nozzle thickness assuming thin wall [m]:
    nozzle_conv_t, nozzle_div_t, = structure.get_nozzle_thickness(
        ib_parameters.P0,
    )

    # Bulkhead thickness [m]:
    bulkhead_t = structure.get_bulkhead_thickness(ib_parameters.P0)

    # Screw safety factors and optimal quantity (shear, tear and compression):
    (
        optimal_fasteners,
        max_sf_fastener,
        shear_sf,
        tear_sf,
        compression_sf,
    ) = structure.get_optimal_fasteners(
        ib_parameters.P0,
    )

    return StructuralParameters(
        casing_sf,
        nozzle_conv_t,
        nozzle_div_t,
        bulkhead_t,
        optimal_fasteners,
        max_sf_fastener,
        shear_sf,
        tear_sf,
        compression_sf,
    )
