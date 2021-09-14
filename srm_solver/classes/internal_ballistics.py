# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
Stores Internal Ballistics class and methods
"""


class InternalBallistics:
    def __init__(self, t, P0, T, T_mean, I_total, I_sp, t_burnout, t_thrust, nozzle_eff, E_opt, V_prop_CP, A_burn_CP,
                 Kn, m_prop, grain_mass_flux, optimal_grain_length, initial_port_to_throat, burn_profile, V_empty,
                 initial_to_final_kn, P_exit):
        self.t = t
        self.P0 = P0
        self.T = T
        self.T_mean = T_mean
        self.I_total = I_total
        self.I_sp = I_sp
        self.t_burnout = t_burnout
        self.t_thrust = t_thrust
        self.nozzle_eff = nozzle_eff
        self.E_opt = E_opt
        self.V_prop = V_prop_CP
        self.A_burn = A_burn_CP
        self.Kn = Kn
        self.m_prop = m_prop
        self.grain_mass_flux = grain_mass_flux
        self.optimal_grain_length = optimal_grain_length
        self.initial_port_to_throat = initial_port_to_throat
        self.burn_profile = burn_profile
        self.V_empty = V_empty
        self.initial_to_final_kn = initial_to_final_kn
        self.P_exit = P_exit
