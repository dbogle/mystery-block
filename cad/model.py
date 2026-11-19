"""Parametric model of the candy-launching mystery block (build123d).

Each `make_*` function returns one printable part in *print orientation*
or in world position (noted per function). `assembly()` places every part in
world coordinates for renders and fit tests.

How it works, bottom to top:
  hit panel  -> floats on 4 guide screws, rests on washers by gravity
  piston     -> stands on the hit panel inside the launch tube
  chamber    -> one ball sits on the piston top, fed through a side window
  hopper     -> sloped floor rolls every ball toward that window
  launch     -> a bonk on the panel drives the piston up 10 mm; the panel hits
                its bumpers, the piston hits the tube end, the ball keeps going
                up the tube and out of the hatch in the lid.
"""
from __future__ import annotations

from math import sqrt

from build123d import (Align, Axis, Box, Color, Cone, Cylinder, Location,
                       Part, Plane, Polygon, Pos, Rectangle, Rot, Sphere,
                       chamfer, extrude, loft)

from params import *  # noqa: F401,F403  (design tables are meant to be global)

MIN = (Align.MIN, Align.MIN, Align.MIN)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def box(x0, x1, y0, y1, z0, z1) -> Part:
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(
        x1 - x0, y1 - y0, z1 - z0)


def cyl(r, z0, z1, x=0.0, y=0.0) -> Part:
    return Pos(x, y, (z0 + z1) / 2) * Cylinder(r, z1 - z0)


def corners(v):
    return [(sx * v, sy * v) for sx in (-1, 1) for sy in (-1, 1)]


# --------------------------------------------------------------------------
# face art
# --------------------------------------------------------------------------
def glyph_cells(dx=0.0, dz=0.0):
    """Pixel squares of the '?' in panel-local XY (mirrored: printed face down).

    Viewer coordinates (vx right, vz up when looking at the outside face)
    map to local x = -vx, local y = vz.
    """
    p = GLYPH_PIXEL
    rows, cols = len(GLYPH), len(GLYPH[0])
    top = GLYPH_CENTER_Z + rows * p / 2
    left = -cols * p / 2
    cells = []
    for r, line in enumerate(GLYPH):
        for c, ch in enumerate(line):
            if ch != "#":
                continue
            vx0 = left + c * p + dx
            vz1 = top - r * p + dz
            # slight overlap so neighbouring pixels fuse into one solid
            cells.append(box(-(vx0 + p + 0.01), -(vx0 - 0.01),
                             vz1 - p - 0.01, vz1 + 0.01, 0, GLYPH_DEPTH))
    return cells


def fuse(parts):
    out = parts[0]
    for p in parts[1:]:
        out = out + p
    return out


def make_glyph():
    return fuse(glyph_cells())


def make_shadow():
    return fuse(glyph_cells(SHADOW, -SHADOW)) - make_glyph()


# --------------------------------------------------------------------------
# wall panels (print orientation: outside face down on the bed, z=0)
# --------------------------------------------------------------------------
def _side_blank() -> Part:
    h = S / 2
    outer = Plane.XY * Pos(0, (S - EDGE_RELIEF) / 2) * Rectangle(
        S - 2 * EDGE_RELIEF, S - EDGE_RELIEF)
    inner = Plane.XY.offset(T) * Pos(0, (S - T) / 2) * Rectangle(
        2 * (h - T), S - T)
    return loft([outer, inner])


def _rivet_bores(positions, through=True):
    cut = []
    for u, v in positions:
        cut.append(cyl(RIVET_BORE_D / 2, -1, T - RIVET_FLOOR, u, v))
        if through:
            cut.append(cyl(1.7, -1, T + 1, u, v))
    return cut


def side_rivets():
    return [(u, z) for u in (-RIVET_U, RIVET_U) for z in RIVET_Z]


def make_side_panel(kind="plain"):
    """kind: 'plain' (front/left), 'back' (wall-mount holes), 'right' (USB-C)."""
    body = _side_blank() - make_glyph() - fuse(glyph_cells(SHADOW, -SHADOW))
    for c in _rivet_bores(side_rivets()):
        body = body - c
    if kind == "back":
        for u, z in MOUNT_HOLES:
            body = body - cyl(2.3, -1, T + 1, u, z)
            body = body - cyl(4.6, T - 2.5, T + 1, u, z)  # head inside
    if kind == "right":
        u, z = USB_JACK
        body = body - cyl(USB_JACK_D / 2, -1, T + 1, u, z)
    return body


# --------------------------------------------------------------------------
# lid (print orientation: top face down)
# --------------------------------------------------------------------------
def make_lid():
    outer = Plane.XY * Rectangle(S - 2 * EDGE_RELIEF, S - 2 * EDGE_RELIEF)
    inner = Plane.XY.offset(T) * Rectangle(S - 2 * T, S - 2 * T)
    lid = loft([outer, inner])
    lid = lid - cyl(R_OUT + 0.5, -1, T + 1)
    for u, v in corners(RIVET_U):
        lid = lid - cyl(RIVET_BORE_D / 2, -1, 3.0, u, v)       # rivet caps
    for u, v in corners(MAGNET_XY):
        lid = lid - cyl(MAGNET_D / 2, T - MAGNET_H, T + 1, u, v)  # magnets
    return lid


# --------------------------------------------------------------------------
# chassis: deck + lower corner posts (world position == print orientation)
# --------------------------------------------------------------------------
def mount_grid_points():
    """3.2 mm holes on a 10 mm grid wherever the deck is free."""
    pts = []
    for i in range(-7, 8):
        for j in range(-7, 8):
            x, y = i * 10.0, j * 10.0
            if max(abs(x), abs(y)) > HALF - 12:
                continue
            if sqrt(x * x + y * y) < 32:
                continue
            if sqrt((x - SPEAKER_XY[0]) ** 2 + (y - SPEAKER_XY[1]) ** 2) < 25:
                continue
            if sqrt((x - HALL_XY[0]) ** 2 + (y - HALL_XY[1]) ** 2) < 8:
                continue
            if any(sqrt((x - gx) ** 2 + (y - gy) ** 2) < 10
                   for gx, gy in corners(GUIDE_XY)):
                continue
            if abs(x) > HALF - POST - 4 and abs(y) > HALF - POST - 4:
                continue
            pts.append((x, y))
    return pts


def speaker_holes():
    pts = [(0.0, 0.0)]
    for ring, n in ((6.5, 6), (13.0, 12)):
        for k in range(n):
            from math import cos, pi, sin
            a = 2 * pi * k / n
            pts.append((ring * cos(a), ring * sin(a)))
    return [(SPEAKER_XY[0] + x, SPEAKER_XY[1] + y) for x, y in pts]


SH_R = R_OUT + 4.0   # tube shoulder radius
SH_T = 3.0


def make_chassis():
    deck = box(-HALF, HALF, -HALF, HALF, DECK_BOT, DECK_TOP)
    for x, y in corners(HALF - POST / 2):
        deck = deck + box(x - POST / 2, x + POST / 2, y - POST / 2,
                          y + POST / 2, DECK_TOP - 0.01, SLAB_BOT)
        deck = deck + cyl(2.5, SLAB_BOT - 0.01, SLAB_BOT + 4, x, y)  # pegs
    # launch tube socket with countersink for the tube shoulder cone
    deck = deck - cyl(R_OUT + 0.25, DECK_BOT - 1, DECK_TOP + 1)
    cs_h = SH_R - R_OUT
    deck = deck - Pos(0, 0, DECK_TOP - cs_h) * Cone(
        R_OUT + 0.25, SH_R + 0.25, cs_h + 0.01, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # M3 inserts for the bottom rivet screws, horizontal from each edge
    for u in (-RIVET_U, RIVET_U):
        z = RIVET_INSET
        L = M3_INSERT_L
        r = M3_INSERT_D / 2
        deck = deck - Pos(u, HALF - L / 2 + 0.5, z) * Rot(90, 0, 0) * Cylinder(r, L + 1)
        deck = deck - Pos(u, -HALF + L / 2 - 0.5, z) * Rot(90, 0, 0) * Cylinder(r, L + 1)
        deck = deck - Pos(HALF - L / 2 + 0.5, u, z) * Rot(0, 90, 0) * Cylinder(r, L + 1)
        deck = deck - Pos(-HALF + L / 2 - 0.5, u, z) * Rot(0, 90, 0) * Cylinder(r, L + 1)
    # M4 inserts for the hit-panel guide screws (from below)
    for x, y in corners(GUIDE_XY):
        deck = deck - cyl(M4_INSERT_D / 2, DECK_BOT - 1, DECK_BOT + M4_INSERT_L, x, y)
    # Hall sensor pocket (flat SS49E, face down) + wire hole
    hx, hy = HALL_XY
    deck = deck - box(hx - 2.3, hx + 2.3, hy - 1.8, hy + 1.8, DECK_BOT - 1, DECK_BOT + 1.8)
    deck = deck - cyl(2.5, DECK_BOT - 1, DECK_TOP + 1, hx, hy + 4.5)
    # speaker seat + grille
    sx, sy = SPEAKER_XY
    deck = deck - cyl(SPEAKER_D / 2, DECK_TOP - 1.5, DECK_TOP + 1, sx, sy)
    for x, y in speaker_holes():
        deck = deck - cyl(1.6, DECK_BOT - 1, DECK_TOP + 1, x, y)
    # general mounting grid for perfboard standoffs / zip ties
    for x, y in mount_grid_points():
        deck = deck - cyl(1.6, DECK_BOT - 1, DECK_TOP + 1, x, y)
    return deck


# --------------------------------------------------------------------------
# hopper: sloped floor slab + upper corner columns (world == print orient.)
# --------------------------------------------------------------------------
PORT = (0.0, R_OUT, Z_C)  # apex of the funnel, on the tube surface (+Y side)


def floor_height(x, y):
    """Analytic floor height (without ridge), used by tests/docs."""
    return Z_C + TAN_SLOPE * sqrt((x - PORT[0]) ** 2 + (y - PORT[1]) ** 2)


def make_hopper():
    top = COL_TOP
    slab = box(-HALF, HALF, -HALF, HALF, SLAB_BOT, top)
    h = S - Z_C
    funnel = Pos(PORT[0], PORT[1], Z_C) * Cone(
        0.01, h / TAN_SLOPE, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    slab = slab - funnel
    # diverter ridge behind the tube so balls split left/right around it
    secs = []
    for y in (-R_OUT + 2, -HALF):
        apex = floor_height(0, y) + RIDGE_H
        tri = Polygon((-RIDGE_W, SLAB_BOT), (RIDGE_W, SLAB_BOT), (0, apex),
                      align=None)
        secs.append(Plane.XZ.offset(-y) * tri)
    slab = slab + loft(secs)
    # upper corner columns (L shaped)
    for sx in (-1, 1):
        for sy in (-1, 1):
            xa, xb = sorted((sx * HALF, sx * (HALF - COL_LEG)))
            ya, yb = sorted((sy * HALF, sy * (HALF - COL_T)))
            slab = slab + box(xa, xb, ya, yb, SLAB_BOT, top)
            xa, xb = sorted((sx * HALF, sx * (HALF - COL_T)))
            ya, yb = sorted((sy * HALF, sy * (HALF - COL_LEG)))
            slab = slab + box(xa, xb, ya, yb, SLAB_BOT, top)
    # trim anything that poked above the column tops
    slab = slab & box(-HALF, HALF, -HALF, HALF, SLAB_BOT, top)
    # tube hole + anti-rotation slot for the tube rib (-Y)
    slab = slab - cyl(R_OUT + 0.25, SLAB_BOT - 1, top + 1)
    slab = slab - box(-2.3, 2.3, -R_OUT - 2.5, -R_OUT + 0.5, SLAB_BOT - 1, top + 1)
    # alignment holes onto the lower post pegs
    for x, y in corners(HALF - POST / 2):
        slab = slab - cyl(2.7, SLAB_BOT - 1, SLAB_BOT + 5, x, y)
    # M3 inserts for the top rivet screws
    z = RIVET_Z[1]
    L, r = M3_INSERT_L, M3_INSERT_D / 2
    for u in (-RIVET_U, RIVET_U):
        slab = slab - Pos(u, HALF - L / 2 + 0.5, z) * Rot(90, 0, 0) * Cylinder(r, L + 1)
        slab = slab - Pos(u, -HALF + L / 2 - 0.5, z) * Rot(90, 0, 0) * Cylinder(r, L + 1)
        slab = slab - Pos(HALF - L / 2 + 0.5, u, z) * Rot(0, 90, 0) * Cylinder(r, L + 1)
        slab = slab - Pos(-HALF + L / 2 - 0.5, u, z) * Rot(0, 90, 0) * Cylinder(r, L + 1)
    # lid magnets
    for x, y in corners(MAGNET_XY):
        slab = slab - cyl(MAGNET_D / 2, top - MAGNET_H, top + 1, x, y)
    # wire channel for the LED ring, down into the electronics bay
    slab = slab - cyl(4.0, SLAB_BOT - 1, top + 1, 56.0, -30.0)
    return slab


# --------------------------------------------------------------------------
# launch tube (world == print orientation)
# --------------------------------------------------------------------------
def make_tube():
    t = cyl(R_OUT, TUBE_BOT, S)
    cs_h = SH_R - R_OUT
    t = t + Pos(0, 0, DECK_TOP - cs_h) * Cone(
        R_OUT, SH_R, cs_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    t = t + cyl(SH_R, DECK_TOP, DECK_TOP + SH_T)
    # anti-rotation rib (-Y side), sits on the shoulder
    t = t + box(-2.0, 2.0, -R_OUT - 2.2, -R_OUT + 0.5, DECK_TOP + SH_T - 0.01, Z_C)
    t = t - cyl(R_IN, TUBE_BOT - 1, S + 1)
    # entry window facing +Y, with a 45 deg peaked roof (prints w/o support)
    t = t - box(-WIN_W / 2, WIN_W / 2, 0, R_OUT + 3, WIN_BOT, WIN_BOT + WIN_W)
    d = WIN_W / sqrt(2)
    t = t - Pos(0, (R_OUT + 3) / 2, WIN_BOT + WIN_W) * Rot(0, 45, 0) * Box(d, R_OUT + 3, d)
    # soften the hatch edge
    top_edges = t.edges().filter_by(Axis.Z, reverse=True).group_by(Axis.Z)[-1]
    try:
        t = chamfer(top_edges, 0.8)
    except Exception:  # noqa: BLE001 - cosmetic only
        pass
    return t


# --------------------------------------------------------------------------
# moving parts
# --------------------------------------------------------------------------
def make_piston():
    """World position at rest (standing on the hit panel)."""
    r = R_IN - PISTON_CLEAR
    p = cyl(FLANGE_D / 2, PANEL_TOP, FLANGE_TOP)
    p = p + cyl(r, FLANGE_TOP - 0.01, PISTON_TOP)
    dish = 2.5
    p = p - Pos(0, 0, PISTON_TOP + PAYLOAD_D / 2 - dish) * Sphere(PAYLOAD_D / 2)
    # hollow core, 45 deg conical roof so it prints without support
    rc = r - 3.0
    roof = PISTON_TOP - dish - 3.0
    p = p - cyl(rc, PANEL_TOP - 1, roof - rc)
    p = p - Pos(0, 0, roof - rc - 0.01) * Cone(
        rc, 0.01, rc, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return p


def make_hit_panel():
    """World position at rest."""
    half = PANEL_SIZE / 2
    p = box(-half, half, -half, half, PANEL_BOT, PANEL_TOP)
    p = p.fillet(3.0, p.edges().filter_by(Axis.Z))
    for x, y in corners(GUIDE_XY):
        p = p + cyl(7.0, PANEL_TOP - 0.01, BOSS_TOP, x, y)
        p = p - cyl(SLEEVE_OD / 2 + 0.35, PANEL_BOT - 1, BOSS_TOP + 1, x, y)
        p = p - cyl(WASHER_D / 2 + 0.4, PANEL_BOT - 1, WASHER_TOP, x, y)
    hx, hy = HALL_XY
    post_top = DECK_BOT - STROKE - HALL_GAP
    p = p + cyl(5.0, PANEL_TOP - 0.01, post_top, hx, hy)
    p = p - cyl(MAGNET_D / 2, post_top - MAGNET_H, post_top + 1, hx, hy)
    for x, y in speaker_holes():
        p = p - cyl(1.6, PANEL_BOT - 1, PANEL_TOP + 1, x, y)
    return p


def make_sleeve():
    return cyl(SLEEVE_OD / 2, 0, SLEEVE_L) - cyl(SLEEVE_ID / 2, -1, SLEEVE_L + 1)


# --------------------------------------------------------------------------
# small parts
# --------------------------------------------------------------------------
def make_rivet_cap():
    """Print orientation: visible face down. Peg pushes into the rivet bore."""
    cap = cyl(RIVET_CAP_D / 2, 0, 1.8)
    cap = chamfer(cap.edges().group_by(Axis.Z)[0], 0.8)
    peg_h = T - RIVET_FLOOR - 1.65 - 0.2  # leaves room for the M3 button head
    return cap + cyl(RIVET_PEG_D / 2, 1.79, 1.8 + peg_h)


def make_led_collar():
    """Holds a 24-LED WS2812 ring (~66 OD / ~52 ID) around the tube top.

    Print orientation: disc down, sleeve up. World: disc bottom at
    LED_COLLAR_Z.
    """
    ri = R_OUT + 0.15
    c = cyl(35.0, 0, 2.5) + cyl(ri + 2.2, 0, 12)
    c = c - cyl(ri, -1, 13)
    c = c - box(-2, 2, ri - 1, 36, -1, 3.5)            # wire slot
    c = c - Pos(0, -(ri + 1), 8) * Rot(90, 0, 0) * Cylinder(1.25, 5)  # M3 set screw
    return c


def make_capsule():
    """Printable two-part capsule. Returns (bottom_with_lip, top).

    Both print rim-down. Outside diameter is PAYLOAD_D - 0.5.
    """
    r = (PAYLOAD_D - 0.5) / 2
    w = 1.6
    lip_h, lip_t, fit = 2.5, 0.8, 0.15
    shell = Sphere(r) - Sphere(r - w)
    upper = shell & box(-r - 1, r + 1, -r - 1, r + 1, 0, r + 1)
    # bottom half: male lip below the rim (printed first, on the bed)
    bottom = Pos(0, 0, lip_h) * upper
    lip = cyl(r - w + lip_t, 0, lip_h + 0.5) - cyl(r - w, -1, lip_h + 1)
    bottom = bottom + lip
    # top half: female recess inside the rim
    top = upper - cyl(r - w + lip_t + fit, -1, lip_h + fit)
    return bottom, top


# --------------------------------------------------------------------------
# assembly
# --------------------------------------------------------------------------
COLORS = {
    "body": Color(0.98, 0.72, 0.10),
    "glyph": Color(0.98, 0.98, 0.95),
    "shadow": Color(0.25, 0.14, 0.08),
    "rivet": Color(0.25, 0.14, 0.08),
    "inner": Color(0.55, 0.60, 0.68),
    "tube": Color(0.85, 0.92, 0.95),
    "moving": Color(0.90, 0.35, 0.25),
    "ball": Color(0.95, 0.25, 0.55),
}

PANEL_PLACEMENT = {
    "back": Rot(0, 0, 0),
    "right": Rot(0, 0, -90),
    "front": Rot(0, 0, 180),
    "left": Rot(0, 0, 90),
}


def place_side(shape, side):
    return PANEL_PLACEMENT[side] * (Pos(0, S / 2, 0) * Rot(90, 0, 0) * shape)


def place_lid(shape):
    return Pos(0, 0, S) * Rot(180, 0, 0) * shape


def assembly(lift=0.0, with_balls=True):
    """List of (name, shape, color_key, moving) in world coordinates.

    lift: how far the hit panel / piston are raised (0..STROKE) for checks.
    """
    parts = []
    glyph, shadow = make_glyph(), make_shadow()
    for side, kind in (("front", "plain"), ("left", "plain"),
                       ("back", "back"), ("right", "right")):
        parts.append((f"panel_{side}", place_side(make_side_panel(kind), side), "body", False))
        parts.append((f"glyph_{side}", place_side(glyph, side), "glyph", False))
        parts.append((f"shadow_{side}", place_side(shadow, side), "shadow", False))
    parts.append(("lid", place_lid(make_lid()), "body", False))
    parts.append(("chassis", make_chassis(), "inner", False))
    parts.append(("hopper", make_hopper(), "inner", False))
    parts.append(("tube", make_tube(), "tube", False))
    parts.append(("led_collar", Pos(0, 0, LED_COLLAR_Z) * make_led_collar(), "inner", False))
    for x, y in corners(GUIDE_XY):
        parts.append((f"sleeve_{x:+.0f}_{y:+.0f}",
                      Pos(x, y, WASHER_TOP) * make_sleeve(), "inner", False))
    parts.append(("hit_panel", Pos(0, 0, lift) * make_hit_panel(), "moving", True))
    parts.append(("piston", Pos(0, 0, lift) * make_piston(), "moving", True))
    if with_balls:
        parts.append(("ball_chamber", Pos(0, 0, chamber_ball_z() + lift) * Sphere(PAYLOAD_D / 2),
                      "ball", True))
    return parts


def chamber_ball_z():
    """Centre height of the ball resting in the piston dish."""
    dish = 2.5
    return PISTON_TOP + PAYLOAD_D / 2 - dish + 0.05


# printable parts: name -> (shape, qty, colour key, note)
def printable_parts():
    cb, ct = make_capsule()
    return {
        "panel_front_left": (make_side_panel("plain"), 2, "body", "front + left walls"),
        "panel_back": (make_side_panel("back"), 1, "body", "back wall (wall-mount holes)"),
        "panel_right": (make_side_panel("right"), 1, "body", "right wall (USB-C jack)"),
        "panel_glyph": (make_glyph(), 4, "glyph", "'?' inlay, print WITH a panel"),
        "panel_shadow": (make_shadow(), 4, "shadow", "shadow inlay, print WITH a panel"),
        "lid": (make_lid(), 1, "body", "removable top"),
        "chassis": (make_chassis(), 1, "inner", "deck + lower posts"),
        "hopper": (make_hopper(), 1, "inner", "sloped floor + upper columns"),
        "tube": (make_tube(), 1, "tube", "launch tube"),
        "piston": (make_piston(), 1, "inner", "launch piston"),
        "hit_panel": (make_hit_panel(), 1, "body", "bottom panel you hit"),
        "sleeve": (make_sleeve(), 4, "inner", "guide sleeves"),
        "rivet_cap": (make_rivet_cap(), 20, "rivet", "rivet caps (16 sides + 4 lid)"),
        "led_collar": (make_led_collar(), 1, "inner", "LED ring holder"),
        "capsule_bottom": (cb, 1, "ball", "optional printable capsule"),
        "capsule_top": (ct, 1, "ball", "optional printable capsule"),
    }
