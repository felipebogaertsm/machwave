# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
Stores structural simulation.
"""

import numpy as np

from models.propulsion.structure import MotorStructure
from simulations import Simulation
from simulations.dataclasses.structural_parameters import StructuralParameters


class StructuralSimulation(Simulation):
    def __init__(
        self,
        structure: MotorStructure,
        chamber_pressure: np.array,
        safety_factor: float,
    ) -> None:
        self.structure = structure
        self.chamber_pressure = chamber_pressure
        self.safety_factor = safety_factor

    def run(self) -> StructuralParameters:
        # Casing thickness assuming thin wall [m]:
        casing_sf = self.structure.chamber.get_casing_safety_factor(
            self.chamber_pressure
        )

        # Nozzle thickness assuming thin wall [m]:
        (
            nozzle_conv_t,
            nozzle_div_t,
        ) = self.structure.nozzle.get_nozzle_thickness(
            self.chamber_pressure, self.safety_factor, self.structure.chamber
        )

        # Bulkhead thickness [m]:
        bulkhead_t = self.structure.chamber.get_bulkhead_thickness(
            self.chamber_pressure, self.safety_factor
        )

        # Screw safety factors and optimal quantity (shear, tear and compression):
        (
            optimal_fasteners,
            max_sf_fastener,
            shear_sf,
            tear_sf,
            compression_sf,
        ) = self.structure.chamber.get_optimal_fasteners(
            self.chamber_pressure,
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
