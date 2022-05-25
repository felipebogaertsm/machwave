# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import pytest

from models.atmosphere import Atmosphere1976
from models.propellants import KNDX, KNER, KNSB, KNSB_NAKKA, KNSU


@pytest.fixture
def propellant_KNDX():
    return KNDX


@pytest.fixture
def propellant_KNER():
    return KNER


@pytest.fixture
def propellant_KNSB():
    return KNSB


@pytest.fixture
def propellant_KNSB_NAKKA():
    return KNSB_NAKKA


@pytest.fixture
def propellant_KNSU():
    return KNSU


@pytest.fixture
def atmosphere_1976():
    return Atmosphere1976()
