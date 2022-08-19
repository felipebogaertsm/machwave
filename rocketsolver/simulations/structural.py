# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
Stores structural simulation.
"""

from dataclasses import dataclass

from rocketsolver.models.propulsion.structure import MotorStructure
from rocketsolver.simulations import Simulation


@dataclass
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
        compression_sf,
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


class StructuralSimulation(Simulation):
    def __init__(
        self,
        structure: MotorStructure,
        max_chamber_pressure: float,
        safety_factor: float,
    ) -> None:
        self.structure = structure
        self.max_chamber_pressure = max_chamber_pressure
        self.safety_factor = safety_factor

    def run(self) -> StructuralParameters:
        # Casing thickness assuming thin wall [m]:
        casing_sf = self.structure.chamber.get_casing_safety_factor(
            self.max_chamber_pressure
        )

        # Nozzle thickness assuming thin wall [m]:
        (
            nozzle_conv_t,
            nozzle_div_t,
        ) = self.structure.nozzle.get_nozzle_thickness(
            self.max_chamber_pressure,
            self.safety_factor,
            self.structure.chamber,
        )

        # Bulkhead thickness [m]:
        bulkhead_t = self.structure.chamber.get_bulkhead_thickness(
            self.max_chamber_pressure, self.safety_factor
        )

        # Screw safety factors and optimal quantity (shear, tear and compression):
        (
            optimal_fasteners,
            max_sf_fastener,
            shear_sf,
            tear_sf,
            compression_sf,
        ) = self.structure.chamber.get_optimal_fasteners(
            self.max_chamber_pressure,
        )

        self.structural_parameters = StructuralParameters(
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

        return self.structural_parameters

    def print_results(self):
        print("\nPRELIMINARY STRUCTURAL PROJECT")
        print(
            f" Casing safety factor: {self.structural_parameters.casing_sf:.2f}"
        )
        print(
            f" Minimal nozzle convergent, divergent thickness: {self.structural_parameters.nozzle_conv_t * 1e3:.3f}, "
            f"{self.structural_parameters.nozzle_div_t * 1e3:.3f} mm"
        )
        print(
            f" Minimal bulkhead thickness: {self.structural_parameters.bulkhead_t * 1e3:.3f} mm"
        )
        print(
            f" Optimal number of screws: {self.structural_parameters.optimal_fasteners + 1:d}"
        )
        print(
            f" Shear, tear, compression screw safety factors: "
            f"{self.structural_parameters.shear_sf[self.structural_parameters.optimal_fasteners]:.3f}, "
            f"{self.structural_parameters.tear_sf[self.structural_parameters.optimal_fasteners]:.3f}, "
            f"{self.structural_parameters.compression_sf[self.structural_parameters.optimal_fasteners]:.3f}"
        )
        print("\nDISCLAIMER: values above shall not be the final dimensions.")
        print(
            "Critical dimensions shall be investigated in depth in order to guarantee safety."
        )
