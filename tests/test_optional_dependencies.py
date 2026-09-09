import importlib.util
import subprocess
import sys
import textwrap

import pytest

import machwave.common.extras as extras

pytestmark = pytest.mark.core

OPTIONAL_PACKAGES = (
    "rocketcea",
    "CoolProp",
    "skfmm",
    "skimage",
    "trimesh",
    "plotly",
    "rocketpy",
)

PUBLIC_IMPORT_SURFACE = """
    import machwave
    import machwave.adapters
    import machwave.core
    import machwave.models
    import machwave.models.feed_systems
    import machwave.models.grain
    import machwave.models.grain.geometries
    import machwave.models.motors
    import machwave.models.nozzle_losses
    import machwave.models.propellants
    import machwave.models.propellants.formulations
    import machwave.models.thrust_chamber
    import machwave.montecarlo
    import machwave.services
    import machwave.simulation

    assert machwave.__version__
"""

BATES_SIMULATION = """
    import machwave.models.grain as grain_models
    import machwave.models.motors as motors_models
    import machwave.models.nozzle_losses as nozzle_losses
    import machwave.models.propellants.formulations as formulations
    import machwave.models.thrust_chamber as thrust_chamber_models
    import machwave.simulation as simulation

    grain = grain_models.Grain(spacing=10e-3)
    for _ in range(4):
        grain.add_segment(
            grain_models.geometries.BatesSegment(
                outer_diameter=41e-3, core_diameter=15e-3, length=67.5e-3
            )
        )

    motor = motors_models.SolidMotor(
        grain=grain,
        propellant=formulations.solid.KNDX,
        thrust_chamber=thrust_chamber_models.SolidMotorThrustChamber(
            nozzle=thrust_chamber_models.Nozzle(
                inlet_diameter=43e-3,
                throat_diameter=9.5e-3,
                divergent_angle=12,
                convergent_angle=40,
                expansion_ratio=8,
            ),
            combustion_chamber=thrust_chamber_models.CombustionChamber(
                casing_inner_diameter=44.5e-3,
                casing_outer_diameter=50.8e-3,
                thermal_liner_thickness=1e-3,
                internal_length=grain.total_length + 10e-3,
            ),
            nozzle_exit_to_grain_port_distance=0.01,
        ),
        combustion_efficiency=0.95,
        nozzle_loss_model=nozzle_losses.presets.spp1975_solid_loss_model(
            other_losses=0.12
        ),
    )

    result = simulation.InternalBallisticsSimulation(
        motor=motor,
        params=simulation.InternalBallisticsSimulationParams(
            d_t=0.01, igniter_pressure=1e6, external_pressure=1e5
        ),
    ).run()

    assert result.thrust.max() > 0
"""


IMPORT_CHECK = """
    import sys

    loaded = sorted(set(OPTIONAL_PACKAGES) & set(sys.modules))
    assert not loaded, f"core path loaded optional packages: {loaded}"
"""


def assert_no_optional_package_loaded(body: str) -> None:
    """
    Run a snippet in a fresh interpreter, asserting it loads no optional package.

    A subprocess is what makes this meaningful in an environment where the
    optional packages are installed: it proves nothing on the core path imports
    them, rather than only that the core path works when they are absent.
    """
    script = "\n".join(
        [
            f"OPTIONAL_PACKAGES = {OPTIONAL_PACKAGES!r}",
            textwrap.dedent(body),
            textwrap.dedent(IMPORT_CHECK),
        ]
    )

    completed = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=False
    )

    assert completed.returncode == 0, completed.stderr


def test_public_import_surface_loads_no_optional_package():
    assert_no_optional_package_loaded(PUBLIC_IMPORT_SURFACE)


def test_bates_solid_simulation_runs_on_the_core_dependencies():
    assert_no_optional_package_loaded(BATES_SIMULATION)


def is_installed(package: str) -> bool:
    """Whether a package can be imported in this environment."""
    return importlib.util.find_spec(package) is not None


def skip_if_installed(package: str):
    """Skip when the package is installed, since the guard cannot fire then."""
    return pytest.mark.skipif(
        is_installed(package), reason=f"{package} is installed; the guard cannot fire"
    )


@skip_if_installed("skfmm")
def test_fmm_geometry_construction_names_the_fmm_extra():
    import machwave.models.grain.geometries as geometries

    with pytest.raises(ImportError, match=rf"machwave\[{extras.FMM}\]"):
        geometries.StarGrainSegment(
            length=0.1,
            outer_diameter=0.065,
            number_of_points=5,
            point_length=0.01,
            point_width=0.005,
        )


@skip_if_installed("trimesh")
def test_stl_grain_segment_names_the_fmm_extra():
    import machwave.models.grain.fmm as grain_fmm

    class StlSegment(grain_fmm.FMMSTLGrainSegment):
        def get_web_thickness(self) -> float:
            return 0.0

    with pytest.raises(ImportError, match=rf"machwave\[{extras.FMM}\]"):
        StlSegment(file_path="grain.stl", outer_diameter=0.065, length=0.1)


@skip_if_installed("CoolProp")
def test_tank_construction_names_the_liquid_extra():
    import machwave.models.feed_systems.tank as tank_models

    with pytest.raises(ImportError, match=rf"machwave\[{extras.LIQUID}\]"):
        tank_models.Tank(
            fluid_name="N2O",
            volume=0.01,
            temperature=293.15,
            initial_fluid_mass=5.0,
        )


@skip_if_installed("rocketcea")
def test_biliquid_evaluation_names_the_cea_extra():
    import machwave.models.propellants.formulations as formulations

    with pytest.raises(ImportError, match=rf"machwave\[{extras.CEA}\]"):
        formulations.biliquid.LOX_LH2_6_0.evaluate(chamber_pressure=6e6)


@skip_if_installed("plotly")
def test_plot_module_import_names_the_plots_extra():
    with pytest.raises(ImportError, match=rf"machwave\[{extras.PLOTS}\]"):
        import machwave.services.plots.internal_ballistics  # noqa: F401


@skip_if_installed("rocketpy")
def test_rocketpy_adapter_import_names_the_rocketpy_extra():
    with pytest.raises(ImportError, match=rf"machwave\[{extras.ROCKETPY}\]"):
        import machwave.adapters.rocketpy  # noqa: F401
