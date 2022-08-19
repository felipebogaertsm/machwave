# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from abc import abstractmethod

from rocketsolver.solvers import Solver
from rocketsolver.utils.odes import solve_cp_seidel


class InternalBallisticsSolver(Solver):
    @abstractmethod
    def solve(self) -> float:
        """
        Solves the chamber pressure in function of input parameters.

        The input parameters will depend on the motor category: SRM, HRE
        or LRE.
        """
        pass


class SRMInternalBallisticsSolver(InternalBallisticsSolver):
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
        burn_rate: float,
        d_t: float,
    ) -> float:
        k_1 = solve_cp_seidel(
            chamber_pressure,
            external_pressure,
            burn_area,
            propellant_volume,
            nozzle_area,
            propellant_density,
            k_mix_ch,
            R_ch,
            T_O,
            burn_rate,
        )

        k_2 = solve_cp_seidel(
            chamber_pressure + 0.5 * k_1 * d_t,
            external_pressure,
            burn_area,
            propellant_volume,
            nozzle_area,
            propellant_density,
            k_mix_ch,
            R_ch,
            T_O,
            burn_rate,
        )

        k_3 = solve_cp_seidel(
            chamber_pressure + 0.5 * k_2 * d_t,
            external_pressure,
            burn_area,
            propellant_volume,
            nozzle_area,
            propellant_density,
            k_mix_ch,
            R_ch,
            T_O,
            burn_rate,
        )

        k_4 = solve_cp_seidel(
            chamber_pressure + 0.5 * k_3 * d_t,
            external_pressure,
            burn_area,
            propellant_volume,
            nozzle_area,
            propellant_density,
            k_mix_ch,
            R_ch,
            T_O,
            burn_rate,
        )

        new_chamber_pressure = (
            chamber_pressure + (1 / 6) * (k_1 + 2 * (k_2 + k_3) + k_4) * d_t
        )

        # In order to avoid RK4 blow up with a large d_t:
        assert new_chamber_pressure >= 0, "Chamber pressure is negative"

        return new_chamber_pressure
