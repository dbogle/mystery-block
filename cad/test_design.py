"""Design checks: run with `pytest cad`.

These are the "does it actually fit together and work" tests: printer bed,
stack-up arithmetic, part-to-part interference at rest and at full stroke,
the ball's path in and out of the launch tube, and hopper capacity.
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


@pytest.fixture(scope="module")
def rest():
    return m.assembly(lift=0.0)


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
    # the hit panel's bosses (plus O-ring) reach the deck exactly at STROKE
    assert DECK_BOT - (BOSS_TOP + PAD) == pytest.approx(STROKE)
    # piston flange (plus felt pad) reaches the tube end after the panel stops
    assert TUBE_BOT - (FLANGE_TOP + PAD) == pytest.approx(STROKE + PISTON_OVERTRAVEL)
    assert TUBE_BOT < DECK_BOT, "tube must poke out under the deck as the stop"
    # guide screw: button head (2.2 mm) + washer must stay inside the panel
    head_bottom = WASHER_TOP - WASHER_T - 2.2
    assert head_bottom > PANEL_BOT, "screw head would stick out of the bottom"
    assert GUIDE_ENGAGE <= M4_INSERT_L
    # rivet screws land in the middle of the deck edge
    assert DECK_BOT + 2.5 < RIVET_Z[0] < DECK_TOP - 2.5
    # the top rivets land inside the upper column legs
    assert HALF - COL_LEG + 3 < RIVET_U < HALF - 3
    # piston top sits just under the window sill so balls drop in
    assert PISTON_TOP < WIN_BOT + 1.0
    assert PISTON_TOP > WIN_BOT - 2.0


def test_nothing_collides_at_rest(rest):
    bad = []
    for (n1, s1, *_), (n2, s2, *_) in itertools.combinations(rest, 2):
        v = overlap(s1, s2)
        if v > TOL:
            bad.append((n1, n2, round(v, 2)))
    assert not bad, bad


def test_nothing_collides_at_full_stroke(rest):
    up = m.assembly(lift=STROKE, with_balls=False)
    fixed = [(n, s) for n, s, _, mv in up if not mv]
    moving = [(n, s) for n, s, _, mv in up if mv]
    bad = []
    for (n1, s1), (n2, s2) in itertools.product(moving, fixed):
        v = overlap(s1, s2)
        if v > TOL:
            bad.append((n1, n2, round(v, 2)))
    assert not bad, bad


def test_piston_overtravel_is_free():
    """After the panel stops the piston can coast PISTON_OVERTRAVEL more."""
    tube = m.make_tube()
    piston = Pos(0, 0, STROKE + PISTON_OVERTRAVEL - 0.05) * m.make_piston()
    assert overlap(tube, piston) < TOL


def _ball(x, y, z):
    return Pos(x, y, z) * Sphere(PAYLOAD_D / 2)


def test_ball_rolls_in_through_the_window():
    """Ball travels from the hopper floor at the port into the chamber."""
    tube, hopper = m.make_tube(), m.make_hopper()
    r = PAYLOAD_D / 2
    # a ball resting on a slope sits r/cos(slope) above the floor point below it
    z_out = m.floor_height(0, R_OUT + r) + r / cos(radians(FLOOR_SLOPE)) + 0.2
    z_in = m.chamber_ball_z() + 0.3
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
    z0 = m.chamber_ball_z() + 1
    z = z0
    while z < S + PAYLOAD_D:
        b = _ball(0, 0, z)
        for name, s in (("tube", tube), ("lid", lid), ("collar", collar)):
            assert overlap(b, s) < TOL, f"ball hits {name} at z={z:.0f}"
        z += 6


def test_raised_piston_blocks_next_ball():
    """While the piston is up, the next ball would have to climb a step of at
    least half its radius to get in, which the hopper's slope can't push it
    over. (It drops in once the panel falls back.)"""
    step = PISTON_TOP + STROKE - WIN_BOT
    assert step >= 0.5 * PAYLOAD_D / 2


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
