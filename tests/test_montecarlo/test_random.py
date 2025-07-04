import numpy as np
import pytest

from machwave.montecarlo.random import (
    NormalRandomGenerator,
    UniformRandomGenerator,
    get_random_generator,
    register_random_generator,
)


@pytest.mark.parametrize(
    "value, spread, rng_seed, nsamples",
    [
        (100.0, 9.0, 0, 50_000),  # sigma = 3.0
    ],
)
def test_normal_generator_bounds(
    value: float, spread: float, rng_seed: int, nsamples: int
) -> None:
    """
    Validate `NormalRandomGenerator` samples.

    The test draws *nsamples* values from a ``NormalRandomGenerator`` seeded
    with ``rng_seed`` and checks:

    * The empirical mean is within ±2 % (or ±0.02 absolute if the mean is
      ~0) of the nominal ``value``.
    * At least 99 % of samples lie inside the interval
      ``value ± spread``.  Because ``spread`` is defined as *three* standard
      deviations (3 sigma), the theoretical fraction inside that interval is
      99.7 %, so 99 % is a safe lower bound.

    Args:
        value (float): Centre value of the normal distribution.
        spread (float): Total width of the distribution, defined as 3 times
            the standard deviation (sigma).
        rng_seed (int): Seed for reproducibility.
        nsamples (int): Number of random draws to perform.
    """
    gen = NormalRandomGenerator(value=value, spread=spread)
    np.random.seed(rng_seed)
    samples = np.array([gen.get_value() for _ in range(nsamples)])

    tol = dict(abs=0.02) if abs(value) < 1e-9 else dict(rel=2e-2)
    assert samples.mean() == pytest.approx(value, **tol)

    low, high = value - spread, value + spread
    inside = np.logical_and(samples >= low, samples <= high)
    assert inside.mean() > 0.99


@pytest.mark.parametrize(
    "value, spread, rng_seed, nsamples",
    [
        (0.0, 4.0, 1, 20_000),  # U(-2, 2)
        (10.0, (8.0, 18.0), 2, 20_000),  # U(8, 18)
    ],
)
def test_uniform_generator_bounds(
    value: float, spread: float | tuple[float, float], rng_seed: int, nsamples: int
) -> None:
    """
    Validate `UniformRandomGenerator` samples.

    The test constructs a uniform generator, draws samples and confirms that

    * **Support bounds**: every sample lies in the closed interval predicted
      by *spread* (either explicit tuple or ``value ± spread / 2``).
    * **Empirical mean** is within ±2 % of the theoretical midpoint (or ±0.02
      absolute if that midpoint is ≈ 0).

    Args:
        value (float): Centre value used only when *spread* is scalar.
        spread (float | tuple[float, float]): Either a scalar width
            (symmetric) or explicit ``(low, high)``.
        rng_seed (int): Seed for reproducibility.
        nsamples (int): Number of random draws.
    """
    gen = UniformRandomGenerator(value=value, spread=spread)
    np.random.seed(rng_seed)
    samples = np.array([gen.get_value() for _ in range(nsamples)])

    low, high = (
        spread
        if isinstance(spread, tuple)
        else (value - spread / 2, value + spread / 2)
    )

    assert samples.min() >= low
    assert samples.max() <= high

    expected_mean = (low + high) / 2
    tol = dict(abs=0.02) if abs(expected_mean) < 1e-9 else dict(rel=2e-2)
    assert samples.mean() == pytest.approx(expected_mean, **tol)


@pytest.mark.parametrize("cls", [NormalRandomGenerator, UniformRandomGenerator])
def test_negative_scalar_spread_raises(cls):
    with pytest.raises(ValueError):
        cls(value=0.0, spread=-1.0)


def test_normal_tuple_spread_raises():
    with pytest.raises(ValueError):
        NormalRandomGenerator(value=0.0, spread=(1.0, 1.0))


@pytest.mark.parametrize("bad_tuple", [(5.0, 5.0), (7.0, 3.0)])
def test_uniform_invalid_tuple_bounds_raises(bad_tuple):
    gen = UniformRandomGenerator(value=0.0, spread=bad_tuple)
    with pytest.raises(ValueError):
        gen.get_value()


def test_get_random_generator_returns_correct_instance():
    gen = get_random_generator("normal", value=1.0, spread=3.0)
    assert isinstance(gen, NormalRandomGenerator)


def test_register_random_generator_and_duplicate_guard():
    class Dummy(NormalRandomGenerator):  # piggy-back on NormalRandomGenerator
        pass

    register_random_generator("dummy", Dummy)
    assert isinstance(get_random_generator("dummy", value=0.0, spread=0.0), Dummy)

    # second registration of the same name should raise
    with pytest.raises(ValueError):
        register_random_generator("dummy", Dummy)


def test_get_random_generator_unknown_distribution():
    with pytest.raises(ValueError):
        get_random_generator("does-not-exist", value=0.0, spread=0.0)
