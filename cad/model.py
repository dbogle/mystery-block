"""Parametric model of the candy-launching mystery block (build123d).

Each `make_*` function returns one part in world position unless noted;
`printable_parts()` gives them in print orientation. `assembly()` places
every part in world coordinates for renders and fit tests.

How it works (motorised launcher):
  hit panel  -> floats on 4 guide screws; a magnet tells the Hall sensor
                under the deck that someone bonked it (4 mm of travel)
  cam        -> an N20 gear motor turns a snail cam that has pushed the lever
                down against a spring and is parked just before its drop-off
  lever      -> on a hit the cam turns ~40 deg more, the lever is released,
                the spring snaps its tip up into the piston
  piston     -> rises LIFT + COAST, stops on the tower lip; the ball keeps
                going up the tube and out of the hatch in the lid
  hopper     -> sloped floor rolls the next ball through the tube window
                onto the piston; the cam re-cocks and parks (~1 s)
"""
from __future__ import annotations

from math import cos, degrees, radians, sin, sqrt

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
def tower_boss_points():
    r = TOWER_BOSS_R
    return [(r, 0.0), (0.0, r), (0.0, -r)]


def mount_grid_points():
    """3.2 mm holes on a 10 mm grid wherever the deck is free."""
    pts = []
    for i in range(-7, 8):
        for j in range(-7, 8):
            x, y = i * 10.0, j * 10.0
            if max(abs(x), abs(y)) > HALF - 12:
                continue
            if sqrt(x * x + y * y) < TOWER_BOSS_R + 6:
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
            if x < -25 and -16 < y < MOTOR_L + 12:   # launcher area
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
# launcher geometry (shared by parts, assembly and tests)
# --------------------------------------------------------------------------
def _solve(f, lo=-0.6, hi=0.6):
    for _ in range(80):
        mid = (lo + hi) / 2
        if f(mid) > 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def lever_top_z(x, theta):
    """World Z of the lever's top face at world X for lever angle theta (rad)."""
    return PIV_Z + LEVER_T / 2 * cos(theta) + (x - PIV_X) * sin(theta)


THETA_UP = _solve(lambda t: lever_top_z(TIP_X, t) - TIP_UP)
THETA_COCKED = _solve(lambda t: lever_top_z(TIP_X, t) - (TIP_UP - TIP_STROKE))


def _dist_to_lever_top(px, pz, theta):
    """Perpendicular distance from a point above the lever to its top face."""
    nx, nz = -sin(theta), cos(theta)
    return (px - PIV_X) * nx + (pz - PIV_Z) * nz - LEVER_T / 2


NOSE_D = CAM_X - PIV_X  # follower nose position along the lever


def nose_center(theta):
    """World (x, z) of the follower nose (a half-round ridge on the lever top)."""
    lx, lz = NOSE_D, LEVER_T / 2
    return (PIV_X + lx * cos(theta) - lz * sin(theta),
            PIV_Z + lx * sin(theta) + lz * cos(theta))


# cam centre: CAM_R0 + CAM_CLR above the nose when released
_nu = nose_center(THETA_UP)
CAM_Z = _nu[1] + NOSE_R + CAM_R0 + CAM_CLR
_nc = nose_center(THETA_COCKED)
CAM_R1 = sqrt((CAM_X - _nc[0]) ** 2 + (CAM_Z - _nc[1]) ** 2) - NOSE_R
CAM_DROP = CAM_RISE + CAM_DWELL            # profile angle of the drop
# Cam rotation (deg about +Y). The profile point at angle psi is at the
# bottom (touching the nose) when beta = psi - 270.
MAG_TOP_BETA = CAM_DROP - 270.0 - 12.0     # magnet passes its sensor here
CAM_MAG_ANGLE = 90.0 + MAG_TOP_BETA        # so the sensor sits at the top
BETA_COCKED = MAG_TOP_BETA - 22.0          # where the motor parks (sensor onset)
BETA_FIRED = CAM_DROP - 270.0 + 30.0
MOTOR_Y0 = LEVER_W / 2 + 1.0        # gearbox face (shaft points -Y)
CAM_SENSOR = (CAM_X, -(CAM_W / 2 + 1.2), CAM_Z + CAM_MAG_R)


def lever_clear(pts, theta):
    """True if no cam profile point (world x, z) is inside the lever at angle
    theta. Models the parts of the lever the cam can reach: the one-sided
    follower nose (quarter round on the tip side, vertical face toward the
    pivot so the cam corner drops off it at once), the relieved top around it
    and the full-height top further out."""
    c, s_ = cos(theta), sin(theta)
    top = LEVER_T / 2
    for px, pz in pts:
        dx, dz = px - PIV_X, pz - PIV_Z
        u, w = dx * c + dz * s_, -dx * s_ + dz * c      # lever frame
        if u > TIP_X - PIV_X:
            continue
        if NOSE_D <= u <= NOSE_D + NOSE_R:              # nose
            if w < top or (u - NOSE_D) ** 2 + (w - top) ** 2 < NOSE_R ** 2:
                return False
            continue
        h = top - LEVER_RELIEF if abs(u - NOSE_D) < RELIEF_W else top
        if w < h:
            return False
    return True


def cam_points(beta, n=1440):
    """Cam profile (world x, z) at rotation beta (deg), plus the drop corner."""
    pts = []
    for i in range(n):
        psi = 360.0 * i / n
        r = cam_radius(psi)
        a = radians(psi - beta)  # rotation about +Y turns the XZ profile by -beta
        pts.append((CAM_X + r * cos(a), CAM_Z + r * sin(a)))
    a = radians(CAM_DROP - beta)
    pts.append((CAM_X + CAM_R1 * cos(a), CAM_Z + CAM_R1 * sin(a)))
    return pts


def lever_angle_for_cam(beta):
    """Highest lever angle (rad) the cam allows at rotation beta (deg), capped
    by the up-stop. The spring holds the lever there."""
    pts = cam_points(beta)
    lo, hi = THETA_COCKED - 0.1, THETA_UP
    if lever_clear(pts, hi):
        return hi
    for _ in range(36):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if lever_clear(pts, mid) else (lo, mid)
    return lo


def cam_radius(psi):
    psi %= 360.0
    if psi < CAM_RISE:
        return CAM_R0 + (CAM_R1 - CAM_R0) * psi / CAM_RISE
    if psi < CAM_DROP:
        return CAM_R1
    return CAM_R0


# --------------------------------------------------------------------------
# chassis: deck + lower corner posts + launcher mounts
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

    # ---- launcher mounts ----------------------------------------------------
    # tower screws (M3 x 20 from the top, nyloc nut under the deck)
    for x, y in tower_boss_points():
        deck = deck - cyl(1.65, DECK_BOT - 1, DECK_TOP + 1, x, y)
    # piston seat ribs (0, 120, 240 deg; the lever comes in from 180). They sit
    # inside the tower ring and also locate it.
    for a in (0, 120, 240):
        rib = box(FLANGE_D / 2 - 2.0, TOWER_RI - 0.9, -4.0, 4.0, DECK_TOP - 0.01, SEAT_Z)
        deck = deck + Rot(0, 0, a) * rib
    # lever pivot posts with a horizontal M3 axle hole
    gap = LEVER_W / 2 + 0.6
    for sy in (-1, 1):
        y0, y1 = sorted((sy * gap, sy * (gap + 6.0)))
        post = box(PIV_X - 4, PIV_X + 4, y0, y1, DECK_TOP - 0.01, PIV_Z + 6)
        post = post.fillet(3.9, post.edges().filter_by(Axis.Y).group_by(Axis.Z)[-1])
        deck = deck + post
    deck = deck - Pos(PIV_X, 0, PIV_Z) * Rot(90, 0, 0) * Cylinder(1.7, 2 * gap + 14)
    # spring post under the cam
    deck = deck + cyl(2.8, DECK_TOP - 0.01, DECK_TOP + 4, SPRING_X, 0)
    # N20 motor cradle: U-channel along +Y, shaft toward the cam (-Y)
    mx0, mx1 = CAM_X - MOTOR_W / 2 - 0.2, CAM_X + MOTOR_W / 2 + 0.2
    my0, my1 = MOTOR_Y0, MOTOR_Y0 + MOTOR_L
    mz0 = CAM_Z - MOTOR_H / 2 - 0.2
    cradle = box(mx0 - 2.5, mx1 + 2.5, my0, my1, DECK_TOP - 0.01, CAM_Z + 2)
    cradle = cradle - box(mx0, mx1, my0 - 1, my1 + 1, mz0, CAM_Z + 3)
    for yy in (my0 + 9, my1 - 9):  # zip-tie slots under the motor
        cradle = cradle - box(mx0 - 3, mx1 + 3, yy - 2, yy + 2, mz0 - 3.5, mz0 - 1.5)
    deck = deck + cradle
    # cam-position Hall sensor post (sensor glued on its +Y face)
    sx_, sy_, sz_ = CAM_SENSOR
    spost = box(sx_ - 3.5, sx_ + 3.5, sy_ - 4.0, sy_ - 1.6, DECK_TOP - 0.01, sz_ + 3.5)
    deck = deck + spost
    deck = deck - box(sx_ - 2.3, sx_ + 2.3, sy_ - 1.65, sy_ - 1.0, sz_ - 2.0, sz_ + 4)  # seat
    return deck


def make_tower():
    """Holds the piston seat, the lever slot and the tube. World position.

    Print it upside down (lip/top on the bed): `tower` in /stl is already flipped.
    """
    top = TUBE_BOT + 4.0
    t = cyl(TOWER_RO, DECK_TOP, LIP_BOT)
    for x, y in tower_boss_points():
        t = t + cyl(4.5, DECK_TOP, LIP_BOT, x, y)
    t = t - cyl(TOWER_RI, DECK_TOP - 1, LIP_BOT + 0.01)
    # lip: piston up-stop underneath, tube stands on top
    t = t + (cyl(TOWER_RO, LIP_BOT - 0.01, TUBE_BOT) - cyl(R_IN, LIP_BOT - 1, TUBE_BOT + 1))
    # locating collar around the tube foot
    t = t + (cyl(R_OUT + 3.0, TUBE_BOT - 0.01, top) - cyl(R_OUT + 0.25, TUBE_BOT - 0.02, top + 1))
    # (the piston seat ribs are on the chassis, so the piston can be dropped
    # in before the tower goes over it)
    # lever slot (-X). Its roof is the lever's up-stop (with a felt dot)
    roof = lever_top_z(-TOWER_RI, THETA_UP) + PAD
    t = t - box(-TOWER_RO - 6, -TOWER_RI + 3, -SLOT_W / 2, SLOT_W / 2, DECK_TOP - 1, roof)
    # screw holes: M3 x 20 head sits on an 8 mm floor at the bottom of each boss
    for x, y in tower_boss_points():
        t = t - cyl(1.7, DECK_TOP - 1, top + 1, x, y)
        t = t - cyl(3.3, DECK_TOP + 8, top + 1, x, y)
    return t


def make_lever():
    """World position for angle 0 (horizontal). Use place_lever(theta)."""
    L = TIP_X - PIV_X
    hub = Pos(0, 0, 0) * Rot(90, 0, 0) * Cylinder(6.0, LEVER_W)
    bar = box(0, L - 3, -LEVER_W / 2, LEVER_W / 2, -LEVER_T / 2, LEVER_T / 2)
    end = Pos(L - 3, 0, 0) * Rot(90, 0, 0) * Cylinder(LEVER_T / 2, LEVER_W)
    lev = hub + bar + (end & box(L - 3, L, -LEVER_W, LEVER_W, -LEVER_T, LEVER_T))
    lev = lev + box(L - 3, L, -LEVER_W / 2, LEVER_W / 2, 0, LEVER_T / 2)  # flat top at tip
    lev = lev - Rot(90, 0, 0) * Cylinder(1.65, LEVER_W + 2)              # axle
    # relief around the nose: the cam corner passes over it after the drop
    lev = lev - box(NOSE_D - RELIEF_W, NOSE_D + RELIEF_W, -LEVER_W, LEVER_W,
                    LEVER_T / 2 - LEVER_RELIEF, LEVER_T)
    # one-sided follower nose: quarter round toward the tip, vertical face
    # toward the pivot (the cam drops off it instantly)
    q = Pos(NOSE_D, 0, LEVER_T / 2) * Rot(90, 0, 0) * Cylinder(NOSE_R, LEVER_W)
    q = q & box(NOSE_D, NOSE_D + NOSE_R, -LEVER_W, LEVER_W, LEVER_T / 2, LEVER_T)
    post = box(NOSE_D, NOSE_D + NOSE_R, -LEVER_W / 2, LEVER_W / 2,
               LEVER_T / 2 - LEVER_RELIEF - 0.01, LEVER_T / 2 + 0.01)
    lev = lev + q + post
    d = SPRING_X - PIV_X
    lev = lev - cyl(5.6, -LEVER_T / 2 - 1, -LEVER_T / 2 + 2.0, d, 0)      # spring cup
    return lev


def place_lever(theta, shape=None):
    shape = shape if shape is not None else make_lever()
    return Pos(PIV_X, 0, PIV_Z) * Rot(0, -degrees(theta), 0) * shape


def make_cam():
    """Snail cam in its own frame: axis along Y through the origin."""
    pts = []
    n = 180
    for i in range(n):
        psi = 360.0 * i / n
        r = cam_radius(psi)
        pts.append((r * cos(radians(psi)), r * sin(radians(psi))))
        if abs(psi - (CAM_DROP - 360.0 / n)) < 1e-6:  # sharp, undercut drop
            pts.append((CAM_R1 * cos(radians(CAM_DROP)), CAM_R1 * sin(radians(CAM_DROP))))
            u = radians(CAM_DROP - CAM_UNDERCUT)
            pts.append((CAM_R0 * cos(u), CAM_R0 * sin(u)))
    prof = Plane.XZ * Polygon(*pts, align=None)
    cam = Pos(0, CAM_W / 2, 0) * extrude(prof, CAM_W)
    # 3 mm D shaft
    shaft = Rot(90, 0, 0) * Cylinder(1.55, CAM_W + 2)
    shaft = shaft - box(1.2, 3, -CAM_W, CAM_W, -3, 3)
    cam = cam - shaft
    # magnet on the -Y face
    a = radians(CAM_MAG_ANGLE)
    mx, mz = CAM_MAG_R * cos(a), CAM_MAG_R * sin(a)
    cam = cam - Pos(mx, -CAM_W / 2 + MAGNET_H / 2 - 0.5, mz) * Rot(90, 0, 0) * Cylinder(MAGNET_D / 2, MAGNET_H + 1)
    return cam


def place_cam(beta_deg, shape=None):
    shape = shape if shape is not None else make_cam()
    return Pos(CAM_X, 0, CAM_Z) * Rot(0, beta_deg, 0) * shape


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
    # anti-rotation rib (-Y side) for the hopper slot
    t = t + box(-2.0, 2.0, -R_OUT - 2.2, -R_OUT + 0.5, TUBE_BOT + 5.0, Z_C)
    t = t - cyl(R_IN, TUBE_BOT - 1, S + 1)
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
def make_piston():
    """World position when seated (cocked). Closed bottom: the lever hits it."""
    r = R_IN - PISTON_CLEAR
    top = PISTON_TOP_SEATED
    p = cyl(FLANGE_D / 2, SEAT_Z, SEAT_Z + FLANGE_T)
    p = p + cyl(r, SEAT_Z + FLANGE_T - 0.01, top)
    dish = 2.5
    p = p - Pos(0, 0, top + PAYLOAD_D / 2 - dish) * Sphere(PAYLOAD_D / 2)
    # light hollow core, closed at the bottom, 45 deg conical roof
    rc = r - 2.4
    z0 = SEAT_Z + 2.0
    roof = top - dish - 2.5
    p = p - cyl(rc, z0, roof - rc)
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
    """Stand-in N20 gear motor + shaft (not printed), for renders and tests."""
    y0 = MOTOR_Y0
    body = box(CAM_X - MOTOR_W / 2, CAM_X + MOTOR_W / 2, y0, y0 + MOTOR_L,
               CAM_Z - MOTOR_H / 2, CAM_Z + MOTOR_H / 2)
    shaft = Pos(CAM_X, y0 - 5, CAM_Z) * Rot(90, 0, 0) * Cylinder(1.15, 10)  # D-flat stand-in
    return body + shaft


def chamber_ball_z(state="cocked"):
    """Centre height of the ball resting in the piston dish."""
    top = PISTON_TOP_SEATED if state == "cocked" else PISTON_TOP_UP
    return top + PAYLOAD_D / 2 - 2.5 + 0.05


def assembly(state="cocked", panel_lift=0.0, with_balls=True):
    """List of (name, shape, color_key, moving) in world coordinates.

    state: 'cocked' (idle, lever down, piston seated) or 'fired'
    (lever up against its stop, piston lifted LIFT). panel_lift: hit panel.
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
    parts.append(("tower", make_tower(), "inner", False))
    parts.append(("hopper", make_hopper(), "inner", False))
    parts.append(("tube", make_tube(), "tube", False))
    parts.append(("motor", motor_dummy(), "motor", False))
    parts.append(("led_collar", Pos(0, 0, LED_COLLAR_Z) * make_led_collar(), "inner", False))
    for x, y in corners(GUIDE_XY):
        parts.append((f"sleeve_{x:+.0f}_{y:+.0f}",
                      Pos(x, y, WASHER_TOP) * make_sleeve(), "inner", False))
    parts.append(("hit_panel", Pos(0, 0, panel_lift) * make_hit_panel(), "moving", True))
    cocked = state == "cocked"
    theta = THETA_COCKED if cocked else THETA_UP
    lift = 0.0 if cocked else LIFT
    parts.append(("lever", place_lever(theta), "moving", True))
    parts.append(("cam", place_cam(BETA_COCKED if cocked else BETA_FIRED), "moving", True))
    parts.append(("piston", Pos(0, 0, lift) * make_piston(), "moving", True))
    if with_balls:
        parts.append(("ball_chamber", Pos(0, 0, chamber_ball_z(state)) * Sphere(PAYLOAD_D / 2),
                      "ball", True))
    return parts


# printable parts: name -> (shape, qty, colour key, note)
def printable_parts():
    cb, ct = make_capsule()
    tower_print = Rot(180, 0, 0) * make_tower()  # lip on the bed
    return {
        "panel_front_left": (make_side_panel("plain"), 2, "body", "front + left walls"),
        "panel_back": (make_side_panel("back"), 1, "body", "back wall (wall-mount holes)"),
        "panel_right": (make_side_panel("right"), 1, "body", "right wall (USB-C jack)"),
        "panel_glyph": (make_glyph(), 4, "glyph", "'?' inlay, print WITH a panel"),
        "panel_shadow": (make_shadow(), 4, "shadow", "shadow inlay, print WITH a panel"),
        "lid": (make_lid(), 1, "body", "removable top"),
        "chassis": (make_chassis(), 1, "inner", "deck, posts, lever pivot, motor cradle"),
        "tower": (tower_print, 1, "inner", "piston seat + tube stand (printed upside down)"),
        "lever": (Rot(90, 0, 0) * make_lever(), 1, "inner", "launch lever (prints on its side)"),
        "cam": (Rot(90, 0, 0) * make_cam(), 1, "inner", "snail cam for the N20 motor"),
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
