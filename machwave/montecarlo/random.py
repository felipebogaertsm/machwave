from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TypeAlias, TypeVar

import numpy as np


@dataclass(slots=True, frozen=True)
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
    spread: float | tuple[float, float] = 0.0

    def __post_init__(self) -> None:
        """
        Ensures non-negative spread values and valid inputs.
        """
        if isinstance(self.spread, tuple):
            if len(self.spread) != 2 or self.spread[0] < 0 or self.spread[1] < 0:
                raise ValueError("Spread must be a tuple of two non-negative values.")
        elif self.spread < 0.0:
            raise ValueError("Spread must be a non-negative value.")

    @abstractmethod
    def get_value(self) -> float:
        """
        Gets a random value based on a probability distribution.

        Returns:
            Random value.
        """
        pass


@dataclass(slots=True, frozen=True)
class NormalRandomGenerator(RandomGenerator):
    """
    Random number generator based on a normal distribution.

    - Uses `spread` as 3 sigma (99.7% confidence interval).

    Raises:
        ValueError: If `spread` is specified as a tuple.
    """

    _sigma: float = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """
        Ensures `spread` is not set as a tuple.

        Raises:
            ValueError: If `spread` is specified as a tuple.
        """
        RandomGenerator.__post_init__(self)

        if not isinstance(self.spread, float):
            raise ValueError("NormalRandomGenerator does not support tuple spreads.")

        sigma = self.spread / 3
        object.__setattr__(self, "_sigma", sigma)

    def get_value(self) -> float:
        """
        In numpy.random, "scale" determines the standard deviation of the
        normal distribution. In this case, the spread is defined as 3 times
        the standard deviation, so that ~99.7% of the generated values are
        within spread.

        Returns:
            Random value based on a normal probability distribution.
        """
        return np.random.normal(
            loc=self.value,
            scale=self._sigma,
        )


@dataclass(slots=True, frozen=True)
class UniformRandomGenerator(RandomGenerator):
    """
    Random number generator based on a uniform distribution.

    - Uses `spread` as the total width of the distribution.
    """

    def get_value(self) -> float:
        """
        Gets a random value based on a uniform probability distribution.

        Returns:
            Random value within the range defined by the value and spread.
        """
        if isinstance(self.spread, tuple):
            lower_bound, upper_bound = self.spread
            if lower_bound >= upper_bound:
                raise ValueError("Spread tuple must be (low, high) with low < high.")
        else:
            lower_bound = self.value - self.spread / 2
            upper_bound = self.value + self.spread / 2

        return np.random.uniform(
            low=lower_bound,
            high=upper_bound,
        )


T = TypeVar("T", bound="RandomGenerator")
FactoryFn: TypeAlias = Callable[..., T]

_GENERATOR_REGISTRY: dict[str, FactoryFn] = {
    "normal": NormalRandomGenerator,
    "uniform": UniformRandomGenerator,
}


def register_random_generator(name: str, ctor: FactoryFn) -> None:
    """
    Adds a new random generator to the registry at runtime.

    Args:
        name (str): Name of the generator (case-insensitive).
        ctor (FactoryFn): Constructor function for the generator.
    Raises:
        ValueError: If the name is already registered.
    """
    if name.lower() in _GENERATOR_REGISTRY:
        raise ValueError(f'Generator "{name}" already registered.')

    _GENERATOR_REGISTRY[name.lower()] = ctor


def get_random_generator(
    probability_distribution: str,
    *args,
    **kwargs,
) -> RandomGenerator:
    """
    Returns a random number generator based on the specified
    probability distribution.

    Args:
        probability_distribution (str): Name of the probability
            distribution (case-insensitive).
        *args: Positional arguments for the generator constructor.
        **kwargs: Keyword arguments for the generator constructor.
    Returns:
        RandomGenerator: An instance of the specified random generator.
    """
    try:
        ctor = _GENERATOR_REGISTRY[probability_distribution.lower()]
    except KeyError as exc:
        available = ", ".join(sorted(_GENERATOR_REGISTRY))
        raise ValueError(
            f'Distribution "{probability_distribution}" not supported. '
            f"Available: {available}."
        ) from exc

    return ctor(*args, **kwargs)
