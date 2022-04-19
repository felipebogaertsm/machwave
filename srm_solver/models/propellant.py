# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
n_ce: Combustion, two phase, heat loss, friction inefficiency factor
pp: Propellant density [kg/m^3]
k_mix_ch: Isentropic exponent (chamber)
k_2ph_ex: Isentropic exponent (exhaust)
T0_ideal: Ideal combustion temperature [K]
T0: Real combustion temperature [K]
M_ch: Molar weight (chamber) [100g/mole]
M_ex: Molar weight (exhaust) [100g/mole]
Isp_frozen, Isp_shifting: Frozen and shifting specific getImpulses [s]
qsi_ch: Number of condensed phase moles per 100 gram (chamber) [mole]
qsi_ex: Number of condensed phase moles per 100 gram (exhaust) [mole]
"""

import scipy.constants


class Propellant:
    def __init__(
        self,
        burn_rate,
        n_ce,
        pp,
        k_mix_ch,
        k_2ph_ex,
        T0_ideal,
        M_ch,
        M_ex,
        Isp_frozen,
        Isp_shifting,
        qsi_ch,
        qsi_ex,
    ):
        self.burn_rate = burn_rate
        self.n_ce = n_ce
        self.pp = pp
        self.k_mix_ch = k_mix_ch
        self.k_2ph_ex = k_2ph_ex
        # Real combustion temperature based on the ideal temp. and the combustion efficiency [K]:
        self.T0 = T0_ideal * n_ce
        self.M_ch = M_ch
        self.M_ex = M_ex
        # Gas constant per molecular weight calculations:
        self.R_ch = scipy.constants.R / M_ch
        self.R_ex = scipy.constants.R / M_ex
        self.Isp_frozen = Isp_frozen
        self.Isp_shifting = Isp_shifting
        self.qsi_ch = qsi_ch
        self.qsi_ex = qsi_ex

    def get_burn_rate(self, chamber_pressure):
        """
        chamber_pressure must be in Pascals.
        """
        for item in self.burn_rate:
            if item["min"] < chamber_pressure < item["max"]:
                a = item["a"]
                n = item["n"]
                return (a * (chamber_pressure * 1e-6) ** n) * 1e-3  # in m/s

        raise Exception("Chamber pressure out of bounds for burn rate")
