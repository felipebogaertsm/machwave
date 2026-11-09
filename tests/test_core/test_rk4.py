import math

import numpy as np
import pytest

import machwave.core.solvers.rk4 as rk4

DECAY_RATE = 1.0e4


def exponential_decay(quantity):
    return (-DECAY_RATE * quantity,)


@pytest.mark.parametrize(
    "d_t, expected_substep_count",
    [(0.5e-4, 1), (4.5e-4, 5), (1.025e-2, 103)],
)
def test_substep_count_keeps_each_substep_within_one_decay_time(
    d_t, expected_substep_count
):
    substep_count = rk4.get_substep_count({"quantity": 1.0}, exponential_decay, d_t)

    assert substep_count == expected_substep_count


def test_growing_solution_takes_a_single_step():
    def exponential_growth(quantity):
        return (DECAY_RATE * quantity,)

    assert rk4.get_substep_count({"quantity": 1.0}, exponential_growth, 1.0) == 1


def test_substep_count_rejects_more_than_one_variable():
    with pytest.raises(ValueError, match="single variable"):
        rk4.get_substep_count({"a": 1.0, "b": 1.0}, lambda a, b: (a, b), 1e-3)


def test_substepped_solver_matches_a_single_step_when_the_step_is_stable():
    d_t = 1.0e-4

    substepped, substep_count = rk4.rk4th_substepped_ode_solver(
        {"quantity": 1.0}, exponential_decay, d_t
    )

    assert substep_count == 1
    assert (
        substepped == rk4.rk4th_ode_solver({"quantity": 1.0}, exponential_decay, d_t)[0]
    )


def test_substepped_solver_stays_stable_past_the_rk4_limit():
    d_t = 10 / DECAY_RATE

    single_step = rk4.rk4th_ode_solver({"quantity": 1.0}, exponential_decay, d_t)[0]
    substepped, substep_count = rk4.rk4th_substepped_ode_solver(
        {"quantity": 1.0}, exponential_decay, d_t
    )

    assert abs(single_step) > 1.0
    assert substep_count == 10
    assert 0.0 < substepped < 1.0


def test_substepped_solver_is_fourth_order_on_exponential_decay():
    horizon = 10 / DECAY_RATE
    expected = math.exp(-DECAY_RATE * horizon)
    errors = []
    for step_count in (40, 80, 160, 320):
        quantity = 1.0
        for _ in range(step_count):
            quantity, _ = rk4.rk4th_substepped_ode_solver(
                {"quantity": quantity}, exponential_decay, horizon / step_count
            )
        errors.append(abs(quantity - expected))

    observed_orders = np.log2(np.array(errors[:-1]) / np.array(errors[1:]))

    # measured 4.15, 4.08 and 4.04, approaching 4 as the step halves
    np.testing.assert_allclose(observed_orders, 4.0, atol=0.2)
