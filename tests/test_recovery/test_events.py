import numpy as np

from machwave.models.recovery import Recovery
from machwave.models.recovery.events import (
    AltitudeBasedEvent,
    ApogeeBasedEvent,
)
from machwave.models.recovery.parachutes import (
    HemisphericalParachute,
    ToroidalParachute,
)


def test_recovery_initialization():
    recovery = Recovery()
    assert recovery.events == []


def test_recovery_add_event():
    recovery = Recovery()

    event = AltitudeBasedEvent(1000, HemisphericalParachute(2))
    recovery.add_event(event)

    assert len(recovery.events) == 1
    assert recovery.events[0] == event


def test_recovery_get_drag_coefficient_and_area():
    recovery = Recovery()

    event1 = AltitudeBasedEvent(1000, HemisphericalParachute(2))
    event2 = ApogeeBasedEvent(1, ToroidalParachute(4, 1))

    recovery.add_event(event1)
    recovery.add_event(event2)

    height = np.array([1001, 1000, 999, 998])
    time = np.array([0, 1, 2, 3])
    velocity = np.array([-1, -1, -1, -1])
    propellant_mass = 0

    assert event1.is_active(height, time, velocity, propellant_mass)
    assert event2.is_active(height, time, velocity, propellant_mass)

    drag_coefficient, area = recovery.get_drag_coefficient_and_area(
        height, time, velocity, propellant_mass
    )

    assert (
        drag_coefficient
        == event1.parachute.drag_coefficient
        + event2.parachute.drag_coefficient
    )
    assert area == event1.parachute.area + event2.parachute.area
