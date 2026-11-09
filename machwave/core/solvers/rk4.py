import math
from typing import Any, Callable

import numpy as np
import numpy.typing as npt


def rk4th_step(
    variables: dict[str, float],
    equation: Callable,
    d_t: float,
    **kwargs: Any,
) -> tuple[float, ...]:
    """
    Advance a system of ODEs by one step using the 4th-order Runge-Kutta method.

    Args:
        variables: Mapping of variable name to current value.
        equation: Callable returning the derivatives of the variables.
        d_t: Time step [s].
        **kwargs: Additional keyword arguments forwarded to `equation`. These
            are held constant across all four stages, while `variables` are
            advanced; a term that depends on a `variables` entry must be
            computed inside `equation` (or passed as a callable it resolves)
            so it stays consistent across the stages.

    Returns:
        New values of the variables, in the order of `variables`.
    """
    k_1 = equation(**variables, **kwargs)
    k_2 = equation(
        **{
            key: value + 0.5 * k_1[index] * d_t
            for index, (key, value) in enumerate(variables.items())
        },
        **kwargs,
    )
    k_3 = equation(
        **{
            key: value + 0.5 * k_2[index] * d_t
            for index, (key, value) in enumerate(variables.items())
        },
        **kwargs,
    )
    k_4 = equation(
        **{
            key: value + k_3[index] * d_t
            for index, (key, value) in enumerate(variables.items())
        },
        **kwargs,
    )

    return tuple(
        value
        + (1 / 6) * (k_1[index] + 2 * (k_2[index] + k_3[index]) + k_4[index]) * d_t
        for index, value in enumerate(variables.values())
    )


# RK4 is stable up to about 2.8, but past about 1.3 its last stage overshoots the
# equilibrium, and near the limit the chamber settles on a spurious steady state
MAX_DECAY_RATE_STEP_PRODUCT = 1.0

# about the square root of machine epsilon, to balance truncation and round-off error
RELATIVE_DERIVATIVE_PERTURBATION = 1e-6
MIN_DERIVATIVE_PERTURBATION_SCALE = 1.0  # keeps the perturbation finite near zero


def get_substep_count(
    variables: dict[str, float],
    equation: Callable,
    d_t: float,
    **kwargs: Any,
) -> int:
    """
    Return how many equal RK4 substeps keep a scalar ODE stable over `d_t`.

    The decay rate is minus the derivative of the right-hand side with respect to
    the variable, taken by central difference at its current value. Each step is
    kept within one decay time.

    Args:
        variables: Mapping of the single variable name to its current value.
        equation: Callable returning the derivative of the variable.
        d_t: Time step [s].
        **kwargs: Additional keyword arguments forwarded to `equation`.

    Returns:
        Number of substeps, at least one.

    Raises:
        ValueError: If `variables` does not hold exactly one variable.
    """
    if len(variables) != 1:
        raise ValueError(f"expected a single variable, got {len(variables)}")

    ((state_name, state),) = variables.items()
    perturbation = RELATIVE_DERIVATIVE_PERTURBATION * max(
        abs(state), MIN_DERIVATIVE_PERTURBATION_SCALE
    )
    decay_rate = -(
        equation(**{state_name: state + perturbation}, **kwargs)[0]
        - equation(**{state_name: state - perturbation}, **kwargs)[0]
    ) / (2 * perturbation)

    return max(1, math.ceil(decay_rate * d_t / MAX_DECAY_RATE_STEP_PRODUCT))


def rk4th_ode_solver(
    variables: dict[str, float],
    equation: Callable,
    d_t: float,
    **kwargs: Any,
) -> tuple[float, int]:
    """
    Advance a scalar ODE over `d_t` in as many equal RK4 substeps as stability needs.

    Args:
        variables: Mapping of the single variable name to its current value.
        equation: Callable returning the derivative of the variable.
        d_t: Time step [s].
        **kwargs: Additional keyword arguments forwarded to `equation`.

    Returns:
        New value of the variable and the number of substeps taken.
    """
    substep_count = get_substep_count(variables, equation, d_t, **kwargs)
    ((state_name, state),) = variables.items()

    for _ in range(substep_count):
        state = rk4th_step(
            {state_name: state}, equation, d_t / substep_count, **kwargs
        )[0]

    return state, substep_count


def rk4th_vector_ode_solver(
    state: npt.NDArray[np.float64],
    equation: Callable[[npt.NDArray[np.float64]], npt.NDArray[np.float64]],
    d_t: float,
    step_count: int = 1,
    initial_derivative: npt.NDArray[np.float64] | None = None,
) -> npt.NDArray[np.float64]:
    """
    Advance an autonomous system y' = f(y) over `d_t` in equal classical RK4 steps.

    Every component goes through every stage, so a right-hand side that couples them
    keeps fourth order (Hairer, Norsett and Wanner 1993, Section II.1).

    Args:
        state: Current state vector.
        equation: Callable returning dy/dt at a state, with the shape of the
            state.
        d_t: Time step [s].
        step_count: Number of equal RK4 steps to take over `d_t` (>=1).
        initial_derivative: f at `state`, when the caller has evaluated it
            already. It is the first stage of the first step, so passing it
            saves one evaluation of `equation`.

    Returns:
        The state after `d_t`.

    Raises:
        ValueError: If `step_count` is less than one.
    """
    if step_count < 1:
        raise ValueError(f"step_count must be at least 1, got {step_count}")

    step = d_t / step_count
    value = np.asarray(state, dtype=np.float64)
    for index in range(step_count):
        k_1 = (
            np.asarray(initial_derivative, dtype=np.float64)
            if index == 0 and initial_derivative is not None
            else equation(value)
        )
        k_2 = equation(value + 0.5 * step * k_1)
        k_3 = equation(value + 0.5 * step * k_2)
        k_4 = equation(value + step * k_3)
        value = value + (step / 6.0) * (k_1 + 2.0 * (k_2 + k_3) + k_4)

    return value
