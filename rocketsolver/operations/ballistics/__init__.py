# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from abc import abstractmethod
from .. import Operation


class BallisticOperation(Operation):
    @property
    @abstractmethod
    def apogee(self) -> float:
        pass

    @property
    @abstractmethod
    def apogee_time(self) -> float:
        pass

    @property
    @abstractmethod
    def max_velocity(self) -> float:
        pass

    @property
    @abstractmethod
    def max_velocity_time(self) -> float:
        pass
