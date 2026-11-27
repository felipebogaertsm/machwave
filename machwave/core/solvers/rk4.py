import math
from typing import Any, Callable

# past about 1.3 the last stage overshoots equilibrium, well before the limit of 2.785
_MAX_DECAY_TIMES_PER_STEP = 1.0

# near the square root of machine epsilon, balancing truncation and round-off error
_RELATIVE_FINITE_DIFFERENCE_STEP = 1e-6
_MIN_FINITE_DIFFERENCE_SCALE = 1.0


def step_ode_system(
    initial_values: dict[str, float],
    compute_derivatives: Callable,
    time_step: float,
    **constant_arguments: Any,
) -> tuple[float, ...]:
    """
    Advance a system of ODEs by one step using the 4th-order Runge-Kutta method.

    Args:
        initial_values: Mapping of variable name to its value at the start of the step.
        compute_derivatives: Callable returning the derivatives of the variables.
        time_step: Time step [s].
        **constant_arguments: Additional keyword arguments forwarded to
            `compute_derivatives`. These are held constant across all four stages,
            while `initial_values` are advanced; a term that depends on a variable
            must be computed inside `compute_derivatives` (or passed as a callable it
            resolves) so it stays consistent across the stages.

    Returns:
        New values of the variables, in the order of `initial_values`.
    """
    stage_1_derivatives = compute_derivatives(**initial_values, **constant_arguments)
    stage_2_derivatives = compute_derivatives(
        **{
            name: value + 0.5 * stage_1_derivatives[index] * time_step
            for index, (name, value) in enumerate(initial_values.items())
        },
        **constant_arguments,
    )
    stage_3_derivatives = compute_derivatives(
        **{
            name: value + 0.5 * stage_2_derivatives[index] * time_step
            for index, (name, value) in enumerate(initial_values.items())
        },
        **constant_arguments,
    )
    stage_4_derivatives = compute_derivatives(
        **{
            name: value + stage_3_derivatives[index] * time_step
            for index, (name, value) in enumerate(initial_values.items())
        },
        **constant_arguments,
    )

    return tuple(
        value
        + (1 / 6)
        * (
            stage_1_derivatives[index]
            + 2 * (stage_2_derivatives[index] + stage_3_derivatives[index])
            + stage_4_derivatives[index]
        )
        * time_step
        for index, value in enumerate(initial_values.values())
    )


def get_stable_step_count(
    variable_name: str,
    initial_value: float,
    compute_derivatives: Callable,
    interval: float,
    **constant_arguments: Any,
) -> int:
    """
    Return how many equal Runge-Kutta steps keep a scalar ODE stable over `interval`.

    Each step spans at most one decay time, taken by central difference at
    `initial_value`. A growing solution takes a single step.

    Args:
        variable_name: Keyword under which `compute_derivatives` takes the variable.
        initial_value: Value of the variable at the start of the interval.
        compute_derivatives: Callable returning the derivative of the variable.
        interval: Time interval to integrate over [s].
        **constant_arguments: Additional keyword arguments forwarded to
            `compute_derivatives`.

    Returns:
        Number of steps, at least one.
    """
    finite_difference_step = _RELATIVE_FINITE_DIFFERENCE_STEP * max(
        abs(initial_value), _MIN_FINITE_DIFFERENCE_SCALE
    )
    decay_rate = -(
        compute_derivatives(
            **{variable_name: initial_value + finite_difference_step},
            **constant_arguments,
        )[0]
        - compute_derivatives(
            **{variable_name: initial_value - finite_difference_step},
            **constant_arguments,
        )[0]
    ) / (2 * finite_difference_step)

    return max(1, math.ceil(decay_rate * interval / _MAX_DECAY_TIMES_PER_STEP))


def integrate_scalar_ode(
    variable_name: str,
    initial_value: float,
    compute_derivatives: Callable,
    interval: float,
    **constant_arguments: Any,
) -> tuple[float, int]:
    """
    Integrate a scalar ODE over `interval` in as many Runge-Kutta steps as it needs.

    Args:
        variable_name: Keyword under which `compute_derivatives` takes the variable.
        initial_value: Value of the variable at the start of the interval.
        compute_derivatives: Callable returning the derivative of the variable.
        interval: Time interval to integrate over [s].
        **constant_arguments: Additional keyword arguments forwarded to
            `compute_derivatives`.

    Returns:
        Value of the variable at the end of the interval and the number of steps
        taken.
    """
    step_count = get_stable_step_count(
        variable_name,
        initial_value,
        compute_derivatives,
        interval,
        **constant_arguments,
    )
    value = initial_value

    for _ in range(step_count):
        value = step_ode_system(
            {variable_name: value},
            compute_derivatives,
            interval / step_count,
            **constant_arguments,
        )[0]

    return value, step_count
