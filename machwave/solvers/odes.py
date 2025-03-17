from typing import Callable


def rk4th_ode_solver(
    variables: dict[str, float],
    equation: Callable,
    d_t: float,
    **kwargs,
) -> tuple[float, ...]:
    """
    Solves a system of ordinary differential equations using the 4th order
    Runge-Kutta method.

    Args:
        variables (dict[str, float]): A dictionary containing the variables to
            be solved.
        equation (Callable): A function that returns the derivatives of the
            variables.
        d_t (float): The time step.
        **kwargs: Additional keyword arguments to be passed to the equation
            function.

    Returns:
        tuple[float]: A tuple containing the new values of the variables. The
        length of the tuple is equal to the number of variables + 1.

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
