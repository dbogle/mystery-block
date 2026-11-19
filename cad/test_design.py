"""Design checks: run with `pytest cad`.

These are the "does it actually fit together and work" tests: printer bed,
stack-up arithmetic, part-to-part interference at rest and at full stroke,
the capsule's path into the lift and up out of the lid, and hopper capacity.
"""
import itertools
import sys
from math import cos, pi, radians, sqrt
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build123d import Box, Pos, Sphere  # noqa: E402

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
    # guide screw: button head (2.2 mm) + washer must stay inside the panel
    head_bottom = WASHER_TOP - WASHER_T - 2.2
    assert head_bottom > PANEL_BOT, "screw head would stick out of the bottom"
    assert GUIDE_ENGAGE <= M4_INSERT_L
    # rivet screws land in the middle of the deck edge / in the column legs
    assert DECK_BOT + 2.5 < RIVET_Z[0] < DECK_TOP - 2.5
    assert HALF - COL_LEG + 3 < RIVET_U < HALF - 3
    # lift: car top below the window sill when down, so the next capsule
    # rolls straight in; at the top the dish is flush with the lid
    assert 2.0 <= WIN_BOT - CAR_TOP_DOWN <= 6.0
    assert CAR_TOP_UP == pytest.approx(S)
    # the hit panel at full stroke stays under the car
    assert CAR_BOT_DOWN > PANEL_TOP + STROKE + 1
    # idler and housing stay under the lid
    assert IDLER_Z + IDLER_FLANGE_R < LID_IN


def test_window_stays_shut_while_the_car_is_away():
    """No gate needed: once the car leaves, its side wall covers the window,
    so the next capsule waits in the hopper. The gap under the car at the
    top can't let a capsule in."""
    car_bot_up = CAR_BOT_DOWN + LIFT_TRAVEL
    assert car_bot_up - WIN_BOT < PAYLOAD_D / 8
    win_top = WIN_BOT + WIN_W + WIN_W / 2  # peaked roof
    # the car is a solid wall over the window from bottom to top of travel
    assert CAR_H > WIN_W + WIN_W / 2 + (car_bot_up - WIN_BOT)
    assert CAR_TOP_UP > win_top


def test_capsule_is_presented_above_the_lid():
    z = m.chamber_ball_z(LIFT_TRAVEL)
    assert z - S > PAYLOAD_D * 0.35  # more than 85% of the capsule is out
    lid = m.place_lid(m.make_lid())
    assert overlap(_ball(0, 0, z), lid) < TOL


STATIC_SKIP = {("car", "belt"), ("belt", "car"), ("ball_chamber", "car"), ("car", "ball_chamber")}


@pytest.mark.parametrize("lift", [0.0, LIFT_TRAVEL])
def test_nothing_collides(lift):
    parts = m.assembly(lift=lift)
    bad = []
    for (n1, s1, *_), (n2, s2, *_) in itertools.combinations(parts, 2):
        if (n1, n2) in STATIC_SKIP:
            continue
        v = overlap(s1, s2)
        if v > TOL:
            bad.append((n1, n2, round(v, 2)))
    assert not bad, bad


def test_car_travel_is_free():
    """Car (with its capsule) at many heights against every fixed part."""
    fixed = [(n, s) for n, s, *_ in m.assembly(with_balls=False)
             if n not in ("car", "belt", "hit_panel")]
    car = m.make_car()
    steps = 9
    for i in range(steps + 1):
        lift = LIFT_TRAVEL * i / steps
        c = m.place_car(lift, car)
        b = _ball(0, 0, m.chamber_ball_z(lift))
        for n, s in fixed:
            assert overlap(c, s) < TOL, (round(lift, 1), "car", n)
            assert overlap(b, s) < TOL, (round(lift, 1), "capsule", n)


@pytest.mark.parametrize("dz", [5, 30, 60, 100])
def test_assembly_order(dz):
    """The car goes in first (it rests in the deck), then the belt housing and
    the tube are lowered straight down over it. Nothing may block that path."""
    asm = {n: s for n, s, *_ in m.assembly(with_balls=False)}
    housing = Pos(0, 0, dz) * asm["housing"]
    for n in ("car", "chassis", "motor", "pulleys"):
        assert overlap(housing, asm[n]) < TOL, ("housing", n)
    tube = Pos(0, 0, dz) * asm["tube"]
    for n in ("car", "chassis", "housing"):
        assert overlap(tube, asm[n]) < TOL, ("tube", n)


def test_belt_clamp_clears_pulley_and_idler():
    pulleys, _ = m.belt_dummy()
    car = m.make_car()
    for lift in (0.0, LIFT_TRAVEL):
        assert overlap(m.place_car(lift, car), pulleys) < TOL, lift


def test_lift_sensors_line_up_with_the_magnet():
    (bx, by, bz), (tx, ty, tz) = m.lift_sensor_points()
    assert bz == pytest.approx(ARM_MIN) and tz == pytest.approx(ARM_MAX)
    assert tz - bz == pytest.approx(LIFT_TRAVEL)
    assert bx - 5.5 < 6.0  # magnet face to sensor face, SS49E range


def test_hit_panel_full_stroke_is_free():
    up = m.assembly(panel_lift=STROKE, with_balls=False)
    panel = [s for n, s, *_ in up if n == "hit_panel"][0]
    bad = [(n, round(overlap(panel, s), 2)) for n, s, *_ in up
           if n != "hit_panel" and overlap(panel, s) > TOL]
    assert not bad, bad


def _ball(x, y, z):
    return Pos(x, y, z) * Sphere(PAYLOAD_D / 2)


def test_ball_rolls_in_through_the_window():
    """Capsule rolls from the hopper floor over the sill into the car dish.
    For each step toward the tube axis find the lowest height where it fits
    (where it would rest): that must only ever go down, and end in the dish."""
    solids = [m.make_tube(), m.make_hopper(), m.place_car(0.0)]
    r = PAYLOAD_D / 2
    z_dish = m.chamber_ball_z(0)

    def fits(y, z):
        b = _ball(0, y, z)
        return all(overlap(b, s) < TOL for s in solids)

    def rest_z(y, hi):
        lo = z_dish - 0.5
        if fits(y, lo):
            return lo
        assert fits(y, hi), y
        for _ in range(10):
            mid = (lo + hi) / 2
            lo, hi = (lo, mid) if fits(y, mid) else (mid, hi)
        return hi

    y0 = R_OUT + r + 2
    z = m.floor_height(0, y0) + r / cos(radians(FLOOR_SLOPE)) + 1.0
    prev = z
    for i in range(9):
        y = y0 * (1 - i / 8)
        z = rest_z(y, prev + 0.2)
        assert z <= prev + 0.2, f"capsule would have to climb at y={y:.1f}"
        prev = z
    assert prev <= z_dish + 0.2


def test_hopper_holds_enough_capsules():
    hopper = m.make_hopper()
    tube = m.make_tube()
    fill_to = LED_COLLAR_Z - 2
    space = Pos(0, 0, (SLAB_BOT + fill_to) / 2) * Box(INNER, INNER, fill_to - SLAB_BOT)
    free = space - hopper - tube - m.make_housing()
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
