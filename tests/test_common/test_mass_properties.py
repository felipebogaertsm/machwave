import math

import numpy as np
import pytest

import machwave.common.mass_properties as mass_properties
import machwave.core.mechanics as core_mechanics


def point_mass(mass: float, axial_position: float):
    return mass_properties.AxisymmetricMassProperties(
        mass=mass,
        axial_position=axial_position,
        axial_moment_of_inertia=0.0,
        transverse_moment_of_inertia=0.0,
    )


class TestAxisymmetricMassProperties:
    def test_a_cylinder_takes_the_cylinder_moments_of_inertia(self):
        cylinder = mass_properties.AxisymmetricMassProperties.from_cylinder(
            mass=2.0,
            length=0.3,
            outer_radius=0.05,
            inner_radius=0.02,
            axial_position=0.4,
        )

        axial, transverse = core_mechanics.get_cylinder_moments_of_inertia(
            mass=2.0, length=0.3, outer_radius=0.05, inner_radius=0.02
        )
        assert cylinder.mass == pytest.approx(2.0)
        assert cylinder.axial_position == pytest.approx(0.4)
        assert cylinder.axial_moment_of_inertia == pytest.approx(axial)
        assert cylinder.transverse_moment_of_inertia == pytest.approx(transverse)

    def test_combining_shifts_the_transverse_moment_with_the_parallel_axis_theorem(
        self,
    ):
        combined = mass_properties.AxisymmetricMassProperties.combine(
            (point_mass(1.0, 0.0), point_mass(3.0, 2.0))
        )

        assert combined.mass == pytest.approx(4.0)
        assert combined.axial_position == pytest.approx(1.5)
        assert combined.axial_moment_of_inertia == pytest.approx(0.0)
        assert combined.transverse_moment_of_inertia == pytest.approx(
            1.0 * 1.5**2 + 3.0 * 0.5**2
        )

    def test_combining_adds_the_moments_about_the_shared_axis(self):
        cylinders = [
            mass_properties.AxisymmetricMassProperties.from_cylinder(
                mass=mass, length=0.2, outer_radius=0.05, axial_position=position
            )
            for mass, position in ((1.0, 0.1), (2.0, 0.5))
        ]

        combined = mass_properties.AxisymmetricMassProperties.combine(cylinders)

        assert combined.axial_moment_of_inertia == pytest.approx(
            sum(cylinder.axial_moment_of_inertia for cylinder in cylinders)
        )

    def test_a_massless_body_adds_nothing(self):
        body = point_mass(2.0, 0.7)

        combined = mass_properties.AxisymmetricMassProperties.combine(
            (body, point_mass(0.0, math.nan))
        )

        assert combined == body

    def test_bodies_without_mass_have_no_center_of_gravity(self):
        combined = mass_properties.AxisymmetricMassProperties.combine(
            (point_mass(0.0, 0.1), point_mass(0.0, 0.2))
        )

        assert combined.mass == 0.0
        assert np.isnan(combined.center_of_gravity).all()
        np.testing.assert_array_equal(combined.moment_of_inertia, np.zeros((3, 3)))

    def test_center_of_gravity_and_inertia_tensor_lie_along_the_x_axis(self):
        body = mass_properties.AxisymmetricMassProperties(
            mass=1.0,
            axial_position=0.4,
            axial_moment_of_inertia=0.01,
            transverse_moment_of_inertia=0.05,
        )

        np.testing.assert_array_equal(body.center_of_gravity, [0.4, 0.0, 0.0])
        np.testing.assert_array_equal(
            body.moment_of_inertia, np.diag([0.01, 0.05, 0.05])
        )
