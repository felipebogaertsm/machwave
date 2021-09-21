# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
Stores MotorStructure class and methods.
"""

import numpy as np

from functions.utilities import *
from functions.geometric import *


class MotorStructure:
    def __init__(
        self,
        safety_factor,
        motor_structural_mass,
        chamber_length,
        chamber_inner_diameter,
        casing_inner_diameter,
        casing_outer_diameter,
        screw_diameter,
        screw_clearance_diameter,
        nozzle_throat_diameter,
        C1,
        C2,
        divergent_angle,
        convergent_angle,
        expansion_ratio,
        casing_yield_strength,
        nozzle_yield_strength,
        bulkhead_yield_strength,
        screw_ultimate_strength,
        max_number_of_screws=20,
    ):
        self.safety_factor = safety_factor
        self.motor_structural_mass = motor_structural_mass
        self.chamber_length = chamber_length
        self.chamber_inner_diameter = chamber_inner_diameter
        self.casing_inner_diameter = casing_inner_diameter
        self.casing_outer_diameter = casing_outer_diameter
        self.screw_diameter = screw_diameter
        self.screw_clearance_diameter = screw_clearance_diameter
        self.nozzle_throat_diameter = nozzle_throat_diameter
        self.C1 = C1
        self.C2 = C2
        self.divergent_angle = divergent_angle
        self.convergent_angle = convergent_angle
        self.expansion_ratio = expansion_ratio
        self.casing_yield_strength = casing_yield_strength
        self.nozzle_yield_strength = nozzle_yield_strength
        self.bulkhead_yield_strength = bulkhead_yield_strength
        self.screw_ultimate_strength = screw_ultimate_strength
        self.max_number_of_screws = max_number_of_screws

    def get_chamber_length(self, grain_length, grain_count, grain_spacing):
        """
        Returns the chamber length of the SRM, given the grain parameters.
        """
        return np.sum(grain_length) + (grain_count - 1) * grain_spacing

    def get_chamber_inner_diameter(self, liner_thickness):
        return casing_inner_diameter - 2 * liner_thickness

    def get_throat_area(self):
        return get_circle_area(self.nozzle_throat_diameter)

    def get_bulkhead_thickness(self, chamber_pressure):
        """
        Returns the thickness of a plane bulkhead pressure vessel.
        """
        bulkhead_yield_strength = self.bulkhead_yield_strength
        bulkhead_thickness = self.casing_inner_diameter * (
            np.sqrt(
                (0.75 * np.max(chamber_pressure))
                / (bulkhead_yield_strength / self.safety_factor)
            )
        )
        return bulkhead_thickness

    def get_nozzle_thickness(
        self,
        chamber_pressure,
    ):
        """Returns nozzle convergent and divergent thickness"""
        max_chamber_pressure = np.max(chamber_pressure)
        convergent_angle = self.convergent_angle
        divergent_angle = self.divergent_angle
        nozzle_yield_strength = self.nozzle_yield_strength

        # Yield strength corrected by the safety factor:
        safe_yield_strength = nozzle_yield_strength / self.safety_factor

        nozzle_conv_thickness = (
            np.max(chamber_pressure) * self.casing_inner_diameter / 2
        ) / (
            (
                safe_yield_strength
                - 0.6
                * max_chamber_pressure
                * (np.cos(np.deg2rad(convergent_angle)))
            )
        )

        nozzle_div_thickness = (
            np.max(chamber_pressure) * self.casing_inner_diameter / 2
        ) / (
            (
                safe_yield_strength
                - 0.6
                * max_chamber_pressure
                * (np.cos(np.deg2rad(divergent_angle)))
            )
        )

        return nozzle_conv_thickness, nozzle_div_thickness

    def get_casing_safety_factor(self, Y_cc, chamber_pressure):
        """
        Returns the thickness for a cylindrical pressure vessel.
        """
        casing_yield_strength = self.casing_yield_strength

        thickness = (
            self.casing_outer_diameter - self.casing_inner_diameter
        ) / 2
        max_chamber_pressure = np.max(chamber_pressure)

        bursting_pressure = (casing_yield_strength * thickness) / (
            self.casing_inner_diameter * 0.5 + 0.6 * thickness
        )

        return bursting_pressure / max_chamber_pressure  # casing safety factor

    def get_optimal_fasteners(self, chamber_pressure):
        max_number_of_screws = self.max_number_of_screws
        casing_yield_strength = self.casing_yield_strength
        screw_ultimate_strength = self.screw_ultimate_strength

        shear_safety_factor = np.zeros(max_number_of_screws)
        tear_safety_factor = np.zeros(max_number_of_screws)
        compression_safety_factor = np.zeros(max_number_of_screws)

        for screw_count in range(1, max_number_of_screws + 1):
            shear_area = (self.screw_diameter ** 2) * np.pi * 0.25

            tear_area = (
                (
                    np.pi
                    * 0.25
                    * (
                        (self.casing_outer_diameter ** 2)
                        - (self.casing_inner_diameter ** 2)
                    )
                )
                / screw_count
            ) - (
                np.arcsin(
                    (self.screw_clearance_diameter / 2)
                    / (self.casing_inner_diameter / 2)
                )
            ) * 0.25 * (
                (self.casing_outer_diameter ** 2)
                - (self.casing_inner_diameter ** 2)
            )

            compression_area = (
                ((self.casing_outer_diameter - self.casing_inner_diameter))
                * self.screw_clearance_diameter
                / 2
            )

            force_on_each_fastener = (
                np.max(chamber_pressure)
                * (np.pi * (self.casing_inner_diameter / 2) ** 2)
            ) / screw_count

            shear_stress = force_on_each_fastener / shear_area
            shear_safety_factor[screw_count - 1] = (
                screw_ultimate_strength / shear_stress
            )

            tear_stress = force_on_each_fastener / tear_area
            tear_safety_factor[screw_count - 1] = (
                casing_yield_strength / np.sqrt(3)
            ) / tear_stress

            compression_stress = force_on_each_fastener / compression_area
            compression_safety_factor[screw_count - 1] = (
                casing_yield_strength / compression_stress
            )

        fastener_safety_factor = np.vstack(
            (
                shear_safety_factor,
                tear_safety_factor,
                compression_safety_factor,
            )
        )
        max_safety_factor_fastener = np.max(
            np.min(fastener_safety_factor, axis=0)
        )
        optimal_fasteners = np.argmax(np.min(fastener_safety_factor, axis=0))

        return (
            optimal_fasteners,
            max_safety_factor_fastener,
            shear_safety_factor,
            tear_safety_factor,
            compression_safety_factor,
        )
