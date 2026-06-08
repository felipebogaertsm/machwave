"""Generate the SVG step figures for docs/theory/grain_regression.md.

Runs the real 2D FMM pipeline on a generic circular bore at a coarse map_dim
(so the arrays match the matrices printed on the page) and writes one small
hand-built SVG per step into docs/assets/theory/fmm/, plus a looping animation
of the burn for the page intro.
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


def write_animation(path):
    """Looping animation of the burning surface regressing to burnout."""
    width, height = 560, 320
    cx, cy = 160, 160
    r_case, r_prop, r_bore, r_max = 150, 140, 36, 138
    front_col, arrow_col, handle = "#e2683c", "#6b7079", 20
    keytimes, dur = "0;0.82;1", "4s"
    anim_r = (
        f'<animate attributeName="r" values="{r_bore};{r_max};{r_max}" '
        f'keyTimes="{keytimes}" dur="{dur}" repeatCount="indefinite"/>'
    )
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}" '
        'font-family="sans-serif">',
        '<defs><marker id="ah" markerWidth="8" markerHeight="8" refX="5" '
        f'refY="3.5" orient="auto"><path d="M0,0 L6,3.5 L0,7 z" fill="{arrow_col}"/>'
        "</marker></defs>",
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="12" '
        'fill="#ffffff" stroke="#e6e6e6"/>',
        f'<circle cx="{cx}" cy="{cy}" r="{r_case}" fill="#454a52"/>',
        f'<circle cx="{cx}" cy="{cy}" r="{r_prop}" fill="#cdbb92"/>',
        f'<circle cx="{cx}" cy="{cy}" r="{r_bore}" fill="#f7f2ea">{anim_r}</circle>',
        f'<circle cx="{cx}" cy="{cy}" r="{r_bore}" fill="none" '
        f'stroke="{front_col}" stroke-width="6">{anim_r}</circle>',
        f'<circle cx="{cx}" cy="{cy}" r="{r_bore}" fill="#ffffff"/>',
    ]
    for k in range(16):
        deg = k * 22.5
        parts.append(
            f'<g transform="translate({cx} {cy}) rotate({deg})"><g>'
            '<animateTransform attributeName="transform" type="translate" '
            f'values="{r_bore - handle} 0;{r_max - handle} 0;{r_max - handle} 0" '
            f'keyTimes="{keytimes}" dur="{dur}" repeatCount="indefinite"/>'
            f'<line x1="0" y1="0" x2="{handle}" y2="0" stroke="{arrow_col}" '
            'stroke-width="2" marker-end="url(#ah)"/></g></g>'
        )
    lx, y, rh = 344, 84, 46
    rows = [
        ("swatch", "#cdbb92", "Propellant grain"),
        ("swatch", "#454a52", "Inhibited surface (casing)"),
        ("line", front_col, "Burning surface"),
        ("arrow", arrow_col, "Direction of regression"),
    ]
    for kind, col, text in rows:
        if kind == "swatch":
            parts.append(
                f'<rect x="{lx}" y="{y - 14}" width="20" height="20" rx="3" '
                f'fill="{col}" stroke="#bbbbbb"/>'
            )
        elif kind == "line":
            parts.append(
                f'<line x1="{lx}" y1="{y - 4}" x2="{lx + 20}" y2="{y - 4}" '
                f'stroke="{col}" stroke-width="5"/>'
            )
        else:
            parts.append(
                f'<line x1="{lx}" y1="{y - 4}" x2="{lx + 18}" y2="{y - 4}" '
                f'stroke="{col}" stroke-width="2" marker-end="url(#ah)"/>'
            )
        parts.append(
            f'<text x="{lx + 30}" y="{y}" font-size="13" fill="#3a3f47">{text}</text>'
        )
        y += rh
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n")


def write_geometry_animations(path):
    """Side-by-side looping regression of four 2D grain geometries.

    Each panel runs the real FMM pipeline; the burned region at every frame is
    the even-odd fill of the actual regression contours, so rings and merging
    ports render correctly. Frames reveal cumulatively with a moving front.
    """
    import machwave.models.grain.geometries as geometries

    specs = [
        (
            "Star",
            geometries.StarGrainSegment,
            dict(number_of_points=5, point_length=0.34, point_width=0.16),
        ),
        (
            "Rod and tube",
            geometries.RodAndTubeGrainSegment,
            dict(rod_outer_diameter=0.26, tube_inner_diameter=0.62),
        ),
        (
            "Multi-port",
            geometries.MultiPortGrainSegment,
            dict(port_diameter=0.16, port_radial_count=6, port_level_count=2),
        ),
        ("D-grain", geometries.DGrainSegment, dict(slot_offset=0.06)),
    ]
    gmap_dim, n_frames, target_pts = 120, 22, 64
    front_col, open_col, case_col, prop_col = "#e2683c", "#f7f2ea", "#454a52", "#cdbb92"
    pw, ph, pad, r_case, r_prop, disc_cy = 168, 196, 8, 70, 64, 84
    dur, reveal_end = "6s", 0.85
    half = (gmap_dim - 1) / 2
    width, height = pad * 2 + pw * len(specs), pad * 2 + ph

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}" '
        'font-family="sans-serif">',
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="12" '
        'fill="#ffffff" stroke="#e6e6e6"/>',
    ]

    for p, (title, cls, kw) in enumerate(specs):
        seg = cls(length=1.0, outer_diameter=1.0, map_dim=gmap_dim, **kw)
        web = seg.get_web_thickness()
        pcx, pcy = pad + pw * p + pw / 2, pad + disc_cy
        parts.append(
            f'<circle cx="{pcx:.1f}" cy="{pcy}" r="{r_case}" fill="{case_col}"/>'
        )
        parts.append(
            f'<circle cx="{pcx:.1f}" cy="{pcy}" r="{r_prop}" fill="{prop_col}"/>'
        )

        for i in range(n_frames):
            w = web * 0.93 * i / (n_frames - 1)
            d_parts = []
            for contour in seg.get_contours(w):
                if len(contour) < 3:
                    continue
                step = max(1, (len(contour) - 1) // target_pts)
                coords = []
                for r, c in contour[::step]:
                    x = pcx + (c - half) / half * r_prop
                    y = pcy + (r - half) / half * r_prop
                    coords.append(f"{x:.1f},{y:.1f}")
                d_parts.append("M" + " L".join(coords) + " Z")
            if not d_parts:
                continue
            d = " ".join(d_parts)
            shape = (
                f'<path d="{d}" fill="{open_col}" fill-rule="evenodd" '
                f'stroke="{front_col}" stroke-width="2.5"'
            )
            if i == 0:
                parts.append(shape + "/>")
            else:
                r = reveal_end * i / (n_frames - 1)
                parts.append(
                    shape + ' opacity="0"><animate attributeName="opacity" '
                    f'values="0;1;1" keyTimes="0;{r:.3f};1" dur="{dur}" '
                    'calcMode="discrete" repeatCount="indefinite"/></path>'
                )

        parts.append(
            f'<text x="{pcx:.1f}" y="{pad + ph - 14}" text-anchor="middle" '
            f'font-size="13" fill="#3a3f47">{title}</text>'
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

    write_svg(
        OUT_DIR / "coord_x.svg",
        [[_hex(_lerp(COOLWARM, (v + 1) / 2)) for v in row] for row in map_x],
    )
    write_svg(
        OUT_DIR / "coord_y.svg",
        [[_hex(_lerp(COOLWARM, (v + 1) / 2)) for v in row] for row in map_y],
    )
    write_svg(OUT_DIR / "mask.svg", [[OUT if m else PROP for m in row] for row in mask])
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

    face_colors = [
        [OUT if v == -1 else (BURN if v == 0 else PROP) for v in row] for row in face_w
    ]
    write_svg(OUT_DIR / "face_map.svg", face_colors)
    polyline = [(c * CELL + CELL / 2, r * CELL + CELL / 2) for r, c in contour]
    write_svg(OUT_DIR / "contours.svg", face_colors, polyline=polyline)

    write_animation(OUT_DIR / "regression_animation.svg")
    write_geometry_animations(OUT_DIR / "geometry_animations.svg")

    print(
        f"web_thickness={s.get_web_thickness():.3f} web={web:.3f} "
        f"reg_max={reg_max:.3f} contour_pts={len(contour)}"
    )
    for p in sorted(OUT_DIR.glob("*.svg")):
        print(f"  {p}  ({p.stat().st_size} B)")


if __name__ == "__main__":
    main()
