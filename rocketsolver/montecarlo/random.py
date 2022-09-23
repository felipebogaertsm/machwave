# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class RandomGenerator(ABC):
    """
    Abstract class for a random number generator.
    """

    value: float | int
    lower_tolerance: Optional[float | int] = 0
    upper_tolerance: Optional[float | int] = 0
    tolerance: Optional[float | int] = 0

    def __post_init__(self) -> None:
        pass

    @abstractmethod
    def get_value(self) -> float:
        """
        Gets a random value based on a probability distribution.

        :return: Random value
        :rtype: float
        """
        pass


@dataclass
class NormalRandomGenerator(RandomGenerator):
    def __post_init__(self) -> None:
        super().__post_init__()

        if self.lower_tolerance != 0 or self.upper_tolerance != 0:
            raise ValueError(
                "NormalRandomGenerator does not support lower/upper tolerances."
            )

    def get_value(self) -> float:
        """
        Gets a random value based on a normal probability distribution.

        In numpy.random, "scale" determines the standard deviation of the
        normal distribution. In this case, the tolerance is defined as 3 times
        the standard deviation, so that ~99.7% of the generated values are
        within tolerance.

        :return: Random value
        :rtype: float
        """
        return np.random.normal(loc=self.value, scale=self.tolerance / 3)


@dataclass
class UniformRandomGenerator(RandomGenerator):
    def __post_init__(self) -> None:
        super().__post_init__()

        if (self.lower_tolerance or self.upper_tolerance) and self.tolerance:
            raise ValueError(
                "UniformRandomGenerator does not support lower/upper "
                "tolerances and simmetrical tolerances simultaneously."
            )

    def get_value(self) -> float:
        """
        Gets a random value based on a normal probability distribution.

        :return: Random value
        :rtype: float
        """
        return np.random.uniform(
            low=self.value - self.lower_tolerance - self.tolerance,
            high=self.value + self.upper_tolerance + self.tolerance,
        )


def get_random_generator(
    probability_distribution: str, *args, **kwargs
) -> RandomGenerator:
    """
    Gets a random generator based on a probability distribution.

    :param probability_distribution: Probability distribution
    :return: Random generator
    :rtype: None
    """
    if probability_distribution == "normal":
        return NormalRandomGenerator(*args, **kwargs)
    elif probability_distribution == "uniform":
        return UniformRandomGenerator(*args, **kwargs)

    raise ValueError(
        f'Probability distribution "{probability_distribution}" not supported.'
    )
