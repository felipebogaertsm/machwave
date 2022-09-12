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
        return multiply_matrix(A, np.linalg.pinv(B))
    except ValueError:
        return multiply_matrix(A, np.transpose(np.linalg.pinv(B)))


def cumtrapz_matrices(
    y: np.ndarray, x: np.ndarray, *args, **kwargs
) -> np.ndarray:
    """
    Returns the cumulative integral of a matrix.
    """

    cumtrapz_result = np.array([])

    for i in range(np.shape(y)[1]):
        y_matrix = np.array([y[index][i][0] for index in range(len(y))])

        trapz_integration = scipy.integrate.cumtrapz(
            y_matrix, x, *args, **kwargs
        )

        cumtrapz_result = np.append(
            cumtrapz_result,
            trapz_integration,
        )

    return np.transpose([cumtrapz_result])
