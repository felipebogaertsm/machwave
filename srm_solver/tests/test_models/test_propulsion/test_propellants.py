# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import numpy as np

from models.propulsion.propellant import Propellant


def _test_propellant_burn_rate(propellant: Propellant):
    burn_rate_map = propellant.burn_rate

    # Getting pressure range covered by burn rate map:
    min_pressure = np.min(list(map(lambda item: item["min"], burn_rate_map)))
    max_pressure = np.min(list(map(lambda item: item["max"], burn_rate_map)))

    burn_rate = propellant.get_burn_rate(min_pressure)
    assert isinstance(burn_rate, float)

    burn_rate = propellant.get_burn_rate(max_pressure)
    assert isinstance(burn_rate, float)


def test_propellant_burn_rate_KNSB_NAKKA(propellant_KNSB_NAKKA):
    _test_propellant_burn_rate(propellant=propellant_KNSB_NAKKA)


def test_propellant_burn_rate_KNDX(propellant_KNDX):
    _test_propellant_burn_rate(propellant=propellant_KNDX)


def test_propellant_burn_rate_KNER(propellant_KNER):
    _test_propellant_burn_rate(propellant=propellant_KNER)


def test_propellant_burn_rate_KNSB(propellant_KNSB):
    _test_propellant_burn_rate(propellant=propellant_KNSB)


def test_propellant_burn_rate_KNSU(propellant_KNSU):
    _test_propellant_burn_rate(propellant=propellant_KNSU)
