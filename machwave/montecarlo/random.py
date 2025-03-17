from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


@dataclass
class RandomGenerator(ABC):
    """
    Abstract class for a random number generator.

    Attributes:
        value: The main value of the random generator.
        lower_tolerance: The lower bound of the parameter (default: 0).
        upper_tolerance: The upper bound of the parameter (default: 0).
        tolerance: The tolerance of the parameter (default: 0).

    Methods:
        get_value(): Gets a random value based on a probability distribution.
    """

    value: float
    lower_tolerance: float = 0
    upper_tolerance: float = 0
    tolerance: float = 0

    def __post_init__(self) -> None:
        """
        Ensures non-negative tolerance values and valid inputs.
        """
        if self.lower_tolerance < 0 or self.upper_tolerance < 0 or self.tolerance < 0:
            raise ValueError("Tolerances must be non-negative values.")

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

    - Uses `tolerance` as 3σ (99.7% confidence interval).
    - Does **not** support `lower_tolerance` and `upper_tolerance`.

    Raises:
        ValueError: If `lower_tolerance` or `upper_tolerance` is specified.
    """

    def __post_init__(self) -> None:
        """
        Ensures `lower_tolerance` and `upper_tolerance` are not set.

        Raises:
            ValueError: If `lower_tolerance` or `upper_tolerance` is specified.
        """
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

        Returns:
            Random value.
        """
        return np.random.normal(
            loc=self.value,
            scale=(
                self.tolerance / 3 if self.tolerance != 0 else 1e-6
            ),  # Prevent division by zero
        )


@dataclass
class UniformRandomGenerator(RandomGenerator):
    """
    Random number generator based on a uniform distribution.

    - Can use either `lower_tolerance` and `upper_tolerance` **or** `tolerance`, but not both.

    Raises:
        ValueError: If both `tolerance` and `lower_tolerance`/`upper_tolerance` are set.
    """

    def __post_init__(self) -> None:
        """
        Ensures valid tolerances.

        Raises:
            ValueError: If both `tolerance` and `lower_tolerance`/`upper_tolerance` are set.
        """
        super().__post_init__()

        if (
            self.lower_tolerance != 0 or self.upper_tolerance != 0
        ) and self.tolerance != 0:
            raise ValueError(
                "UniformRandomGenerator does not support lower/upper "
                "tolerances and symmetrical tolerance simultaneously."
            )

    def get_value(self) -> float:
        """
        Gets a random value based on a uniform probability distribution.

        Returns:
            Random value.
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
