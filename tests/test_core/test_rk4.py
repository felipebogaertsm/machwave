import math

import numpy as np
import pytest

import machwave.core.solvers.rk4 as rk4

DECAY_RATE = 1.0e4


def exponential_decay(quantity):
    return (-DECAY_RATE * quantity,)


def test_step_returns_one_value_per_variable():
    def rotation(x, y):
        return (-y, x)

    assert len(rk4.step_ode_system({"x": 1.0, "y": 0.0}, rotation, 0.1)) == 2


@pytest.mark.parametrize(
    "interval, expected_step_count",
    [(0.5e-4, 1), (4.5e-4, 5), (1.025e-2, 103)],
)
def test_stable_step_count_keeps_each_step_within_one_time_constant(
    interval, expected_step_count
):
    step_count = rk4.get_stable_step_count("quantity", 1.0, exponential_decay, interval)

    assert step_count == expected_step_count


def test_growing_solution_takes_a_single_step():
    def exponential_growth(quantity):
        return (DECAY_RATE * quantity,)

    assert rk4.get_stable_step_count("quantity", 1.0, exponential_growth, 1.0) == 1


def test_stable_interval_is_integrated_in_one_step():
    interval = 1.0e-4

    integrated, step_count = rk4.integrate_scalar_ode(
        "quantity", 1.0, exponential_decay, interval
    )

    assert step_count == 1
    assert (
        integrated
        == rk4.step_ode_system({"quantity": 1.0}, exponential_decay, interval)[0]
    )


def test_integration_stays_stable_past_the_single_step_limit():
    interval = 10 / DECAY_RATE

    single_step = rk4.step_ode_system({"quantity": 1.0}, exponential_decay, interval)[0]
    integrated, step_count = rk4.integrate_scalar_ode(
        "quantity", 1.0, exponential_decay, interval
    )

    assert abs(single_step) > 1.0
    assert step_count == 10
    assert 0.0 < integrated < 1.0


def test_integration_is_fourth_order_on_exponential_decay():
    horizon = 10 / DECAY_RATE
    expected = math.exp(-DECAY_RATE * horizon)
    errors = []
    for interval_count in (40, 80, 160, 320):
        quantity = 1.0
        for _ in range(interval_count):
            quantity, _ = rk4.integrate_scalar_ode(
                "quantity", quantity, exponential_decay, horizon / interval_count
            )
        errors.append(abs(quantity - expected))

    observed_orders = np.log2(np.array(errors[:-1]) / np.array(errors[1:]))

    # measured 4.15, 4.08 and 4.04
    np.testing.assert_allclose(observed_orders, 4.0, atol=0.2)
