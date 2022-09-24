# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from abc import ABC, abstractmethod

from .. import GrainSegment


class FMMGrainSegment(GrainSegment, ABC):
    @abstractmethod
    def get_burn_area(self, web_distance: float) -> float:
        """
        Not yet implemented.
        """
        pass

    @abstractmethod
    def get_volume(self, web_distance: float) -> float:
        """
        Not yet implemented.
        """
        pass
