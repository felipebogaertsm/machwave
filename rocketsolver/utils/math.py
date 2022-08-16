# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.


def get_percentage_error(numerator: float, denominator: float) -> float:
    """
    Returns percentage error between a numerator and a denominator.
    """
    return ((numerator - denominator) / denominator) * 100
