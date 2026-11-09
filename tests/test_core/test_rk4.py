import math

import numpy as np
import pytest
import scipy.linalg

import machwave.core.solvers.rk4 as rk4

DECAY_RATE = 1.0e4


def exponential_decay(quantity):
    return (-DECAY_RATE * quantity,)


def test_step_returns_one_value_per_variable():
    def rotation(x, y):
        return (-y, x)

    assert len(rk4.rk4th_step({"x": 1.0, "y": 0.0}, rotation, 0.1)) == 2


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


def test_solver_takes_a_single_step_when_it_is_stable():
    d_t = 1.0e-4

    solved, substep_count = rk4.rk4th_ode_solver(
        {"quantity": 1.0}, exponential_decay, d_t
    )

    assert substep_count == 1
    assert solved == rk4.rk4th_step({"quantity": 1.0}, exponential_decay, d_t)[0]


def test_solver_stays_stable_past_the_single_step_limit():
    d_t = 10 / DECAY_RATE

    single_step = rk4.rk4th_step({"quantity": 1.0}, exponential_decay, d_t)[0]
    solved, substep_count = rk4.rk4th_ode_solver(
        {"quantity": 1.0}, exponential_decay, d_t
    )

    assert abs(single_step) > 1.0
    assert substep_count == 10
    assert 0.0 < solved < 1.0


# eigenvalues -1 +/- 2i and -3: a decaying rotation driving a third component
LINEAR_SYSTEM = np.array(
    [
        [-1.0, 2.0, 0.0],
        [-2.0, -1.0, 0.0],
        [1.0, 0.0, -3.0],
    ]
)
LINEAR_SYSTEM_START = np.array([1.0, 0.0, 0.5])


def linear_system(value):
    return LINEAR_SYSTEM @ value


def linear_system_error(step_count, final_time=1.0):
    exact = scipy.linalg.expm(LINEAR_SYSTEM * final_time) @ LINEAR_SYSTEM_START
    value = LINEAR_SYSTEM_START
    for _ in range(step_count):
        value = rk4.rk4th_vector_ode_solver(
            value, linear_system, final_time / step_count
        )
    return np.linalg.norm(value - exact)


def test_vector_solver_converges_at_fourth_order_on_a_linear_system():
    errors = [linear_system_error(step_count) for step_count in (10, 20, 40, 80)]

    observed_orders = np.log2(np.array(errors[:-1]) / np.array(errors[1:]))

    np.testing.assert_allclose(observed_orders, 4.0, atol=0.1)


def test_vector_solver_substeps_match_the_same_steps_taken_one_by_one():
    d_t = 0.2
    substepped = rk4.rk4th_vector_ode_solver(
        LINEAR_SYSTEM_START, linear_system, d_t, step_count=4
    )

    stepwise = LINEAR_SYSTEM_START
    for _ in range(4):
        stepwise = rk4.rk4th_vector_ode_solver(stepwise, linear_system, d_t / 4)

    np.testing.assert_allclose(substepped, stepwise, rtol=1e-15)


def test_vector_solver_uses_a_given_initial_derivative_as_its_first_stage():
    calls = []

    def counted(value):
        calls.append(value)
        return linear_system(value)

    rk4.rk4th_vector_ode_solver(
        LINEAR_SYSTEM_START,
        counted,
        0.1,
        step_count=2,
        initial_derivative=linear_system(LINEAR_SYSTEM_START),
    )

    assert len(calls) == 2 * 4 - 1


def test_vector_solver_matches_the_scalar_solver():
    d_t = 0.5e-4

    vector = rk4.rk4th_vector_ode_solver(
        np.array([1.0]), lambda value: np.array(exponential_decay(value[0])), d_t
    )

    assert vector[0] == pytest.approx(
        rk4.rk4th_step({"quantity": 1.0}, exponential_decay, d_t)[0], rel=1e-15
    )


def test_vector_solver_rejects_fewer_than_one_step():
    with pytest.raises(ValueError, match="step_count"):
        rk4.rk4th_vector_ode_solver(LINEAR_SYSTEM_START, linear_system, 0.1, 0)


def test_solver_is_fourth_order_on_exponential_decay():
    horizon = 10 / DECAY_RATE
    expected = math.exp(-DECAY_RATE * horizon)
    errors = []
    for step_count in (40, 80, 160, 320):
        quantity = 1.0
        for _ in range(step_count):
            quantity, _ = rk4.rk4th_ode_solver(
                {"quantity": quantity}, exponential_decay, horizon / step_count
            )
        errors.append(abs(quantity - expected))

    observed_orders = np.log2(np.array(errors[:-1]) / np.array(errors[1:]))

    # measured 4.15, 4.08 and 4.04
    np.testing.assert_allclose(observed_orders, 4.0, atol=0.2)
