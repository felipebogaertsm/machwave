"""Meshing the burn-area iso-levels in worker processes must not change them.

The pool is an optimization for fine grids only: small fields, worker
processes, and pools that fail to start all mesh the levels in-process, and
every path has to return the same areas.
"""

import numpy as np
import pytest

import machwave.models.grain.fmm._3d as fmm_3d
from tests.factories import ConicalGrainSegmentFactory

WEB_DISTANCES = (0.0, 0.002, 0.005, 0.01)


def _segment():
    return ConicalGrainSegmentFactory.build(length=0.05, outer_diameter=0.1)


def _burn_areas():
    segment = _segment()
    return [segment.get_burn_area(web_distance) for web_distance in WEB_DISTANCES]


def _force_parallel(monkeypatch):
    monkeypatch.setattr(fmm_3d, "FORK_PARALLEL_CELL_COUNT", 0)
    monkeypatch.setattr(fmm_3d, "SPAWN_PARALLEL_CELL_COUNT", 0)


def test_pooled_areas_match_in_process_areas(monkeypatch):
    serial = _burn_areas()

    _force_parallel(monkeypatch)
    assert _burn_areas() == serial


def test_small_field_never_starts_a_pool(monkeypatch):
    def fail(*args, **kwargs):
        pytest.fail("A pool was started for a field below the parallel threshold")

    monkeypatch.setattr(fmm_3d, "_compute_iso_surface_areas_in_parallel", fail)

    # The default grid over a short segment holds ~0.5M cells, well under both
    # thresholds.
    assert _segment().get_burn_area(0.0) > 0.0


def test_falls_back_when_the_pool_cannot_start(monkeypatch):
    serial = _burn_areas()

    def raise_os_error(*args, **kwargs):
        raise OSError("no worker processes available")

    _force_parallel(monkeypatch)
    monkeypatch.setattr(
        fmm_3d.concurrent.futures, "ProcessPoolExecutor", raise_os_error
    )
    assert _burn_areas() == serial


def test_worker_processes_mesh_in_process(monkeypatch):
    _force_parallel(monkeypatch)
    monkeypatch.setattr(fmm_3d.multiprocessing, "parent_process", lambda: object())

    assert not fmm_3d._is_parallel_meshing_worthwhile(10**9)


@pytest.mark.parametrize(
    ("start_method", "cell_count", "expected"),
    [
        ("fork", fmm_3d.FORK_PARALLEL_CELL_COUNT - 1, False),
        ("fork", fmm_3d.FORK_PARALLEL_CELL_COUNT, True),
        ("spawn", fmm_3d.FORK_PARALLEL_CELL_COUNT, False),
        ("spawn", fmm_3d.SPAWN_PARALLEL_CELL_COUNT, True),
    ],
)
def test_threshold_depends_on_the_start_method(
    monkeypatch, start_method, cell_count, expected
):
    monkeypatch.setattr(
        fmm_3d.multiprocessing, "get_start_method", lambda: start_method
    )
    monkeypatch.setattr(fmm_3d.multiprocessing, "parent_process", lambda: None)

    assert fmm_3d._is_parallel_meshing_worthwhile(cell_count) is expected


def test_worker_rejects_levels_before_it_holds_a_field(monkeypatch):
    monkeypatch.setattr(fmm_3d, "_worker_distance_field", None)
    monkeypatch.setattr(fmm_3d, "_worker_grid_spacing", None)

    with pytest.raises(RuntimeError):
        fmm_3d._compute_iso_surface_area_in_worker(0.5)


def test_worker_meshes_the_field_it_was_loaded_with(monkeypatch):
    segment = _segment()
    regression_map = segment.get_padded_regression_map()
    values = np.asarray(
        regression_map[~np.ma.getmaskarray(regression_map)], dtype=np.float64
    )
    max_level = float(values.max())
    distance_field = np.ma.filled(regression_map, max_level + 1.0)
    grid_spacing = (
        segment.get_axial_grid_spacing(),
        segment.get_radial_grid_spacing(),
        segment.get_radial_grid_spacing(),
    )
    level = max_level / 2

    # Restored by monkeypatch once the test leaves the worker globals set.
    monkeypatch.setattr(fmm_3d, "_worker_distance_field", None)
    monkeypatch.setattr(fmm_3d, "_worker_grid_spacing", None)
    fmm_3d._load_iso_surface_worker(distance_field, grid_spacing)

    assert fmm_3d._compute_iso_surface_area_in_worker(level) == (
        fmm_3d._compute_iso_surface_area(distance_field, level, grid_spacing)
    )
