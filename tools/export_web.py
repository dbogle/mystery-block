"""Export the assembly as compact meshes for the 3D viewer (docs/viewer/).

    python tools/export_web.py

Writes docs/viewer/model.json: part list, colours, pivots, explode vectors,
the lever-angle table for the animation, and "data", a base64 blob of
float32 vertices + uint32 indices that the parts index into.
Static parts are in world coordinates. The lever and cam are exported in
their own frames, so the viewer can rotate them about their axles.
"""
from __future__ import annotations

import base64
import json
import sys
from math import degrees
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cad"))

from build123d import Pos, Rot  # noqa: E402

import model as m  # noqa: E402

from params import (CAM_X, GUIDE_XY, LED_COLLAR_Z, LIFT, COAST, PAYLOAD_D,  # noqa: E402
                    PIV_X, PIV_Z, RIVET_U, RIVET_Z, S, STROKE, WASHER_TOP,
                    PISTON_TOP_SEATED)

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
    add("motor", m.motor_dummy(), "motor", "core", (0, 40, 0))
    add("tower", m.make_tower(), "inner", "core", (0, 0, 70))
    add("hopper", m.make_hopper(), "inner", "core", (0, 0, 150))
    add("tube", m.make_tube(), "tube", "core", (0, 0, 115))
    add("led_collar", Pos(0, 0, LED_COLLAR_Z) * m.make_led_collar(), "inner", "core", (0, 0, 205))
    sleeves = None
    for x, y in m.corners(GUIDE_XY):
        s = Pos(x, y, WASHER_TOP) * m.make_sleeve()
        sleeves = s if sleeves is None else sleeves + s
    add("sleeves", sleeves, "inner", "core", (0, 0, -40))
    add("hit_panel", m.make_hit_panel(), "body", "hit", (0, 0, -80))
    add("piston", m.make_piston(), "moving", "piston", (0, 0, 40))
    add("lever", m.make_lever(), "moving", "lever", (0, -45, 0), pivot=[PIV_X, 0, PIV_Z])
    add("cam", m.make_cam(), "moving", "cam", (0, -70, 0), pivot=[CAM_X, 0, m.CAM_Z])

    # lever angle (deg, about +Y as three.js rotates) for each cam angle
    table = []
    for b in range(0, 361, 2):
        bb = b if b <= 90 else b - 360
        table.append(round(-degrees(m.lever_angle_for_cam(bb)), 3))
    meta = dict(
        size=S, parts=parts, lever_table=table,
        beta_cocked=m.BETA_COCKED, cam_drop=m.CAM_DROP - 270.0,
        stroke=STROKE, lift=LIFT, coast=COAST, ball_d=PAYLOAD_D,
        ball_z=m.chamber_ball_z("cocked"), piston_top=PISTON_TOP_SEATED,
        colors={k: hexcol(k) for k in m.COLORS},
    )
    meta["data"] = base64.b64encode(bytes(blob)).decode()  # one servable file
    (OUT / "model.json").write_text(json.dumps(meta))
    print(f"wrote {OUT/'model.json'} ({len(meta['data'])/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
