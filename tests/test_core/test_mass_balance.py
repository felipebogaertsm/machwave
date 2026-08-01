import numpy as np
import pytest

import machwave.core.mass_balance as mass_balance
import machwave.core.solvers.rk4 as rk4


BASE_KWARGS = {
    "external_pressure": 101_325.0,
    "free_chamber_volume": 1.0e-3,
    "throat_area": 1.0e-4,
    "k": 1.18,
    "R": 320.0,
    "flame_temperature": 2_800.0,
    "nozzle_discharge_coefficient": 0.95,
}


def constant(value):
    """Wrap a scalar as a chamber-pressure-independent callable."""
    return lambda _chamber_pressure: value


@pytest.mark.parametrize(
    "chamber_pressure, mass_flow_in",
    [
        (5.0e6, 0.5),  # choked
        (
            1.5e5,
            0.05,
        ),  # sub-critical: external_pressure/chamber_pressure above critical
    ],
)
def test_zero_volume_rate_matches_rigid_form(chamber_pressure, mass_flow_in):
    """With V_dot = 0 (default), output must equal the rigid-volume form."""
    explicit = mass_balance.compute_chamber_pressure_mass_balance(
        chamber_pressure=chamber_pressure,
        mass_flow_in=constant(mass_flow_in),
        free_chamber_volume_rate=constant(0.0),
        **BASE_KWARGS,
    )
    default = mass_balance.compute_chamber_pressure_mass_balance(
        chamber_pressure=chamber_pressure,
        mass_flow_in=constant(mass_flow_in),
        **BASE_KWARGS,
    )
    assert explicit == default


def test_balanced_mass_flow_isolates_volume_term():
    """With m_dot_in = m_dot_out, dP/dt collapses to -P V_dot / V exactly."""
    chamber_pressure = 4.0e6
    (baseline,) = mass_balance.compute_chamber_pressure_mass_balance(
        chamber_pressure=chamber_pressure,
        mass_flow_in=constant(0.0),
        **BASE_KWARGS,
    )
    mass_flow_out = (
        -baseline
        * BASE_KWARGS["free_chamber_volume"]
        / (BASE_KWARGS["R"] * BASE_KWARGS["flame_temperature"])
    )

    free_chamber_volume_rate = 2.5e-5
    (derivative,) = mass_balance.compute_chamber_pressure_mass_balance(
        chamber_pressure=chamber_pressure,
        mass_flow_in=constant(mass_flow_out),
        free_chamber_volume_rate=constant(free_chamber_volume_rate),
        **BASE_KWARGS,
    )

    expected = (
        -chamber_pressure
        * free_chamber_volume_rate
        / BASE_KWARGS["free_chamber_volume"]
    )
    assert derivative == pytest.approx(expected, rel=1e-12, abs=1e-12)


@pytest.mark.parametrize(
    "chamber_pressure, mass_flow_in, free_chamber_volume_rate",
    [
        (5.0e6, 0.5, 2.5e-5),
        (5.0e6, 0.5, -1.0e-5),
        (1.5e5, 0.05, 1.0e-6),
    ],
)
def test_volume_term_is_linear_addition(
    chamber_pressure, mass_flow_in, free_chamber_volume_rate
):
    """dP/dt(V_dot) = dP/dt(0) + (-P V_dot / V) to machine precision."""
    (baseline,) = mass_balance.compute_chamber_pressure_mass_balance(
        chamber_pressure=chamber_pressure,
        mass_flow_in=constant(mass_flow_in),
        **BASE_KWARGS,
    )
    (with_rate,) = mass_balance.compute_chamber_pressure_mass_balance(
        chamber_pressure=chamber_pressure,
        mass_flow_in=constant(mass_flow_in),
        free_chamber_volume_rate=constant(free_chamber_volume_rate),
        **BASE_KWARGS,
    )
    expected = (
        baseline
        - chamber_pressure
        * free_chamber_volume_rate
        / BASE_KWARGS["free_chamber_volume"]
    )
    assert with_rate == pytest.approx(expected, rel=1e-12, abs=1e-12)


def test_inflow_callable_is_evaluated_at_each_rk4_stage_pressure():
    """RK4 evaluates the inflow at the staged pressure, not a frozen value."""
    seen_pressures = []

    def mass_flow_in(chamber_pressure):
        seen_pressures.append(chamber_pressure)
        return 0.5

    rk4.rk4th_ode_solver(
        variables={"chamber_pressure": 5.0e6},
        equation=mass_balance.compute_chamber_pressure_mass_balance,
        d_t=0.05,
        mass_flow_in=mass_flow_in,
        **BASE_KWARGS,
    )

    assert len(seen_pressures) == 4
    assert len(set(seen_pressures)) > 1


# Lumped solid chamber for the staged-inflow convergence test: choked outflow
# plus a Saint Robert inflow r = a * Pc^n, so the inflow depends on pressure.
STAGED_CHAMBER_KWARGS = {
    "external_pressure": 101_325.0,
    "free_chamber_volume": 9.0e-4,
    "throat_area": 7.7e-5,
    "k": 1.2,
    "R": 320.0,
    "flame_temperature": 2_800.0,
    "nozzle_discharge_coefficient": 0.95,
}
BURN_RATE_COEFFICIENT = 1.2e-4
BURN_RATE_EXPONENT = 0.5


def saint_robert_inflow(chamber_pressure):
    return BURN_RATE_COEFFICIENT * chamber_pressure**BURN_RATE_EXPONENT


def integrate_chamber_pressure(*, staged, d_t, step_count, initial_pressure):
    """Integrate the lumped chamber ODE; freeze or stage the inflow per step."""
    pressures = [initial_pressure]
    for _ in range(step_count):
        chamber_pressure = pressures[-1]
        if staged:
            mass_flow_in = saint_robert_inflow
        else:
            mass_flow_in = constant(saint_robert_inflow(chamber_pressure))
        result = rk4.rk4th_ode_solver(
            variables={"chamber_pressure": chamber_pressure},
            equation=mass_balance.compute_chamber_pressure_mass_balance,
            d_t=d_t,
            mass_flow_in=mass_flow_in,
            **STAGED_CHAMBER_KWARGS,
        )
        pressures.append(result[0])
    return np.array(pressures)


def test_staged_inflow_tracks_refined_reference_better_than_freezing():
    """Staging the pressure-dependent inflow restores high-order accuracy.

    Freezing the inflow across the four RK4 stages drops the integrator to
    first order, so a coarse step lags a refined reference. Evaluating the
    inflow at each stage pressure keeps the same coarse step close to it.
    """
    initial_pressure = 2.0e6
    end_time = 0.15
    fine_d_t = 1.0e-4
    coarse_d_t = 1.0e-2
    stride = round(coarse_d_t / fine_d_t)

    reference = integrate_chamber_pressure(
        staged=True,
        d_t=fine_d_t,
        step_count=round(end_time / fine_d_t),
        initial_pressure=initial_pressure,
    )[::stride]
    staged = integrate_chamber_pressure(
        staged=True,
        d_t=coarse_d_t,
        step_count=round(end_time / coarse_d_t),
        initial_pressure=initial_pressure,
    )
    frozen = integrate_chamber_pressure(
        staged=False,
        d_t=coarse_d_t,
        step_count=round(end_time / coarse_d_t),
        initial_pressure=initial_pressure,
    )

    staged_error = np.max(np.abs(staged - reference))
    frozen_error = np.max(np.abs(frozen - reference))

    assert np.all(staged > 0.0)
    assert staged_error < 0.2 * frozen_error


class TestChamberBelowAmbient:
    """A chamber that falls to ambient stops driving the nozzle.

    The sub-critical branch takes the square root of one minus a power of the
    pressure ratio, which turns negative once the chamber drops below ambient.
    A blowdown reaches that on the way out, and the derivative has to stay a
    number for the integrator to land there.
    """

    @pytest.mark.parametrize(
        "chamber_pressure",
        [BASE_KWARGS["external_pressure"], 5.0e4, 1.0e3],
    )
    def test_derivative_stays_finite(self, chamber_pressure):
        (derivative,) = mass_balance.compute_chamber_pressure_mass_balance(
            chamber_pressure=chamber_pressure,
            mass_flow_in=constant(0.0),
            **BASE_KWARGS,
        )

        assert np.isfinite(derivative)

    def test_no_inflow_leaves_the_pressure_alone(self):
        (derivative,) = mass_balance.compute_chamber_pressure_mass_balance(
            chamber_pressure=BASE_KWARGS["external_pressure"],
            mass_flow_in=constant(0.0),
            **BASE_KWARGS,
        )

        assert derivative == pytest.approx(0.0)

    def test_inflow_still_raises_the_pressure(self):
        (derivative,) = mass_balance.compute_chamber_pressure_mass_balance(
            chamber_pressure=5.0e4,
            mass_flow_in=constant(0.01),
            **BASE_KWARGS,
        )

        assert derivative > 0.0
