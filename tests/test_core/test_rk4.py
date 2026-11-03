import pytest

import machwave.core.solvers.rk4 as rk4

DECAY_RATE = 1.0e4


def exponential_decay(value):
    return (-DECAY_RATE * value,)


@pytest.mark.parametrize(
    "d_t, expected_step_count",
    [(0.5e-4, 1), (4.5e-4, 5), (1.025e-2, 103)],
)
def test_step_count_keeps_each_step_within_the_stiffness_bound(
    d_t, expected_step_count
):
    step_count = rk4.get_stable_step_count({"value": 1.0}, exponential_decay, d_t)

    assert step_count == expected_step_count


def test_growing_solution_takes_a_single_step():
    def exponential_growth(value):
        return (DECAY_RATE * value,)

    assert rk4.get_stable_step_count({"value": 1.0}, exponential_growth, 1.0) == 1


def test_step_count_rejects_more_than_one_variable():
    with pytest.raises(ValueError, match="single variable"):
        rk4.get_stable_step_count({"a": 1.0, "b": 1.0}, lambda a, b: (a, b), 1e-3)


def test_substepped_solver_matches_a_single_step_when_the_step_is_stable():
    d_t = 1.0e-4

    substepped = rk4.rk4th_substepped_ode_solver({"value": 1.0}, exponential_decay, d_t)

    assert substepped == rk4.rk4th_ode_solver({"value": 1.0}, exponential_decay, d_t)[0]


def test_substepped_solver_stays_stable_past_the_rk4_limit():
    d_t = 10 / DECAY_RATE

    single_step = rk4.rk4th_ode_solver({"value": 1.0}, exponential_decay, d_t)[0]
    substepped = rk4.rk4th_substepped_ode_solver({"value": 1.0}, exponential_decay, d_t)

    assert abs(single_step) > 1.0
    assert 0.0 < substepped < 1.0
