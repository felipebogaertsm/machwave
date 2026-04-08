import itertools

import numpy as np

from machwave.models import grain
from machwave.models.grain import geometries
from machwave.services.plots.fmm import (
    plot_2d_face_map_animated,
    plot_3d_face_map_animated,
)


STAR_GRAIN_PARAMS = dict(
    length=100e-3,
    outer_diameter=50e-3,
    number_of_points=5,
    point_length=15e-3,
    point_width=8e-3,
)

CONICAL_GRAIN_PARAMS = dict(
    length=100e-3,
    outer_diameter=50e-3,
    upper_core_diameter=15e-3,
    lower_core_diameter=10e-3,
)


def _collect_face_maps(segment, n_steps: int = 20):
    """Collect face maps at evenly spaced web distances."""
    web_thickness = segment.get_web_thickness()
    web_distances = np.linspace(0, web_thickness * 0.95, n_steps)
    face_maps = np.array([segment.get_face_map(wd) for wd in web_distances])
    return face_maps, web_distances


def _show_2d(label: str, segment) -> None:
    face_maps, web_distances = _collect_face_maps(segment)
    fig = plot_2d_face_map_animated(face_maps, web_distances)
    fig.update_layout(title=label)
    fig.show()


def _show_3d(label: str, segment) -> None:
    face_maps, web_distances = _collect_face_maps(segment)
    fig = plot_3d_face_map_animated(face_maps, web_distances)
    fig.update_layout(title=label)
    fig.show()


def _all_inhibition_cases() -> list[tuple[str, grain.InhibitedSurfaces]]:
    """Generate all 15 valid inhibition combinations (excludes all-inhibited)."""
    cases = []
    for od, id_, ue, le in itertools.product([True, False], repeat=4):
        if od and id_ and ue and le:
            continue  # invalid: all surfaces inhibited
        label = f"OD={'T' if od else 'F'},ID={'T' if id_ else 'F'},UE={'T' if ue else 'F'},LE={'T' if le else 'F'}"
        cases.append(
            (
                label,
                grain.InhibitedSurfaces(
                    outer_surface=od,
                    inner_surface=id_,
                    upper_end=ue,
                    lower_end=le,
                ),
            )
        )
    return cases


def main():
    inhibition_cases = _all_inhibition_cases()

    # --- Star grain (2D) cases ---
    for label, inh in inhibition_cases:
        _show_2d(
            f"Star grain - {label}",
            geometries.StarGrainSegment(
                **STAR_GRAIN_PARAMS,
                inhibited_surfaces=inh,
            ),
        )

    # --- Conical grain (3D) cases ---
    for label, inh in inhibition_cases:
        _show_3d(
            f"Conical grain - {label}",
            geometries.ConicalGrainSegment(
                **CONICAL_GRAIN_PARAMS,
                inhibited_surfaces=inh,
            ),
        )


if __name__ == "__main__":
    main()
