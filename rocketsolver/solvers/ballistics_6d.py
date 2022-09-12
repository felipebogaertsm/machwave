# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import numpy as np

from rocketsolver.solvers import Solver
from rocketsolver.utils.odes import ballistics_6dof_ode


class Ballistics6D(Solver):
    def solve(
        self,
        M: np.ndarray,
        C: np.ndarray,
        V: np.ndarray,
        D: np.ndarray,
        G: np.ndarray,
        tau: np.ndarray,
        d_t: float,
    ) -> float:

        k_1 = ballistics_6dof_ode(M, C, V, D, G, tau)
        k_2 = ballistics_6dof_ode(M, C, V + 0.5 * k_1 * d_t, D, G, tau)
        k_3 = ballistics_6dof_ode(M, C, V + 0.5 * k_2 * d_t, D, G, tau)
        k_4 = ballistics_6dof_ode(M, C, V + 0.5 * k_3 * d_t, D, G, tau)

        return V + (1 / 6) * (k_1 + 2 * (k_2 + k_3) + k_4) * d_t
