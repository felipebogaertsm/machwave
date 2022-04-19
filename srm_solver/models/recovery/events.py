# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import numpy as np

from models.recovery.parachutes import Parachute


class RecoveryEvent:
    def __init__(self, trigger_value, parachute: Parachute) -> None:
        self.trigger_value = trigger_value
        self.parachute = parachute

    def is_active(self):
        pass


class AltitudeBasedEvent(RecoveryEvent):
    def is_active(self, height: float, velocity: float) -> bool:
        if velocity < 0 and height < self.trigger_value:
            return True
        else:
            return False


class ApogeeBasedEvent(RecoveryEvent):
    def is_active(
        self,
        height: np.array,
        time: np.array,
        propellant_mass: float,
        time_after_apogee: float,
    ):
        max_height_index = np.argmax(height)
        apogee_time = time[max_height_index]

        if (
            propellant_mass == 0
            and time[-1] >= time_after_apogee + apogee_time
        ):
            return True

        return False
