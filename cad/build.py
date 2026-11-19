"""Export every printable part (STL + colour 3MF) and the documentation renders.

    python cad/build.py            # everything
    python cad/build.py --no-render
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from build123d import Box, Mesher, Pos, export_stl  # noqa: E402

import model as m  # noqa: E402
from params import S, RIVET_U, RIVET_Z  # noqa: E402

ROOT = HERE.parent
STL, MF, IMG = ROOT / "stl", ROOT / "3mf", ROOT / "images" / "renders"


def export_all():
    STL.mkdir(exist_ok=True)
    MF.mkdir(exist_ok=True)
    parts = m.printable_parts()
    for name, (shape, qty, color, note) in parts.items():
        export_stl(shape, STL / f"{name}.stl", tolerance=0.02, angular_tolerance=0.15)
        print(f"  stl/{name}.stl  x{qty}  ({note})")

    # Multi-colour panels: one 3MF per wall with body / glyph / shadow parts.
    glyph, shadow = m.make_glyph(), m.make_shadow()
    for kind, fname in (("plain", "panel_front_left"), ("back", "panel_back"),
                        ("right", "panel_right")):
        mesher = Mesher()
        for part, ck, label in ((m.make_side_panel(kind), "body", "body"),
                                (glyph, "glyph", "glyph"),
                                (shadow, "shadow", "shadow")):
            part.color = m.COLORS[ck]
            part.label = label
            mesher.add_shape(part, linear_deflection=0.02, angular_deflection=0.15,
                             part_number=f"{fname}_{label}")
        mesher.write(str(MF / f"{fname}.3mf"))
        print(f"  3mf/{fname}.3mf")


def rivet_caps():
    cap = m.make_rivet_cap()
    out = []
    for side in m.PANEL_PLACEMENT:
        for u in (-RIVET_U, RIVET_U):
            for z in RIVET_Z:
                # cap face sits on the outside face (local z=0), peg goes in
                local = Pos(u, z, -1.8) * cap
                out.append(m.place_side(local, side))
    for u, v in m.corners(RIVET_U):
        out.append(m.place_lid(Pos(u, v, -1.8) * cap))
    return out


def renders():
    IMG.mkdir(parents=True, exist_ok=True)
    from render import render

    col = {k: (c.wrapped.GetRGB().Red(), c.wrapped.GetRGB().Green(),
               c.wrapped.GetRGB().Blue()) for k, c in m.COLORS.items()}
    asm = m.assembly()
    caps = [(c, col["rivet"]) for c in rivet_caps()]

    # 1. hero shot
    render([(s, col[k]) for _, s, k, _ in asm] + caps, IMG / "assembly.png",
           title="Mystery block (160 mm)")

    # 2. bottom view (hit panel)
    render([(s, col[k]) for _, s, k, _ in asm] + caps, IMG / "bottom.png",
           elev=-35, azim=-60, title="Bottom: the hit panel")

    # 3. cutaway: remove front + left walls and lid
    hide = {"panel_front", "glyph_front", "shadow_front", "panel_left",
            "glyph_left", "shadow_left", "lid"}
    render([(s, col[k]) for n, s, k, _ in asm if n not in hide],
           IMG / "cutaway.png", title="Inside: hopper, tube, chassis")

    def section(parts, keep):
        out = []
        for n, s, k, _ in parts:
            cut = s & keep
            if cut is not None and cut.volume > 1e-3:
                out.append((cut, col[k]))
        return out

    # 4./5. section through the capsule path and the belt (x = 0 plane)
    keep_x = Pos(S / 2, 0, S / 2) * Box(S, S * 2, S * 2)
    render(section(asm, keep_x), IMG / "section.png", elev=8, azim=-170,
           title="Section: capsule waits in the lift car (down)")
    asm_up = m.assembly(lift="up")
    render(section(asm_up, keep_x), IMG / "section_up.png", elev=8, azim=-170,
           title="Section: car up, capsule out of the lid")

    # 6./7. lift close-ups: walls, hopper and collar hidden, seen from +X
    hide_walls = {n for n, *_ in asm if n.startswith(("panel_", "glyph_", "shadow_"))}
    hide_walls |= {"lid", "hopper", "led_collar"}
    for st, fname, title in (("down", "lift_down.png", "Lift down: capsule rolls into the car"),
                             ("up", "lift_up.png", "Lift up: belt has raised the car 75 mm")):
        parts = [p for p in m.assembly(lift=st) if p[0] not in hide_walls]
        render(section(parts, keep_x), IMG / fname, elev=10, azim=-150, title=title)

    # 6. exploded view
    offs = {"hit_panel": -60, "chassis": 0, "motor": 0, "pulleys": 0, "belt": 0,
            "car": 45, "housing": 80, "tube": 110, "hopper": 150,
            "led_collar": 210, "lid": 280}
    ex = []
    for n, s, k, _ in asm:
        if n.startswith(("panel_", "glyph_", "shadow_")):
            side = n.split("_")[1]
            vec = {"front": (0, -70, 60), "back": (0, 70, 60),
                   "left": (-70, 0, 60), "right": (70, 0, 60)}[side]
            ex.append((Pos(*vec) * s, col[k]))
        elif n.startswith("sleeve"):
            ex.append((Pos(0, 0, -45) * s, col[k]))
        elif n.startswith("ball"):
            ex.append((Pos(0, 0, 250) * s, col[k]))
        else:
            ex.append((Pos(0, 0, offs.get(n, 0)) * s, col[k]))
    render(ex, IMG / "exploded.png", elev=18, azim=-55, title="Exploded view")
    for p in sorted(IMG.glob("*.png")):
        print(f"  {p.relative_to(ROOT)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-render", action="store_true")
    a = ap.parse_args()
    print("Exporting parts...")
    export_all()
    if not a.no_render:
        print("Rendering...")
        renders()
