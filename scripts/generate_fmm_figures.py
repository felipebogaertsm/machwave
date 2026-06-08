"""Generate the SVG step figures for docs/theory/fmm.md.

Runs the real 2D FMM pipeline on a generic circular bore at a coarse map_dim
(so the arrays match the matrices printed on the page) and writes one small
hand-built SVG per step into docs/assets/theory/fmm/.
"""

from pathlib import Path

import numpy as np

import machwave.models.grain.fmm as fmm

MAP_DIM = 13
CORE_RADIUS = 0.45  # normalized
WEB_FRACTION = 0.35  # of web thickness
CELL = 22
OUT = "#eceff1"  # outside the casing
PROP = "#cdbb92"  # solid propellant
BURN = "#e2683c"  # burning surface / burned away
GRID = "#ffffff"
OUT_DIR = Path("docs/assets/theory/fmm")

VIRIDIS = [(68, 1, 84), (59, 82, 139), (33, 145, 140), (94, 201, 98), (253, 231, 37)]
COOLWARM = [(59, 76, 192), (221, 221, 221), (180, 4, 38)]


class CircularPort(fmm.FMMGrainSegment2D):
    def __init__(self, R, **kw):
        self._R = R
        super().__init__(**kw)

    def get_initial_face_map(self):
        map_x, map_y = self.get_maps()
        core = self.get_empty_face_map()
        core[np.sqrt(map_x**2 + map_y**2) <= self._R] = 0
        return core


def _lerp(stops, t):
    t = min(max(t, 0.0), 1.0)
    n = len(stops) - 1
    pos = t * n
    i = min(int(pos), n - 1)
    f = pos - i
    a, b = stops[i], stops[i + 1]
    return tuple(round(a[k] + (b[k] - a[k]) * f) for k in range(3))


def _hex(rgb):
    return "#%02x%02x%02x" % rgb


def write_svg(path, colors, polyline=None):
    n = len(colors)
    size = n * CELL
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 {size} {size}" shape-rendering="crispEdges">'
    ]
    for i, row in enumerate(colors):
        for j, fill in enumerate(row):
            parts.append(
                f'<rect x="{j * CELL}" y="{i * CELL}" width="{CELL}" height="{CELL}" '
                f'fill="{fill}" stroke="{GRID}" stroke-width="1.5"/>'
            )
    if polyline is not None:
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in polyline)
        parts.append(
            f'<polyline points="{pts}" fill="none" stroke="#1b1b1b" '
            f'stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>'
        )
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    s = CircularPort(R=CORE_RADIUS, length=1.0, outer_diameter=1.0, map_dim=100)
    s.map_dim = MAP_DIM
    s.maps = s.mask = s.masked_face = s.regression_map = s.web_thickness = None
    s.face_area_interp_func = s.burn_area_interp_func = None

    map_x, map_y = s.get_maps()
    mask = s.get_mask()
    face = s.get_initial_face_map()
    masked = s.get_masked_face()
    reg = s.get_regression_map()
    web = WEB_FRACTION * s.get_web_thickness()
    face_w = s.get_face_map(web)
    contour = s.get_contours(web)[0]

    # Coordinate gradients (diverging coolwarm over [-1, 1]).
    write_svg(
        OUT_DIR / "coord_x.svg",
        [[_hex(_lerp(COOLWARM, (v + 1) / 2)) for v in row] for row in map_x],
    )
    write_svg(
        OUT_DIR / "coord_y.svg",
        [[_hex(_lerp(COOLWARM, (v + 1) / 2)) for v in row] for row in map_y],
    )

    # Casing mask: propellant disc on the outside.
    write_svg(OUT_DIR / "mask.svg", [[OUT if m else PROP for m in row] for row in mask])

    # Initial port and masked face: solid / burning / outside.
    write_svg(
        OUT_DIR / "initial_face.svg",
        [[BURN if v == 0 else PROP for v in row] for row in face],
    )
    write_svg(
        OUT_DIR / "masked_face.svg",
        [
            [OUT if np.ma.is_masked(v) else (BURN if v == 0 else PROP) for v in row]
            for row in masked
        ],
    )

    # Regression field: reversed-viridis gradient (bright at the surface).
    reg_max = float(np.max(reg))
    reg_colors = []
    for row in reg:
        line = []
        for v in row:
            if np.ma.is_masked(v):
                line.append(OUT)
            else:
                line.append(_hex(_lerp(VIRIDIS, 1.0 - float(v) / reg_max)))
        reg_colors.append(line)
    write_svg(OUT_DIR / "regression.svg", reg_colors)

    # Regressed face at the web distance, then the same with the traced front.
    face_colors = [
        [OUT if v == -1 else (BURN if v == 0 else PROP) for v in row] for row in face_w
    ]
    write_svg(OUT_DIR / "face_map.svg", face_colors)
    polyline = [(c * CELL + CELL / 2, r * CELL + CELL / 2) for r, c in contour]
    write_svg(OUT_DIR / "contours.svg", face_colors, polyline=polyline)

    print(
        f"web_thickness={s.get_web_thickness():.3f} web={web:.3f} "
        f"reg_max={reg_max:.3f} contour_pts={len(contour)}"
    )
    for p in sorted(OUT_DIR.glob("*.svg")):
        print(f"  {p}  ({p.stat().st_size} B)")


if __name__ == "__main__":
    main()
