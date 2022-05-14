# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import pytest
import numpy as np


def test_propellant_burn_rate(propellant_KNSB_NAKKA):
    burn_rate_map = propellant_KNSB_NAKKA.burn_rate

    # Getting pressure range covered by burn rate map:
    min_pressure = np.min(list(map(lambda item: item["min"], burn_rate_map)))
    max_pressure = np.min(list(map(lambda item: item["max"], burn_rate_map)))

    burn_rate = propellant_KNSB_NAKKA.get_burn_rate(min_pressure)
    assert isinstance(burn_rate, float)

    burn_rate = propellant_KNSB_NAKKA.get_burn_rate(max_pressure)
    assert isinstance(burn_rate, float)
