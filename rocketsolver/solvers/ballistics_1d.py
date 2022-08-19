# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from typing import Tuple

from rocketsolver.solvers import Solver
from rocketsolver.utils.odes import ballistics_ode


class Ballistics1D(Solver):
    def solve(
        self, height, velocity, thrust, D, vehicle_mass, gravity, d_t
    ) -> Tuple[float]:
        p_1, l_1 = ballistics_ode(
            height, velocity, thrust, D, vehicle_mass, gravity
        )
        p_2, l_2 = ballistics_ode(
            height + 0.5 * p_1 * d_t,
            velocity + 0.5 * l_1 * d_t,
            thrust,
            D,
            vehicle_mass,
            gravity,
        )
        p_3, l_3 = ballistics_ode(
            height + 0.5 * p_2 * d_t,
            velocity + 0.5 * l_2 * d_t,
            thrust,
            D,
            vehicle_mass,
            gravity,
        )
        p_4, l_4 = ballistics_ode(
            height + 0.5 * p_3 * d_t,
            velocity + 0.5 * l_3 * d_t,
            thrust,
            D,
            vehicle_mass,
            gravity,
        )

        height = height + (1 / 6) * (p_1 + 2 * (p_2 + p_3) + p_4) * d_t
        velocity = velocity + (1 / 6) * (l_1 + 2 * (l_2 + l_3) + l_4) * d_t
        acceleration = (1 / 6) * (l_1 + 2 * (l_2 + l_3) + l_4)

        return (height, velocity, acceleration)
