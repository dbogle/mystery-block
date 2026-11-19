"""Design checks: run with `pytest cad`.

These are the "does it actually fit together and work" tests: printer bed,
stack-up arithmetic, part-to-part interference at rest and at full stroke,
the ball's path in and out of the launch tube, and hopper capacity.
"""
import itertools
import sys
from math import cos, pi, radians, sin, sqrt
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build123d import Box, Cylinder, Pos, Sphere  # noqa: E402

import model as m  # noqa: E402
from params import *  # noqa: E402,F403

TOL = 0.5  # mm^3: allowed overlap (tessellation / touching faces)


def bbox_overlap(a, b):
    A, B = a.bounding_box(), b.bounding_box()
    return (A.min.X < B.max.X and B.min.X < A.max.X and A.min.Y < B.max.Y
            and B.min.Y < A.max.Y and A.min.Z < B.max.Z and B.min.Z < A.max.Z)


def overlap(a, b):
    if not bbox_overlap(a, b):
        return 0.0
    r = a & b
    return 0.0 if r is None else r.volume


@pytest.fixture(scope="module")
def parts():
    return m.printable_parts()


# --------------------------------------------------------------------------
def test_every_part_fits_the_a1_bed(parts):
    for name, (shape, *_rest) in parts.items():
        bb = shape.bounding_box()
        assert bb.size.X <= BED - 10 and bb.size.Y <= BED - 10, name
        assert bb.size.Z <= BED - 10, name


def test_every_part_is_a_valid_solid(parts):
    for name, (shape, *_rest) in parts.items():
        assert shape.is_valid, name
        assert shape.volume > 0, name


def test_stack_up():
    # hit panel: bosses (plus O-ring) reach the deck exactly at STROKE
    assert DECK_BOT - (BOSS_TOP + PAD) == pytest.approx(STROKE)
    # piston: lever lifts it LIFT, then it coasts COAST into the tower lip pad
    assert LIP_BOT - (SEAT_Z + FLANGE_T + PAD) == pytest.approx(LIFT + COAST)
    # guide screw: button head (2.2 mm) + washer must stay inside the panel
    head_bottom = WASHER_TOP - WASHER_T - 2.2
    assert head_bottom > PANEL_BOT, "screw head would stick out of the bottom"
    assert GUIDE_ENGAGE <= M4_INSERT_L
    # rivet screws land in the middle of the deck edge / in the column legs
    assert DECK_BOT + 2.5 < RIVET_Z[0] < DECK_TOP - 2.5
    assert HALF - COL_LEG + 3 < RIVET_U < HALF - 3
    # after firing the piston drops back onto the lever just below the sill,
    # so the next ball rolls straight in
    assert 0.5 <= WIN_BOT - PISTON_TOP_UP <= 2.5
    # launcher fits in the electronics bay
    assert m.lever_top_z(TIP_X, m.THETA_COCKED) - LEVER_T > DECK_TOP + 1
    assert m.CAM_Z + m.CAM_R1 < SLAB_BOT - 1
    assert TUBE_BOT + 4 < SLAB_BOT


@pytest.mark.parametrize("state", ["cocked", "fired"])
def test_nothing_collides(state):
    parts = m.assembly(state=state)
    bad = []
    for (n1, s1, *_), (n2, s2, *_) in itertools.combinations(parts, 2):
        v = overlap(s1, s2)
        if v > TOL:
            bad.append((n1, n2, round(v, 2)))
    assert not bad, bad


@pytest.mark.parametrize("dz", [2, 10, 25, 45, 60])
def test_tower_drops_over_piston_and_lever(dz):
    """Assembly order: lever + piston go in first, then the tower is lowered
    straight down over them. Nothing may block that path."""
    asm = {n: s for n, s, *_ in m.assembly(state="cocked", with_balls=False)}
    tower = Pos(0, 0, dz) * asm["tower"]
    for n in ("piston", "lever", "chassis", "cam", "motor"):
        assert overlap(tower, asm[n]) < 1e-3, n


def test_tower_nuts_clear_the_hit_panel():
    """Tower screw tips + nyloc nuts hang under the deck; the panel must miss them."""
    panel = Pos(0, 0, STROKE) * m.make_hit_panel()
    for x, y in m.tower_boss_points():
        nut = Pos(x, y, DECK_BOT - 3) * Cylinder(3.5, 6)
        assert overlap(panel, nut) < 1e-3, (x, y)


def test_hit_panel_full_stroke_is_free():
    up = m.assembly(state="cocked", panel_lift=STROKE, with_balls=False)
    panel = [s for n, s, *_ in up if n == "hit_panel"][0]
    bad = [(n, round(overlap(panel, s), 2)) for n, s, *_ in up
           if n != "hit_panel" and overlap(panel, s) > TOL]
    assert not bad, bad


def test_piston_coast_is_free():
    """After the lever stops, the piston can coast COAST more."""
    tower = m.make_tower()
    piston = Pos(0, 0, LIFT + COAST - 0.05) * m.make_piston()
    assert overlap(tower, piston) < TOL
    assert overlap(m.make_tube(), piston) < TOL


def _lever_angle_for_cam(beta):
    return m.lever_angle_for_cam(beta)


def test_cam_cocks_dwells_and_releases():
    from math import degrees
    th = {b: _lever_angle_for_cam(b) for b in range(-270, 91, 5)}
    # parked: fully cocked
    assert degrees(_lever_angle_for_cam(m.BETA_COCKED)) == pytest.approx(
        degrees(m.THETA_COCKED), abs=0.3)
    # dwell: stays cocked across the whole dwell (motor coast margin)
    dwell0 = CAM_RISE - 270 + 3
    dwell1 = CAM_RISE + CAM_DWELL - 270 - 4
    for b in range(int(dwell0), int(dwell1) + 1):
        assert degrees(_lever_angle_for_cam(b)) == pytest.approx(
            degrees(m.THETA_COCKED), abs=0.5), b
    # after the drop the lever is free (cam not touching)
    assert _lever_angle_for_cam(m.BETA_FIRED) == pytest.approx(m.THETA_UP)
    # the release is a snap: from fully cocked to fully up within 6 deg of cam
    # turn (about 20 ms at 50 RPM), so the spring, not the cam, sets the speed
    from math import degrees as _d
    cocked = [b / 2 for b in range(int(dwell1 * 2), 120)
              if _lever_angle_for_cam(b / 2) < m.THETA_COCKED + radians(0.5)]
    up = [b / 2 for b in range(int(dwell1 * 2), 120)
          if _lever_angle_for_cam(b / 2) >= m.THETA_UP - 1e-6]
    assert up and up[0] - max(cocked) <= 6.0, (max(cocked), up[0])
    # during the rise the lever only ever goes down (smooth cocking)
    seq = [th[b] for b in sorted(th) if b <= dwell0]
    assert all(b <= a + 1e-4 for a, b in zip(seq, seq[1:]))


def test_cam_turns_freely():
    """Full revolution: the cam never hits the chassis, tower or hopper."""
    fixed = [m.make_chassis(), m.make_tower(), m.make_hopper(), m.motor_dummy()]
    cam = m.make_cam()
    for beta in range(0, 360, 15):
        c = m.place_cam(beta, cam)
        for f in fixed:
            assert overlap(c, f) < TOL, beta


def test_cam_parks_inside_the_dwell():
    """The motor stops when the cam magnet reaches its sensor. That must be
    inside the dwell (fully cocked) with margin for motor coast before the
    drop, and the sensor must sit right where the magnet passes."""
    dwell0, drop = CAM_RISE - 270.0, m.CAM_DROP - 270.0
    assert dwell0 + 10 <= m.BETA_COCKED <= drop - 25
    assert dwell0 + 25 <= m.MAG_TOP_BETA <= drop - 8
    a = radians(m.CAM_MAG_ANGLE - m.MAG_TOP_BETA)
    mx, mz = CAM_X + CAM_MAG_R * cos(a), m.CAM_Z + CAM_MAG_R * sin(a)
    sx, _, sz = m.CAM_SENSOR
    assert sqrt((mx - sx) ** 2 + (mz - sz) ** 2) < 0.5


def _ball(x, y, z):
    return Pos(x, y, z) * Sphere(PAYLOAD_D / 2)


def test_ball_rolls_in_through_the_window():
    """Ball travels from the hopper floor at the port into the chamber."""
    tube, hopper = m.make_tube(), m.make_hopper()
    r = PAYLOAD_D / 2
    # a ball resting on a slope sits r/cos(slope) above the floor point below it
    z_out = m.floor_height(0, R_OUT + r) + r / cos(radians(FLOOR_SLOPE)) + 0.2
    z_in = m.chamber_ball_z("fired") + 0.3
    steps = 8
    for i in range(steps + 1):
        f = i / steps
        y = (R_OUT + r) * (1 - f)
        z = z_out + (z_in - z_out) * f
        b = _ball(0, y, max(z, z_in))
        assert overlap(b, tube) < TOL, f"ball hits tube at y={y:.1f}"
        assert overlap(b, hopper) < 2.0, f"ball hits hopper at y={y:.1f}"


def test_ball_flies_out_of_the_hatch():
    tube, lid = m.make_tube(), m.place_lid(m.make_lid())
    collar = Pos(0, 0, LED_COLLAR_Z) * m.make_led_collar()
    z0 = m.chamber_ball_z("fired") + 1
    z = z0
    while z < S + PAYLOAD_D:
        b = _ball(0, 0, z)
        for name, s in (("tube", tube), ("lid", lid), ("collar", collar)):
            assert overlap(b, s) < TOL, f"ball hits {name} at z={z:.0f}"
        z += 6


def test_hopper_holds_enough_capsules():
    hopper = m.make_hopper()
    tube = m.make_tube()
    fill_to = LED_COLLAR_Z - 2
    space = Pos(0, 0, (SLAB_BOT + fill_to) / 2) * Box(INNER, INNER, fill_to - SLAB_BOT)
    free = space - hopper - Pos(0, 0, 0) * tube
    free_v = free.volume
    ball_v = 4 / 3 * pi * (PAYLOAD_D / 2) ** 3
    capsules = int(free_v * 0.5 / ball_v)  # ~0.5 packing incl. wall effects
    print(f"hopper free volume {free_v / 1000:.0f} cm3 -> ~{capsules} capsules")
    assert capsules >= 15


def test_floor_slope_rolls_everywhere():
    """Steepest-descent check on the analytic floor: everywhere at least the
    design slope, i.e. no flat spots that could strand a ball."""
    for x in range(-60, 61, 15):
        for y in range(-60, 61, 15):
            d = sqrt(x * x + (y - R_OUT) ** 2)
            if d < R_OUT + 1:
                continue
            h1 = m.floor_height(x, y)
            h2 = m.floor_height(x * 0.99, R_OUT + (y - R_OUT) * 0.99)
            assert h1 > h2
