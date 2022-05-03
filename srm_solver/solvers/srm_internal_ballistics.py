# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from typing import Any, Callable, List

from solvers import Solver
from utils.odes import ballistics_ode


class SRMInternalBallisticsSolver(Solver):
    def solve(
        self,
        chamber_pressure: float,
        external_pressure: float,
        burn_area: float,
        propellant_volume: float,
        nozzle_area: float,
        propellant_density: float,
        k_mix_ch: float,
        R_ch: float,
        T_O: float,
    ) -> List[float]:
        pass
