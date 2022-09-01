# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import scipy
import numpy as np


def get_percentage_error(numerator: float, denominator: float) -> float:
    """
    Returns percentage error between a numerator and a denominator.
    """
    return ((numerator - denominator) / denominator) * 100


def multiply_matrix(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    return np.matmul(A, B)


def divide_matrix(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    try:
        return np.linalg.solve(B.conj().T, A.conj().T).conj().T
    except np.linalg.LinAlgError:
        return scipy.linalg.lstsq(A, B)
