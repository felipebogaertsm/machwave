from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


@dataclass
class RandomGenerator(ABC):
    """
    Abstract class for a random number generator.

    Attributes:
        value (float): The nominal or mean value of the parameter.
        spread (float | tuple[float, float]): The spread of the
            parameter (default: 0).

    Methods:
        get_value(): Gets a random value based on a probability
            distribution. Implemented in subclasses.
    """

    value: float
    spread: float | tuple[float, float] = 0

    def __post_init__(self) -> None:
        """
        Ensures non-negative spread values and valid inputs.
        """
        if isinstance(self.spread, tuple):
            if len(self.spread) != 2 or self.spread[0] < 0 or self.spread[1] < 0:
                raise ValueError("Spread must be a tuple of two non-negative values.")
        elif self.spread < 0:
            raise ValueError("Spread must be a non-negative value.")

    @abstractmethod
    def get_value(self) -> float:
        """
        Gets a random value based on a probability distribution.

        Returns:
            Random value.
        """
        pass


@dataclass
class NormalRandomGenerator(RandomGenerator):
    """
    Random number generator based on a normal distribution.

    - Uses `spread` as 3 sigma (99.7% confidence interval).

    Raises:
        ValueError: If `spread` is specified as a tuple.
    """

    def __post_init__(self) -> None:
        """
        Ensures `spread` is not set as a tuple.

        Raises:
            ValueError: If `spread` is specified as a tuple.
        """
        super().__post_init__()

        if isinstance(self.spread, tuple):
            raise ValueError("NormalRandomGenerator does not support tuple spreads.")

    def get_value(self) -> float:
        """
        In numpy.random, "scale" determines the standard deviation of the
        normal distribution. In this case, the spread is defined as 3 times
        the standard deviation, so that ~99.7% of the generated values are
        within spread.

        Returns:
            Random value based on a normal probability distribution.
        """
        sigma = self.spread / 3 if self.spread != 0 else 1e-6
        return np.random.normal(
            loc=self.value,
            scale=sigma,
        )


@dataclass
class UniformRandomGenerator(RandomGenerator):
    """
    Random number generator based on a uniform distribution.

    - Uses `spread` as the total width of the distribution.

    Raises:

    """

    def get_value(self) -> float:
        """
        Gets a random value based on a uniform probability distribution.

        Returns:
            Random value within the range defined by the value and spread.
        """
        if isinstance(self.spread, tuple):
            lower_bound, upper_bound = self.spread
        else:
            lower_bound = self.value - self.spread / 2
            upper_bound = self.value + self.spread / 2

        return np.random.uniform(
            low=lower_bound,
            high=upper_bound,
        )


def get_random_generator(
    probability_distribution: str, *args, **kwargs
) -> RandomGenerator:
    """
    Gets a random generator based on a probability distribution.

    Args:
        probability_distribution (str): The probability distribution ("normal"
            or "uniform").
        *args: Additional arguments for the random generator constructor.
        **kwargs: Additional keyword arguments for the random generator
            constructor.

    Returns:
        RandomGenerator: An instance of the appropriate random generator.

    Raises:
        ValueError: If the specified probability distribution is not supported.
    """
    if probability_distribution == "normal":
        return NormalRandomGenerator(*args, **kwargs)
    elif probability_distribution == "uniform":
        return UniformRandomGenerator(*args, **kwargs)

    raise ValueError(
        f'Probability distribution "{probability_distribution}" not supported.'
    )
