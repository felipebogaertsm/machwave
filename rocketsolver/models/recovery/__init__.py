# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
Stores Recovery class and methods.
"""

import numpy as np

from .events import RecoveryEvent


class Recovery:
    def __init__(self) -> None:
        self.events = []

    def add_event(self, recovery_event: RecoveryEvent) -> None:
        self.events.append(recovery_event)

    def get_drag_coefficient_and_area(
        self,
        height: np.ndarray,
        time: np.ndarray,
        velocity: np.ndarray,
        propellant_mass: np.ndarray,
    ) -> float:
        drag_coefficient = 0
        area = 0

        for event in self.events:
            if event.is_active(height, time, velocity, propellant_mass):
                drag_coefficient += event.parachute.drag_coefficient
                area += event.parachute.area
            else:
                pass

        return drag_coefficient, area
