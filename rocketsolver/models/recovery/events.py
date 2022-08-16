# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
Recovery events are implemented using Strategy design pattern.
"""

from abc import ABC, abstractmethod
import numpy as np

from models.recovery.parachutes import Parachute


class RecoveryEvent(ABC):
    def __init__(self, trigger_value: float, parachute: Parachute) -> None:
        self.trigger_value = trigger_value
        self.parachute = parachute

    @abstractmethod
    def is_active(
        self,
        height: np.ndarray,
        time: np.ndarray,
        velocity: np.ndarray,
        propellant_mass: np.ndarray,
    ) -> bool:
        return False


class AltitudeBasedEvent(RecoveryEvent):
    def is_active(
        self,
        height: np.ndarray,
        time: np.ndarray,
        velocity: np.ndarray,
        propellant_mass: np.ndarray,
    ) -> bool:
        if velocity[-1] < 0 and height[-1] < self.trigger_value:
            return True
        else:
            return False


class ApogeeBasedEvent(RecoveryEvent):
    def __init__(self, trigger_value: float, parachute: Parachute) -> None:
        """
        :param trigger_value: represents parachute activation time delay after
            vehicle hits apogee
        :param parachute: parachute class
        :return: None
        """
        super().__init__(trigger_value, parachute)

    def is_active(
        self,
        height: np.ndarray,
        time: np.ndarray,
        velocity: np.ndarray,
        propellant_mass: float,
    ) -> bool:
        max_height_index = np.argmax(height)
        apogee_time = time[max_height_index]

        if (
            propellant_mass == 0
            and velocity[-1] < 0
            and time[-1] >= self.trigger_value + apogee_time
        ):
            return True
        else:
            return False
