# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.


class RecoveryEvent:
    def __init__(
        self,
        trigger_type,
        trigger_value,
    ) -> None:
        self.trigger_type = trigger_type
        self.trigger_value = trigger_value


class ParachuteEvent(RecoveryEvent):
    def __init__(
        self,
        trigger_type,
        trigger_value,
        parachute,
    ) -> None:
        super().__init__(trigger_type, trigger_value)

        self.parachute = parachute
