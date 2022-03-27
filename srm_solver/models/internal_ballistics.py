# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
Stores Internal Ballistics class and methods
"""

from dataclasses import dataclass
import numpy as np


@dataclass()
class InternalBallistics:
    t: np.array
    P0: np.array
    T: np.array
    T_mean: float
    I_total: float
    I_sp: float
    t_burnout: float
    t_thrust: float
    nozzle_eff: np.array
    E_opt: float
    V_prop: np.array
    A_burn: np.array
    Kn: np.array
    m_prop: np.array
    grain_mass_flux: np.array
    optimal_grain_length: np.array
    initial_port_to_throat: float
    burn_profile: str
    V_empty: float
    initial_to_final_kn: float
    P_exit: np.array
