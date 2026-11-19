"""Export the assembly as compact meshes for the 3D viewer (docs/viewer/).

    python tools/export_web.py

Writes docs/viewer/model.json: part list, colours, explode vectors, the lift
numbers for the animation, a resting pile of capsules for the hopper, and
"data", a base64 blob of float32 vertices + uint32 indices that the parts
index into. All parts are in world coordinates; the car is exported in its
down position and the viewer moves it up by the lift height.
"""
from __future__ import annotations

import base64
import json
import sys
from math import cos, radians, sqrt
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cad"))

from build123d import Pos, Sphere  # noqa: E402

import model as m  # noqa: E402

from params import (CAR_R, COL_LEG, COL_T, FLOOR_SLOPE, GUIDE_XY, HALF,  # noqa: E402
                    HOUSING_HX, HOUSING_Y0, LED_COLLAR_Z, LIFT_TRAVEL, PAYLOAD_D,
                    R_OUT, RIVET_U, RIVET_Z, S, STROKE, WASHER_TOP)

OUT = ROOT / "docs" / "viewer"
TOL, ANG = 0.15, 0.35


def hexcol(key):
    rgb = m.COLORS[key].wrapped.GetRGB()
    return "#%02x%02x%02x" % tuple(round(255 * c) for c in (rgb.Red(), rgb.Green(), rgb.Blue()))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    blob = bytearray()
    parts = []

    def add(name, shape, color, group, explode=(0, 0, 0), **extra):
        verts, tris = shape.tessellate(TOL, ANG)
        v = np.array([(p.X, p.Y, p.Z) for p in verts], dtype=np.float32)
        t = np.array(tris, dtype=np.uint32)
        vo = len(blob)
        blob.extend(v.tobytes())
        io = len(blob)
        blob.extend(t.tobytes())
        parts.append(dict(name=name, color=hexcol(color), group=group,
                          explode=list(explode), v=[vo, len(v)], i=[io, t.size], **extra))
        print(f"  {name:22s} {len(t):6d} tris")

    glyph, shadow = m.make_glyph(), m.make_shadow()
    cap = m.make_rivet_cap()
    out = {"front": (0, -1, 0), "back": (0, 1, 0), "left": (-1, 0, 0), "right": (1, 0, 0)}
    for side, kind in (("front", "plain"), ("left", "plain"), ("back", "back"), ("right", "right")):
        ox, oy, _ = out[side]
        ex = (ox * 110, oy * 110, 40)
        add(f"wall_{side}", m.place_side(m.make_side_panel(kind), side), "body", "shell", ex)
        add(f"glyph_{side}", m.place_side(glyph, side), "glyph", "shell", ex)
        add(f"shadow_{side}", m.place_side(shadow, side), "shadow", "shell", ex)
        caps = None
        for u in (-RIVET_U, RIVET_U):
            for z in RIVET_Z:
                c = m.place_side(Pos(u, z, -1.8) * cap, side)
                caps = c if caps is None else caps + c
        add(f"caps_{side}", caps, "rivet", "shell", (ox * 140, oy * 140, 40))
    lid_caps = None
    for u, v in m.corners(RIVET_U):
        c = m.place_lid(Pos(u, v, -1.8) * cap)
        lid_caps = c if lid_caps is None else lid_caps + c
    add("lid", m.place_lid(m.make_lid()), "body", "shell", (0, 0, 260))
    add("caps_lid", lid_caps, "rivet", "shell", (0, 0, 290))

    add("chassis", m.make_chassis(), "inner", "core")
    add("motor", m.motor_dummy(), "motor", "core", (60, 0, 0))
    pulleys, belt = m.belt_dummy()
    add("pulleys", pulleys, "motor", "core", (0, -60, 0))
    add("belt", belt, "shadow", "core", (0, -60, 0))
    add("housing", m.make_housing(), "inner", "core", (0, -95, 60))
    add("hopper", m.make_hopper(), "inner", "core", (0, 0, 150))
    add("tube", m.make_tube(), "tube", "core", (0, 0, 115))
    add("led_collar", Pos(0, 0, LED_COLLAR_Z) * m.make_led_collar(), "inner", "core", (0, 0, 205))
    sleeves = None
    for x, y in m.corners(GUIDE_XY):
        s = Pos(x, y, WASHER_TOP) * m.make_sleeve()
        sleeves = s if sleeves is None else sleeves + s
    add("sleeves", sleeves, "inner", "core", (0, 0, -40))
    add("hit_panel", m.make_hit_panel(), "body", "hit", (0, 0, -80))
    add("car", m.make_car(), "moving", "car", (0, 0, 45))

    queue, queue_up = queue_spots()
    pile = hopper_pile([queue, queue_up])
    print(f"  hopper pile: {len(pile)} capsules (+1 queued, +1 in the car)")
    meta = dict(
        size=S, parts=parts, stroke=STROKE, ball_d=PAYLOAD_D,
        ball_z=m.chamber_ball_z(0), travel=LIFT_TRAVEL,
        queue=queue, queue_up=queue_up, pile=pile,
        colors={k: hexcol(k) for k in m.COLORS},
    )
    meta["data"] = base64.b64encode(bytes(blob)).decode()  # one servable file
    (OUT / "model.json").write_text(json.dumps(meta))
    print(f"wrote {OUT/'model.json'} ({len(meta['data'])/1e6:.1f} MB)")


R = PAYLOAD_D / 2
REST = R / cos(radians(FLOOR_SLOPE))  # centre above the floor point below it


def _rest_z(x, y):
    return m.floor_height(x, y) + REST


def queue_spots():
    """Where the next capsule waits at the window: leaning on the capsule in
    the car (car down), and leaning on the car's side wall (car up)."""
    zc = m.chamber_ball_z(0)
    y = 45.0
    while y > 0:  # roll toward the tube until it touches the loaded capsule
        z = _rest_z(0, y - 0.1)
        if sqrt((y - 0.1) ** 2 + (z - zc) ** 2) < PAYLOAD_D + 0.1:
            break
        y -= 0.1
    down = [0.0, round(y, 2), round(_rest_z(0, y), 2)]
    yu = CAR_R + R + 0.1
    up = [0.0, round(yu, 2), round(_rest_z(0, yu), 2)]
    return down, up


def hopper_pile(reserved):
    """A loose single layer of capsules resting on the hopper floor, filled
    from the lowest point outward, then checked against the real solids."""
    lim = HALF - R - 0.6
    solids = [m.make_hopper(), m.make_tube(), m.make_housing(),
              Pos(0, 0, LED_COLLAR_Z) * m.make_led_collar()]

    def in_column(x, y):
        ax, ay = abs(x), abs(y)
        a = ax > HALF - COL_LEG - R and ay > HALF - COL_T - R
        b = ax > HALF - COL_T - R and ay > HALF - COL_LEG - R
        return a or b

    cand = []
    for x in np.arange(-lim, lim + 0.01, 2.0):
        for y in np.arange(-lim, lim + 0.01, 2.0):
            if sqrt(x * x + y * y) < R_OUT + R + 1 or in_column(x, y):
                continue
            if abs(x) < HOUSING_HX + R + 1 and HOUSING_Y0 - 7 - R - 1 < y < 0:
                continue
            cand.append((_rest_z(x, y), float(x), float(y)))
    cand.sort()
    taken = [tuple(p) for p in reserved]
    out = []
    for z, x, y in cand:
        if all((x - a) ** 2 + (y - b) ** 2 + (z - c) ** 2 >= (PAYLOAD_D + 0.6) ** 2
               for a, b, c in taken):
            b = Pos(x, y, z) * Sphere(R)
            lift = 0.0
            while lift < 8 and any(m_overlap(b, s_) > 1.0 for s_ in solids):
                lift += 1.0
                b = Pos(x, y, z + lift) * Sphere(R)
            if lift >= 8:
                continue
            taken.append((x, y, z + lift))
            out.append([round(x, 2), round(y, 2), round(z + lift, 2)])
    return out


def m_overlap(a, b):
    r = a & b
    return 0.0 if r is None else r.volume


if __name__ == "__main__":
    main()
