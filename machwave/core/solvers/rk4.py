import math
from typing import Any, Callable

# a step longer than the chamber time constant can drive the chamber pressure negative
_MAX_TIME_CONSTANTS_PER_STEP = 1.0
# the chamber time constant is measured by perturbing the pressure by this fraction
_RELATIVE_FINITE_DIFFERENCE_STEP = 1e-6
# perturb as if the pressure were at least 1 Pa
_MIN_FINITE_DIFFERENCE_SCALE = 1.0


def step_ode_system(
    initial_values: dict[str, float],
    compute_derivatives: Callable,
    time_step: float,
    **constant_arguments: Any,
) -> tuple[float, ...]:
    """
    Advance a system of ODEs by one classical fourth-order Runge-Kutta step.

    Args:
        initial_values: Mapping of variable name to its value at the start of the step.
        compute_derivatives: Callable taking the variables and `constant_arguments`
            as keywords and returning the time derivatives of the variables, in the
            order of `initial_values`.
        time_step: Step size [s].
        **constant_arguments: Keyword arguments passed unchanged to
            `compute_derivatives` at all four stages. A term that depends on a
            variable must be evaluated inside `compute_derivatives`, or passed as a
            callable it evaluates, so that it follows the stage values.

    Returns:
        Values of the variables at the end of the step, in the order of
        `initial_values`.
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
    Return the number of equal Runge-Kutta steps to split `interval` into.

    Each step is at most one time constant of the variable, measured at
    `initial_value`. For the chamber pressure it is close to the chamber residence
    time. A longer step can drive the chamber pressure negative. A variable that is
    not settling toward equilibrium takes a single step.

    Args:
        variable_name: Keyword under which `compute_derivatives` takes the variable.
        initial_value: Value of the variable at the start of the interval.
        compute_derivatives: Callable returning a tuple whose first item is the time
            derivative of the variable.
        interval: Time interval to integrate over [s].
        **constant_arguments: Keyword arguments passed unchanged to
            `compute_derivatives`.

    Returns:
        Number of steps, at least one.

    References:
        Dahlquist, G., "A Special Stability Problem for Linear Multistep Methods",
        BIT 3, 1963, pp. 27-43.
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

    return max(1, math.ceil(decay_rate * interval / _MAX_TIME_CONSTANTS_PER_STEP))


def integrate_scalar_ode(
    variable_name: str,
    initial_value: float,
    compute_derivatives: Callable,
    interval: float,
    **constant_arguments: Any,
) -> tuple[float, int]:
    """
    Integrate a scalar ODE over `interval` in equal Runge-Kutta substeps.

    The number of substeps comes from `get_stable_step_count`.

    Args:
        variable_name: Keyword under which `compute_derivatives` takes the variable.
        initial_value: Value of the variable at the start of the interval.
        compute_derivatives: Callable returning a tuple whose first item is the time
            derivative of the variable.
        interval: Time interval to integrate over [s].
        **constant_arguments: Keyword arguments passed unchanged to
            `compute_derivatives` at every stage of every substep.

    Returns:
        Value of the variable at the end of the interval and the number of substeps
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
