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

from rocketsolver.models.materials import Material
from rocketsolver.models.propulsion.thermals import ThermalLiner
from rocketsolver.utils.geometric import get_cylinder_volume


class CombustionChamber:
    def __init__(
        self,
        casing_inner_diameter: float,
        outer_diameter: float,
        liner: ThermalLiner,
        length: float,
        casing_material: Material,
        bulkhead_material: Material,
    ) -> None:
        self.casing_inner_diameter = casing_inner_diameter
        self.outer_diameter = outer_diameter
        self.liner = liner
        self.length = length
        self.casing_material = casing_material
        self.bulkhead_material = bulkhead_material

    @property
    def inner_diameter(self) -> float:
        return self.casing_inner_diameter - 2 * self.liner.thickness

    @property
    def inner_radius(self) -> float:
        return self.inner_diameter / 2

    @property
    def outer_radius(self) -> float:
        return self.outer_diameter / 2

    @property
    def casing_inner_radius(self) -> float:
        return self.casing_inner_diameter / 2

    def get_bulkhead_thickness(
        self, chamber_pressure: np.ndarray, safety_factor: float
    ) -> float:
        """
        Returns the thickness of a planar bulkhead pressure vessel.
        """
        return self.inner_diameter * (
            np.sqrt(
                (0.75 * chamber_pressure)
                / (self.bulkhead_material.yield_strength / safety_factor)
            )
        )

    def get_chamber_length(
        self,
        grain_length: float,
        grain_count: int,
        grain_spacing: float,
    ) -> float:
        """
        Returns the chamber length of the SRM, given the grain parameters.
        """
        return np.sum(grain_length) + (grain_count - 1) * grain_spacing

    def get_casing_stress_theta(self, chamber_pressure: float) -> float:
        return (
            (chamber_pressure * self.casing_inner_radius**2)
            / (self.outer_radius**2 - self.casing_inner_radius**2)
            * (
                1
                + ((self.outer_radius**2) / (self.casing_inner_radius**2))
            )
        )

    def get_casing_stress_radius(self, chamber_pressure: float) -> float:
        return (
            (chamber_pressure * self.casing_inner_radius**2)
            / (self.outer_radius**2 - self.casing_inner_radius**2)
            * (1 - ((self.outer_radius) / (self.casing_inner_radius)) ** 2)
        )

    def get_casing_stress_z(self, chamber_pressure: float) -> float:
        return (
            2
            * chamber_pressure
            * self.casing_inner_radius**2
            / (self.outer_radius**2 - self.casing_inner_radius**2)
        )

    def get_casing_safety_factor(self, chamber_pressure: np.ndarray) -> float:
        """
        Returns the thickness for a cylindrical pressure vessel, using
        Von Misses criteria.
        """
        casing_yield_strength = self.casing_material.yield_strength
        max_chamber_pressure = chamber_pressure

        gama_z = self.get_casing_stress_z(max_chamber_pressure)
        gama_r = self.get_casing_stress_radius(max_chamber_pressure)
        gama_theta = self.get_casing_stress_theta(max_chamber_pressure)

        return casing_yield_strength / np.sqrt(
            (
                (gama_z - gama_r) ** 2
                + (gama_r - gama_theta) ** 2
                + (gama_theta - gama_z) ** 2
            )
            / 2
        )

    def get_empty_volume(self) -> None:
        return get_cylinder_volume(self.inner_diameter, self.length)


class BoltedCombustionChamber(CombustionChamber):
    def __init__(
        self,
        casing_inner_diameter: float,
        outer_diameter: float,
        liner: ThermalLiner,
        length: float,
        casing_material: Material,
        bulkhead_material: Material,
        screw_material: Material,
        max_screw_count: int,
        screw_clearance_diameter: float,
        screw_diameter: float,
    ) -> None:
        super().__init__(
            casing_inner_diameter,
            outer_diameter,
            liner,
            length,
            casing_material,
            bulkhead_material,
        )
        self.screw_material = screw_material
        self.max_screw_count = max_screw_count
        self.screw_clearance_diameter = screw_clearance_diameter
        self.screw_diameter = screw_diameter

    def get_shear_area(self) -> float:
        return (self.screw_diameter**2) * np.pi * 0.25

    def get_tear_area(self, screw_count: int) -> float:
        """
        Calculates tear area for screw section.
        """
        return (
            (
                np.pi
                * 0.25
                * ((self.outer_diameter**2) - (self.inner_diameter**2))
            )
            / screw_count
        ) - (
            np.arcsin(
                (self.screw_clearance_diameter / 2) / (self.inner_diameter / 2)
            )
        ) * 0.25 * (
            (self.outer_diameter**2) - (self.inner_diameter**2)
        )

    def get_compression_area(self) -> float:
        return (
            ((self.outer_diameter - self.inner_diameter))
            * self.screw_clearance_diameter
            / 2
        )

    def get_force_on_each_fastener(
        self, screw_count: int, chamber_pressure: float
    ) -> float:
        return (
            chamber_pressure * (np.pi * (self.inner_diameter / 2) ** 2)
        ) / screw_count

    def get_optimal_fasteners(self, chamber_pressure: np.ndarray):
        max_screw_count = self.max_screw_count
        casing_yield_strength = self.casing_material.yield_strength
        screw_ultimate_strength = self.screw_material.ultimate_strength

        shear_safety_factor = np.zeros(max_screw_count)
        tear_safety_factor = np.zeros(max_screw_count)
        compression_safety_factor = np.zeros(max_screw_count)

        for screw_count in range(1, max_screw_count + 1):
            shear_area = self.get_shear_area()
            tear_area = self.get_tear_area(screw_count)
            compression_area = self.get_compression_area()

            force_on_each_fastener = self.get_force_on_each_fastener(
                screw_count=screw_count, chamber_pressure=chamber_pressure
            )

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
