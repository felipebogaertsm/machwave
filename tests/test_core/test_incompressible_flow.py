import math

import pytest

import machwave.core.geometric as geometric
import machwave.core.incompressible_flow as incompressible_flow


@pytest.mark.parametrize(
    "discharge_coefficient,area,density,pressure_upstream,pressure_downstream,expected",
    [
        (0.8, 0.001, 1000, 3e5, 1e5, pytest.approx(16.0)),
        (0.9, 0.0005, 1200, 5e5, 1e5, pytest.approx(13.943, rel=1e-3)),
        (0.7, 0.002, 800, 2e5, 2e5, pytest.approx(0.0)),
        (0.85, 0.0001, 1500, 4e5, 2e5, pytest.approx(2.082, rel=1e-3)),
        (0.95, 0.0015, 900, 6e5, 3e5, pytest.approx(33.114, rel=1e-3)),
    ],
)
def test_get_mass_flow_orifice(
    discharge_coefficient,
    area,
    density,
    pressure_upstream,
    pressure_downstream,
    expected,
):
    mass_flow = incompressible_flow.get_mass_flow_orifice(
        discharge_coefficient,
        area,
        density,
        pressure_upstream,
        pressure_downstream,
    )
    assert mass_flow == expected


def test_get_mass_flow_orifice_raises_value_error():
    """ValueError is raised when downstream pressure exceeds upstream pressure."""
    with pytest.raises(
        ValueError, match="Pressure downstream cannot be greater than upstream"
    ):
        incompressible_flow.get_mass_flow_orifice(
            discharge_coefficient=0.8,
            area=0.001,
            density=1000,
            pressure_upstream=1e5,
            pressure_downstream=3e5,  # Higher than upstream
        )


class TestReynoldsNumber:
    def test_matches_the_definition(self):
        assert incompressible_flow.get_reynolds_number(
            density=1000.0, velocity=2.0, diameter=0.01, dynamic_viscosity=1e-3
        ) == pytest.approx(1000.0 * 2.0 * 0.01 / 1e-3)

    def test_direction_does_not_matter(self):
        forward = incompressible_flow.get_reynolds_number(1000.0, 2.0, 0.01, 1e-3)
        reverse = incompressible_flow.get_reynolds_number(1000.0, -2.0, 0.01, 1e-3)
        assert forward == reverse

    def test_rejects_non_positive_viscosity(self):
        with pytest.raises(ValueError, match="dynamic_viscosity"):
            incompressible_flow.get_reynolds_number(1000.0, 2.0, 0.01, 0.0)


class TestDarcyFrictionFactor:
    def test_still_fluid_has_no_friction(self):
        assert incompressible_flow.get_darcy_friction_factor(0.0) == 0.0

    @pytest.mark.parametrize("reynolds_number", [10.0, 500.0, 2000.0])
    def test_laminar_branch_is_the_exact_solution(self, reynolds_number):
        assert incompressible_flow.get_darcy_friction_factor(
            reynolds_number
        ) == pytest.approx(64.0 / reynolds_number)

    @pytest.mark.parametrize(
        ("reynolds_number", "expected"),
        # Smooth-pipe Colebrook solutions, which Haaland stands in for.
        [(1e4, 0.0309), (1e5, 0.0180), (1e6, 0.0116)],
    )
    def test_turbulent_branch_tracks_colebrook_on_a_smooth_pipe(
        self, reynolds_number, expected
    ):
        assert incompressible_flow.get_darcy_friction_factor(
            reynolds_number
        ) == pytest.approx(expected, rel=0.03)

    def test_roughness_raises_the_friction_factor(self):
        smooth = incompressible_flow.get_darcy_friction_factor(1e6)
        rough = incompressible_flow.get_darcy_friction_factor(
            1e6, relative_roughness=1e-3
        )
        assert rough > smooth

    def test_a_rough_pipe_stops_following_reynolds(self):
        # Fully rough flow is set by the wall, not by the Reynolds number.
        rough = [
            incompressible_flow.get_darcy_friction_factor(
                reynolds_number, relative_roughness=0.01
            )
            for reynolds_number in (1e6, 1e8)
        ]
        assert rough[0] == pytest.approx(rough[1], rel=0.02)


class TestPipePressureDrop:
    def test_still_fluid_has_no_drop(self):
        assert (
            incompressible_flow.get_pipe_pressure_drop(
                density=1000.0,
                mass_flow_rate=0.0,
                length=1.0,
                diameter=0.01,
                dynamic_viscosity=1e-3,
            )
            == 0.0
        )

    def test_matches_darcy_weisbach(self):
        density = 800.0
        mass_flow_rate = 0.5
        length = 1.5
        diameter = 0.008
        dynamic_viscosity = 1.2e-3

        drop = incompressible_flow.get_pipe_pressure_drop(
            density=density,
            mass_flow_rate=mass_flow_rate,
            length=length,
            diameter=diameter,
            dynamic_viscosity=dynamic_viscosity,
        )

        velocity = mass_flow_rate / (density * geometric.get_circle_area(diameter))
        friction_factor = incompressible_flow.get_darcy_friction_factor(
            density * velocity * diameter / dynamic_viscosity
        )
        assert drop == pytest.approx(
            friction_factor * (length / diameter) * density * velocity**2 / 2
        )

    def test_laminar_flow_follows_hagen_poiseuille(self):
        # Darcy-Weisbach with f = 64 / Re collapses onto the exact laminar law.
        density = 900.0
        diameter = 0.004
        length = 1.0
        dynamic_viscosity = 0.05
        mass_flow_rate = 1e-3

        drop = incompressible_flow.get_pipe_pressure_drop(
            density=density,
            mass_flow_rate=mass_flow_rate,
            length=length,
            diameter=diameter,
            dynamic_viscosity=dynamic_viscosity,
        )

        volumetric_flow_rate = mass_flow_rate / density
        hagen_poiseuille = (128 * dynamic_viscosity * length * volumetric_flow_rate) / (
            math.pi * diameter**4
        )
        assert drop == pytest.approx(hagen_poiseuille)

    def test_fittings_add_velocity_heads(self):
        arguments = dict(
            density=800.0,
            mass_flow_rate=0.5,
            length=1.5,
            diameter=0.008,
            dynamic_viscosity=1.2e-3,
        )
        bare = incompressible_flow.get_pipe_pressure_drop(**arguments)
        with_fittings = incompressible_flow.get_pipe_pressure_drop(
            **arguments, loss_coefficient=2.0
        )

        velocity = arguments["mass_flow_rate"] / (
            arguments["density"] * geometric.get_circle_area(arguments["diameter"])
        )
        velocity_head = arguments["density"] * velocity**2 / 2
        assert with_fittings - bare == pytest.approx(2.0 * velocity_head)

    def test_drop_grows_with_the_square_of_the_flow(self):
        arguments = dict(
            density=800.0, length=1.5, diameter=0.008, dynamic_viscosity=1.2e-3
        )
        single = incompressible_flow.get_pipe_pressure_drop(
            mass_flow_rate=0.25, **arguments
        )
        double = incompressible_flow.get_pipe_pressure_drop(
            mass_flow_rate=0.5, **arguments
        )
        # Not exactly four times: the friction factor eases off with Reynolds,
        # which over a doubling costs the ratio a little under a fifth of a power.
        assert 3.3 < double / single < 4.0

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("density", 0.0),
            ("diameter", 0.0),
            ("length", -1.0),
            ("loss_coefficient", -1.0),
        ],
    )
    def test_rejects_out_of_range_inputs(self, field, value):
        arguments = dict(
            density=800.0,
            mass_flow_rate=0.5,
            length=1.5,
            diameter=0.008,
            dynamic_viscosity=1.2e-3,
        )
        arguments[field] = value

        with pytest.raises(ValueError, match=field):
            incompressible_flow.get_pipe_pressure_drop(**arguments)
