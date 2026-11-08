import math
from typing import Any, Callable


def rk4th_ode_solver(
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
        Tuple containing the new values of the variables followed by the
        averaged auxiliary term; length equals `len(variables) + 1`.
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

    derivatives = (
        variables[key]
        + (1 / 6) * (k_1[index] + 2 * (k_2[index] + k_3[index]) + k_4[index]) * d_t
        for index, key in enumerate(variables.keys())
    )

    return (
        *derivatives,
        (1 / 6) * (k_1[-1] + 2 * (k_2[-1] + k_3[-1]) + k_4[-1]),
    )


# |lambda * d_t| per step. RK4 stays stable up to about 2.785, but past 1 its stages
# overshoot a decaying variable through zero, and near the stability limit the
# nonlinear chamber balance settles on spurious steady states.
MAX_STIFFNESS_STEP_PRODUCT = 1.0

# Central-difference step relative to the variable, near the square root of machine
# epsilon so truncation and round-off errors are balanced; the scale floor keeps the
# step finite when the variable is near zero.
RELATIVE_STIFFNESS_PERTURBATION = 1e-6
MIN_STIFFNESS_PERTURBATION_SCALE = 1.0


def get_stable_step_count(
    variables: dict[str, float],
    equation: Callable,
    d_t: float,
    **kwargs: Any,
) -> int:
    """
    Return how many equal RK4 steps keep a scalar ODE stable over `d_t`.

    The stiffness is the derivative of the right-hand side with respect to the
    variable, taken by central difference at its current value.

    Args:
        variables: Mapping of the single variable name to its current value.
        equation: Callable returning the derivative of the variable.
        d_t: Time step [s].
        **kwargs: Additional keyword arguments forwarded to `equation`.

    Returns:
        Number of steps, at least one.

    Raises:
        ValueError: If `variables` does not hold exactly one variable.
    """
    if len(variables) != 1:
        raise ValueError(f"expected a single variable, got {len(variables)}")

    ((state_name, state),) = variables.items()
    perturbation = RELATIVE_STIFFNESS_PERTURBATION * max(
        abs(state), MIN_STIFFNESS_PERTURBATION_SCALE
    )
    stiffness = (
        equation(**{state_name: state + perturbation}, **kwargs)[0]
        - equation(**{state_name: state - perturbation}, **kwargs)[0]
    ) / (2 * perturbation)

    return max(1, math.ceil(-stiffness * d_t / MAX_STIFFNESS_STEP_PRODUCT))


def rk4th_substepped_ode_solver(
    variables: dict[str, float],
    equation: Callable,
    d_t: float,
    **kwargs: Any,
) -> float:
    """
    Advance a scalar ODE over `d_t` in as many equal RK4 steps as its stiffness needs.

    Args:
        variables: Mapping of the single variable name to its current value.
        equation: Callable returning the derivative of the variable.
        d_t: Time step [s].
        **kwargs: Additional keyword arguments forwarded to `equation`.

    Returns:
        New value of the variable.
    """
    step_count = get_stable_step_count(variables, equation, d_t, **kwargs)
    ((state_name, state),) = variables.items()

    for _ in range(step_count):
        state = rk4th_ode_solver(
            {state_name: state}, equation, d_t / step_count, **kwargs
        )[0]

    return state
