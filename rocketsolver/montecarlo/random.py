from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class RandomGenerator(ABC):
    """
    Abstract class for a random number generator.

    Attributes:
        value (float | int): The main value of the random generator.
        lower_tolerance (Optional[float | int]): The lower bound of the
            parameter (default: 0).
        upper_tolerance (Optional[float | int]): The upper bound of the
            parameter (default: 0).
        tolerance (Optional[float | int]): The tolerance of the parameter
            (default: 0).

    Methods:
        get_value(): Gets a random value based on a probability distribution.

    """

    value: float | int
    lower_tolerance: Optional[float | int] = 0
    upper_tolerance: Optional[float | int] = 0
    tolerance: Optional[float | int] = 0

    def __post_init__(self) -> None:
        """
        Post-initialization method. Can be overridden in derived classes if
        additional setup is required.

        Returns:
            None
        """
        pass

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

    Attributes:
        value (float | int): The main value of the random generator.
        lower_tolerance (Optional[float | int]): The lower bound of the
            parameter (default: 0).
        upper_tolerance (Optional[float | int]): The upper bound of the
            parameter (default: 0).
        tolerance (Optional[float | int]): The tolerance of the parameter
            (default: 0).

    Methods:
        get_value(): Gets a random value based on a normal probability distribution.

    """

    def __post_init__(self) -> None:
        """
        Post-initialization method. Raises an exception if lower/upper
        tolerances are specified.

        Raises:
            ValueError: If lower/upper tolerances are specified.

        Returns:
            None
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
        return np.random.normal(loc=self.value, scale=self.tolerance / 3)


@dataclass
class UniformRandomGenerator(RandomGenerator):
    """
    Random number generator based on a uniform distribution.

    Attributes:
        value (float | int): The main value of the random generator.
        lower_tolerance (Optional[float | int]): The lower bound of the
            parameter (default: 0).
        upper_tolerance (Optional[float | int]): The upper bound of the
            parameter (default: 0).
        tolerance (Optional[float | int]): The tolerance of the parameter
            (default: 0).

    Methods:
        get_value(): Gets a random value based on a uniform probability distribution.

    """

    def __post_init__(self) -> None:
        """
        Post-initialization method. Raises an exception if both lower/upper
        tolerances and a symmetrical tolerance are specified.

        Raises:
            ValueError: If conflicting tolerances are specified.

        Returns:
            None
        """
        super().__post_init__()

        if (self.lower_tolerance or self.upper_tolerance) and self.tolerance:
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
