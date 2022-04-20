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

from models.materials import Material
from models.motor.thermals import ThermalLiner
from utils.geometric import get_circle_area


class Nozzle:
    def __init__(
        self,
        throat_diameter,
        divergent_angle,
        convergent_angle,
        expansion_ratio,
        material=None,
    ) -> None:
        self.throat_diameter = throat_diameter
        self.divergent_angle = divergent_angle
        self.convergent_angle = convergent_angle
        self.expansion_ratio = expansion_ratio
        self.material = material

    def get_throat_area(self):
        return get_circle_area(self.nozzle_throat_diameter)

    def get_nozzle_thickness(
        self,
        chamber_pressure,
    ):
        """Returns nozzle convergent and divergent thickness"""
        max_chamber_pressure = np.max(chamber_pressure)
        convergent_angle = self.convergent_angle
        divergent_angle = self.divergent_angle
        nozzle_yield_strength = self.material.yield_strength

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


class CombustionChamber:
    def __init__(
        self,
        inner_diameter: float,
        outer_diameter: float,
        liner: ThermalLiner,
        length: float,
        C1: float,
        C2: float,
        casing_material: Material,
        bulkhead_material: Material,
    ) -> None:
        self.inner_diameter = inner_diameter
        self.outer_diameter = outer_diameter
        self.liner = liner
        self.length = length
        self.C1 = C1
        self.C2 = C2
        self.casing_material = casing_material
        self.bulkhead_material = bulkhead_material

    def get_bulkhead_thickness(self, chamber_pressure):
        """
        Returns the thickness of a plane bulkhead pressure vessel.
        """
        return self.inner_diameter * (
            np.sqrt(
                (0.75 * np.max(chamber_pressure))
                / (self.bulkhead_material.yield_strength / self.safety_factor)
            )
        )

    def get_chamber_length(self, grain_length, grain_count, grain_spacing):
        """
        Returns the chamber length of the SRM, given the grain parameters.
        """
        return np.sum(grain_length) + (grain_count - 1) * grain_spacing

    def get_casing_safety_factor(self, chamber_pressure):
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


class BoltedCombustionChamber(CombustionChamber):
    def __init__(
        self,
        inner_diameter: float,
        outer_diameter: float,
        liner: ThermalLiner,
        length: float,
        C1: float,
        C2: float,
        casing_material: Material,
        bulkhead_material: Material,
        screw_material: Material,
        max_screw_count: int,
        screw_clearance_diameter: float,
        screw_diameter: float,
    ) -> None:
        super().__init__(
            inner_diameter,
            outer_diameter,
            liner,
            length,
            C1,
            C2,
            casing_material,
            bulkhead_material,
        )
        self.screw_material = screw_material
        self.max_screw_count = max_screw_count
        self.screw_clearance_diameter = screw_clearance_diameter
        self.screw_diameter = screw_diameter

    def get_chamber_inner_diameter(
        self,
        casing_inner_diameter,
        liner_thickness,
    ):
        return casing_inner_diameter - 2 * liner_thickness

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


class MotorStructure:
    def __init__(
        self,
        safety_factor,
        dry_mass,
        nozzle: Nozzle,
        chamber: CombustionChamber,
    ):
        self.safety_factor = safety_factor
        self.dry_mass = dry_mass
        self.nozzle = nozzle
        self.chamber = chamber
