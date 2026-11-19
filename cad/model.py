"""Parametric model of the mystery block (build123d).

Each `make_*` function returns one part in world position unless noted;
`printable_parts()` gives them in print orientation. `assembly()` places
every part in world coordinates for renders and fit tests.

How it works (lift):
  hit panel  -> floats on 4 guide screws; a magnet tells the Hall sensor
                under the deck that someone bonked it (4 mm of travel)
  car        -> a tall cup in the tube carries one capsule. A GT2 belt
                (N20 motor pulley below, idler above) pulls it up by an arm
                that runs in a slot at the front of the tube, until the
                capsule sits on top of the lid. It waits, then goes back down.
  housing    -> encloses the belt next to the tube so capsules can't touch
                it; holds the idler and the top/bottom Hall sensors
  hopper     -> sloped floor rolls the next capsule through the tube window
                onto the car once it is down. While the car is away its side
                keeps the window shut, so exactly one capsule loads.
"""
from __future__ import annotations

from math import sqrt

from build123d import (Align, Axis, Box, Color, Cone, Cylinder,
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
            if sqrt(x * x + y * y) < R_OUT + 8:
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
            if abs(x) < HOUSING_HX + 6 and y < -R_OUT:      # belt housing + arm slot
                continue
            if 0 < x < MOTOR_X0 + MOTOR_L + 6 and BELT_Y - 12 < y < BELT_Y + 12:  # motor
                continue
            pts.append((x, y))
    return pts


def speaker_holes():
    from math import cos, pi, sin
    pts = [(0.0, 0.0)]
    for ring, n in ((6.5, 6), (13.0, 12)):
        for k in range(n):
            a = 2 * pi * k / n
            pts.append((ring * cos(a), ring * sin(a)))
    return [(SPEAKER_XY[0] + x, SPEAKER_XY[1] + y) for x, y in pts]


# --------------------------------------------------------------------------
# lift: car, belt housing (world position)
# --------------------------------------------------------------------------
def make_car():
    """The lift car in its down (loading) position. It is tall so its side
    keeps the hopper window shut while it is up. Prints upright, dish on top."""
    r = CAR_R
    top, bot = CAR_TOP_DOWN, CAR_BOT_DOWN
    c = cyl(r, bot, top)
    c = c - Pos(0, 0, top + PAYLOAD_D / 2 - DISH) * Sphere(PAYLOAD_D / 2)
    # light: hollow, open at the bottom, 45 deg roof under the dish
    rc = r - 2.0
    roof = top - DISH - 2.0
    c = c - cyl(rc, bot - 1, roof - rc)
    c = c - Pos(0, 0, roof - rc - 0.01) * Cone(
        rc, 0.01, rc, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # arm out of the front slot to the belt, with a 45 deg gusset underneath
    za = ARM_MIN
    y_in = -r + 1.5
    y_out = STRAND_Y + 2.0
    arm = box(-ARM_W / 2, ARM_W / 2, y_out, y_in, za - 3.0, za + 3.0)
    L = y_in - y_out
    gus = Plane.YZ * Polygon((y_in, za - 2.9), (y_out + 2.0, za - 2.9),
                             (y_in, za - 2.9 - (L - 2.0)), align=None)
    arm = arm + extrude(gus, ARM_W / 2, both=True)
    # belt clamp: both belt ends go into the 1.8 mm slot (one from above, one
    # from below) and are pinched by an M3 screw through the clamp
    cl = box(-5.5, 5.5, STRAND_Y - 3.5, STRAND_Y + 2.5, za - CLAMP_H / 2, za + CLAMP_H / 2)
    cl = cl - box(-BELT_W / 2 - 0.3, BELT_W / 2 + 0.3, STRAND_Y - 0.9, STRAND_Y + 0.9,
                  za - CLAMP_H, za + CLAMP_H)
    cl = cl - Pos(0, STRAND_Y + 1.6, za) * Rot(0, 90, 0) * Cylinder(1.4, 12)  # pinch screw
    # magnet for the top/bottom lift sensors, in the +X face
    cl = cl - Pos(5.5 - MAGNET_H / 2 + 0.01, STRAND_Y - 2.2, za) * Rot(0, 90, 0) * Cylinder(MAGNET_D / 2, MAGNET_H)
    return c + arm + cl


def place_car(lift, shape=None):
    """Car raised by `lift` mm (0 = down, LIFT_TRAVEL = up)."""
    shape = shape if shape is not None else make_car()
    return Pos(0, 0, lift) * shape


def make_housing():
    """Belt housing: keeps capsules off the belt. Stands on the deck in front
    of the tube, goes up through the hopper floor, carries the idler axle
    and the two lift sensors. World position == print orientation."""
    hx, y0 = HOUSING_HX, HOUSING_Y0
    w = 1.6
    low_top = ARM_MAX + CLAMP_H / 2 + 2.0          # arm channel top
    top = IDLER_Z + IDLER_FLANGE_R + 1.5
    h = box(-hx, hx, y0, -R_OUT + 1.0, DECK_TOP, low_top)
    h = h + box(-hx, hx, y0, HOUSING_UPPER_Y, low_top - 0.01, top)
    h = h - cyl(R_OUT + 0.25, DECK_TOP - 1, low_top + 1)
    h = h - box(-hx + w, hx - w, y0 + w, -R_OUT + 2, DECK_TOP - 1, low_top)
    h = h - box(-hx + w, hx - w, y0 + w, HOUSING_UPPER_Y - w, DECK_TOP - 1, top - w)
    # motor pulley hub comes in through the +X wall at the bottom
    h = h - box(hx - w - 1, hx + 1, BELT_Y - 8.0, BELT_Y + 8.0, DECK_TOP - 1, MOTOR_Z + 8.0)
    # idler axle (M3 along X), slotted 3 mm so the belt can be tensioned
    h = h - box(-hx - 1, hx + 1, BELT_Y - 1.65, BELT_Y + 1.65, IDLER_Z - 2.0, IDLER_Z + 1.0)
    # clear the chassis tube socket ring
    h = h - cyl(R_OUT + 3.4, DECK_TOP - 1, DECK_TOP + 4.5)
    # open over the idler so its flanges clear the walls (still far too
    # narrow for a capsule), and wide enough for the belt clamp, so the
    # housing can be lowered over the car during assembly
    h = h - box(-BELT_W / 2 - 3.0, BELT_W / 2 + 3.0, BELT_Y - IDLER_FLANGE_R - 1.0,
                HOUSING_UPPER_Y + 1, IDLER_Z - IDLER_FLANGE_R - 1.0, top + 1)
    # foot tab on the front (-Y) side with two M3 holes (self-tapping
    # screws from under the deck)
    h = h + box(-hx, hx, y0 - 7.0, y0 + 0.01, DECK_TOP, DECK_TOP + 4)
    for x, y in housing_screw_points():
        h = h - cyl(1.25, DECK_TOP - 1, DECK_TOP + 3.5, x, y)
    # sensor seats on the +X wall (SS49E flat, face against the wall)
    for z in (ARM_MIN, ARM_MAX):
        h = h + box(hx - 0.01, hx + 2.6, STRAND_Y - 6.0, STRAND_Y + 1.4, z - 4.5, z + 4.5)
        h = h - box(hx + 0.4, hx + 2.0, STRAND_Y - 4.5, STRAND_Y + 0.1, z - 2.0, z + 6.0)
    return h


def housing_screw_points():
    return [(sx * 5.0, HOUSING_Y0 - 3.5) for sx in (-1, 1)]


def lift_sensor_points():
    """Where the bottom and top lift sensors sit (x, y, z)."""
    return [(HOUSING_HX + 1.2, STRAND_Y - 2.2, z) for z in (ARM_MIN, ARM_MAX)]


def housing_footprint(clear=0.0):
    return box(-HOUSING_HX - clear, HOUSING_HX + clear, HOUSING_Y0 - 7.0 - clear, -R_OUT + 1.0,
               DECK_TOP - 1, S)


# --------------------------------------------------------------------------
# chassis: deck + lower corner posts + lift mounts
# (world position == print orientation)
# --------------------------------------------------------------------------
def make_chassis():
    deck = box(-HALF, HALF, -HALF, HALF, DECK_BOT, DECK_TOP)
    for x, y in corners(HALF - POST / 2):
        deck = deck + box(x - POST / 2, x + POST / 2, y - POST / 2,
                          y + POST / 2, DECK_TOP - 0.01, SLAB_BOT)
        deck = deck + cyl(2.5, SLAB_BOT - 0.01, SLAB_BOT + 4, x, y)  # pegs
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

    # ---- lift mounts ---------------------------------------------------------
    # tube socket ring + a hole the car drops through
    deck = deck + (cyl(R_OUT + 3.0, DECK_TOP - 0.01, DECK_TOP + 4.0)
                   - cyl(R_OUT + 0.25, DECK_TOP, DECK_TOP + 5))
    deck = deck - cyl(CAR_R + 0.8, DECK_BOT - 1, DECK_TOP + 1)
    # slot for the car arm's gusset, open toward the housing
    deck = deck - box(-ARM_W / 2 - 0.6, ARM_W / 2 + 0.6, STRAND_Y, 0, DECK_BOT + 1.0, DECK_TOP + 5)
    # pocket for the motor pulley (flanges dip below the deck top)
    deck = deck - box(-HOUSING_HX + 1.6, HOUSING_HX - 1.0, BELT_Y - PULLEY_FLANGE_R - 1,
                      BELT_Y + PULLEY_FLANGE_R + 1, MOTOR_Z - PULLEY_FLANGE_R - 1.0, DECK_TOP + 1)
    # housing screw holes
    for x, y in housing_screw_points():
        deck = deck - cyl(1.7, DECK_BOT - 1, DECK_TOP + 1, x, y)
    # N20 motor cradle: U-channel along +X, shaft toward the pulley (-X)
    mx0, mx1 = MOTOR_X0, MOTOR_X0 + MOTOR_L
    my0, my1 = BELT_Y - MOTOR_W / 2 - 0.2, BELT_Y + MOTOR_W / 2 + 0.2
    mz0 = MOTOR_Z - MOTOR_H / 2 - 0.2
    deck = deck - box(mx0 - 1, mx1 + 1, my0, my1, mz0, DECK_TOP + 1)   # body pocket
    cradle = box(mx0, mx1, my0 - 2.5, my1 + 2.5, DECK_TOP - 0.01, MOTOR_Z + 2)
    cradle = cradle - box(mx0 - 1, mx1 + 1, my0, my1, mz0, MOTOR_Z + 3)
    for xx in (mx0 + 8, mx1 - 8):  # zip-tie slots over the motor
        cradle = cradle - box(xx - 2, xx + 2, my0 - 3, my1 + 3, mz0 - 0.01, MOTOR_Z + 3)
        deck = deck - box(xx - 2, xx + 2, my0 - 3.5, my0 - 1.0, DECK_BOT - 1, DECK_TOP + 1)
        deck = deck - box(xx - 2, xx + 2, my1 + 1.0, my1 + 3.5, DECK_BOT - 1, DECK_TOP + 1)
    deck = deck + cradle
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
    slab = slab & box(-HALF, HALF, -HALF, HALF, SLAB_BOT, top)
    # tube hole + anti-rotation slot for the tube rib (+X)
    slab = slab - cyl(R_OUT + 0.25, SLAB_BOT - 1, top + 1)
    slab = slab - box(R_OUT - 0.5, R_OUT + 2.5, -2.3, 2.3, SLAB_BOT - 1, top + 1)
    # the belt housing passes up through the floor in front of the tube
    slab = slab - housing_footprint(0.4)
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
    for x, y in corners(MAGNET_XY):
        slab = slab - cyl(MAGNET_D / 2, top - MAGNET_H, top + 1, x, y)
    # wire channel for the LED ring, down into the electronics bay
    slab = slab - cyl(4.0, SLAB_BOT - 1, top + 1, 56.0, -30.0)
    return slab


# --------------------------------------------------------------------------
# lift tube (world == print orientation)
# --------------------------------------------------------------------------
TUBE_SLOT_TOP = ARM_MAX + 3.0 + 3.0     # arm top at full lift + margin


def make_tube():
    t = cyl(R_OUT, TUBE_BOT, S)
    # anti-rotation rib (+X side) for the hopper slot
    t = t + box(R_OUT - 0.5, R_OUT + 2.2, -2.0, 2.0, SLAB_BOT - 6.0, Z_C)
    t = t - cyl(R_IN, TUBE_BOT - 1, S + 1)
    # front (-Y) slot for the car arm, open at the bottom so the car slides in
    t = t - box(-ARM_W / 2 - 0.6, ARM_W / 2 + 0.6, -R_OUT - 1, 0, TUBE_BOT - 1, TUBE_SLOT_TOP)
    # entry window facing +Y, with a 45 deg peaked roof (prints w/o support)
    t = t - box(-WIN_W / 2, WIN_W / 2, 0, R_OUT + 3, WIN_BOT, WIN_BOT + WIN_W)
    d = WIN_W / sqrt(2)
    t = t - Pos(0, (R_OUT + 3) / 2, WIN_BOT + WIN_W) * Rot(0, 45, 0) * Box(d, R_OUT + 3, d)
    top_edges = t.edges().filter_by(Axis.Z, reverse=True).group_by(Axis.Z)[-1]
    try:
        t = chamfer(top_edges, 0.8)
    except Exception:  # noqa: BLE001 - cosmetic only
        pass
    return t


# --------------------------------------------------------------------------
# moving parts
# --------------------------------------------------------------------------
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
    "motor": Color(0.75, 0.75, 0.78),
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


def motor_dummy():
    """Stand-in N20 gear motor + shaft along X (not printed)."""
    body = box(MOTOR_X0, MOTOR_X0 + MOTOR_L, BELT_Y - MOTOR_W / 2, BELT_Y + MOTOR_W / 2,
               MOTOR_Z - MOTOR_H / 2, MOTOR_Z + MOTOR_H / 2)
    shaft = Pos(MOTOR_X0 / 2, BELT_Y, MOTOR_Z) * Rot(0, 90, 0) * Cylinder(1.5, MOTOR_X0 + 1)
    return body + shaft


def _pulley(r_flange, z):
    hub = Pos(0, BELT_Y, z) * Rot(0, 90, 0) * Cylinder(PULLEY_PD / 2 - 0.75, BELT_W + 1)
    for sx in (-1, 1):
        hub = hub + Pos(sx * (BELT_W / 2 + 1.0), BELT_Y, z) * Rot(0, 90, 0) * Cylinder(r_flange, 1.0)
    return hub - Pos(0, BELT_Y, z) * Rot(0, 90, 0) * Cylinder(1.55, 20)  # 3 mm bore


def belt_dummy():
    """GT2 pulley, idler and the belt loop (bought parts, not printed).
    The belt is drawn on its pitch line; it moves with the car in reality."""
    p = _pulley(PULLEY_FLANGE_R, MOTOR_Z) + _pulley(IDLER_FLANGE_R, IDLER_Z)
    r = PULLEY_PD / 2
    hw, ht = BELT_W / 2, BELT_T / 2
    belt = box(-hw, hw, BELT_Y - r - ht, BELT_Y - r + ht, MOTOR_Z, IDLER_Z)
    belt = belt + box(-hw, hw, BELT_Y + r - ht, BELT_Y + r + ht, MOTOR_Z, IDLER_Z)
    for z, up in ((MOTOR_Z, False), (IDLER_Z, True)):
        ring = (Pos(0, BELT_Y, z) * Rot(0, 90, 0) * Cylinder(r + ht, BELT_W)
                - Pos(0, BELT_Y, z) * Rot(0, 90, 0) * Cylinder(r - ht, BELT_W + 1))
        half = box(-hw - 1, hw + 1, -HALF, HALF, z, z + r + 2) if up else \
            box(-hw - 1, hw + 1, -HALF, HALF, z - r - 2, z)
        belt = belt + (ring & half)
    return p, belt


def chamber_ball_z(lift=0.0):
    """Centre height of the capsule resting in the car dish."""
    return CAR_TOP_DOWN + lift + PAYLOAD_D / 2 - DISH + 0.05


def assembly(lift=0.0, panel_lift=0.0, with_balls=True):
    """List of (name, shape, color_key, moving) in world coordinates.

    lift: car height above its loading position (0 = down, LIFT_TRAVEL =
    up, capsule presented above the lid). panel_lift: hit panel.
    """
    if lift == "down":
        lift = 0.0
    elif lift == "up":
        lift = LIFT_TRAVEL
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
    parts.append(("housing", make_housing(), "inner", False))
    parts.append(("motor", motor_dummy(), "motor", False))
    pulleys, belt = belt_dummy()
    parts.append(("pulleys", pulleys, "motor", False))
    parts.append(("belt", belt, "shadow", False))
    parts.append(("led_collar", Pos(0, 0, LED_COLLAR_Z) * make_led_collar(), "inner", False))
    for x, y in corners(GUIDE_XY):
        parts.append((f"sleeve_{x:+.0f}_{y:+.0f}",
                      Pos(x, y, WASHER_TOP) * make_sleeve(), "inner", False))
    parts.append(("hit_panel", Pos(0, 0, panel_lift) * make_hit_panel(), "moving", True))
    parts.append(("car", place_car(lift), "moving", True))
    if with_balls:
        parts.append(("ball_chamber", Pos(0, 0, chamber_ball_z(lift)) * Sphere(PAYLOAD_D / 2),
                      "ball", True))
    return parts


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
        "chassis": (make_chassis(), 1, "inner", "deck, posts, tube socket, motor cradle"),
        "housing": (make_housing(), 1, "inner", "belt housing, idler + lift sensor mounts"),
        "hopper": (make_hopper(), 1, "inner", "sloped floor + upper columns"),
        "tube": (make_tube(), 1, "tube", "lift tube"),
        "car": (make_car(), 1, "inner", "lift car (prints upright)"),
        "hit_panel": (make_hit_panel(), 1, "body", "bottom panel you hit"),
        "sleeve": (make_sleeve(), 4, "inner", "guide sleeves"),
        "rivet_cap": (make_rivet_cap(), 20, "rivet", "rivet caps (16 sides + 4 lid)"),
        "led_collar": (make_led_collar(), 1, "inner", "LED ring holder"),
        "capsule_bottom": (cb, 1, "ball", "optional printable capsule"),
        "capsule_top": (ct, 1, "ball", "optional printable capsule"),
    }
