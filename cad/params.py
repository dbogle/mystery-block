"""All design parameters for the mystery block, in millimetres.

Change a number here, run `python cad/build.py`, and every STL, 3MF and
render is regenerated. `pytest cad` re-checks that everything still fits.

Coordinate system (world): origin at the centre of the block's bottom face,
+Z up, the "back" of the block is +Y (the side that goes against a wall).
"""
from math import radians, tan

# --- Overall block ---------------------------------------------------------
S = 160.0             # outer cube edge length
T = 6.0               # wall / lid panel thickness
EDGE_RELIEF = 0.5     # tiny V-groove at each cube edge; hides print tolerance
FIT = 0.2             # clearance per side between internal parts and walls
INNER = S - 2 * T     # 148: inside of the box
CORE = INNER - 2 * FIT  # 147.6: footprint of chassis + hopper parts
HALF = CORE / 2

# --- Payload (what comes out) ----------------------------------------------
PAYLOAD_D = 32.0      # ball / capsule diameter. 25.4 for 1" gumballs
TUBE_ID = PAYLOAD_D + 2.5
TUBE_WALL = 2.5
TUBE_OD = TUBE_ID + 2 * TUBE_WALL
R_IN, R_OUT = TUBE_ID / 2, TUBE_OD / 2

# --- Hit panel and stroke stack-up (bottom up) -----------------------------
PANEL_RECESS = 2.0    # hit panel sits this far above the table
PANEL_T = 6.0
PANEL_SIZE = INNER - 0.8
BOSS_H = 8.0          # guide boss height on top of the hit panel
STROKE = 10.0         # how far the hit panel travels
PAD = 2.0             # O-ring / felt bumper thickness
PISTON_OVERTRAVEL = 2.0  # piston keeps flying this far after the panel stops
DECK_T = 10.0
FLANGE_T = 3.0
FLANGE_D = 46.0

PANEL_BOT = PANEL_RECESS
PANEL_TOP = PANEL_BOT + PANEL_T                    # 8
BOSS_TOP = PANEL_TOP + BOSS_H                      # 16
DECK_BOT = BOSS_TOP + PAD + STROKE                 # 28
DECK_TOP = DECK_BOT + DECK_T                       # 38
FLANGE_TOP = PANEL_TOP + FLANGE_T                  # 11
TUBE_BOT = FLANGE_TOP + PAD + STROKE + PISTON_OVERTRAVEL  # 25

# Guide screws: M4 x 30 button head + M4 fender washer + printed sleeve
GUIDE_XY = 56.0
GUIDE_SCREW_L = 30.0
GUIDE_ENGAGE = 7.0    # thread length that ends up in the deck insert
WASHER_T = 1.0
WASHER_D = 12.0
SLEEVE_OD, SLEEVE_ID = 8.0, 4.4
SLEEVE_L = GUIDE_SCREW_L - GUIDE_ENGAGE - WASHER_T  # 22
WASHER_TOP = DECK_BOT - SLEEVE_L                    # 6 (panel rests here)

# --- Chamber / hopper -----------------------------------------------------
Z_C = 90.0            # chamber floor: where the waiting ball sits
SLAB_BOT = Z_C - 6.0  # underside of the hopper part (top of lower posts)
FLOOR_SLOPE = 15.0    # degrees; balls roll reliably above ~8 degrees
TAN_SLOPE = tan(radians(FLOOR_SLOPE))
RIDGE_H = 10.0        # diverter ridge behind the tube (front side, -Y)
RIDGE_W = 30.0        # half width of ridge base
WIN_W = PAYLOAD_D + 2.0  # side window ("port") where balls enter the tube
WIN_BOT = Z_C - 1.5
PISTON_TOP = Z_C - 1.0   # slightly below window sill so balls drop in
PISTON_CLEAR = 0.5       # radial clearance piston <-> tube

# --- Structure --------------------------------------------------------------
LID_IN = S - T                 # 154: underside of lid
COL_TOP = LID_IN - 0.3
COL_T = 8.0                    # upper corner column wall thickness
COL_LEG = 31.0                 # length of each L leg
POST = 16.0                    # lower corner post size
RIVET_INSET = (DECK_BOT + DECK_TOP) / 2      # 33: rivets double as screws
RIVET_U = S / 2 - RIVET_INSET                # 47
RIVET_Z = (RIVET_INSET, S - RIVET_INSET)     # 33, 127
M3_INSERT_D, M3_INSERT_L = 4.0, 7.0
M4_INSERT_D, M4_INSERT_L = 5.6, 8.0
MAGNET_D, MAGNET_H = 6.2, 3.2                # pocket for 6x3 magnets
MAGNET_XY = HALF - COL_T / 2 - 0.1           # lid magnet position

# --- Electronics placement (deck) ------------------------------------------
HALL_XY = (40.0, 40.0)
HALL_GAP = 1.5          # magnet-to-sensor gap at full stroke
SPEAKER_XY = (-38.0, -34.0)
SPEAKER_D = 40.6
USB_JACK = (-40.0, 55.0)  # on the right (+X) panel: local u, z. Near the back
USB_JACK_D = 12.3         # M12 panel-mount USB-C
MOUNT_HOLES = ((-28.0, 143.0), (28.0, 143.0))  # back panel wall screws
LED_COLLAR_Z = 140.0

# --- Face art --------------------------------------------------------------
GLYPH_PIXEL = 8.5
GLYPH_DEPTH = 1.2       # colour inlay depth (6 layers at 0.2 mm)
GLYPH_CENTER_Z = 82.0
SHADOW = GLYPH_PIXEL / 3
# Original chunky pixel "?" (viewed from outside). '#' = pixel.
GLYPH = [
    ".####.",
    "##..##",
    "##..##",
    "....##",
    "...##.",
    "..##..",
    "..##..",
    "......",
    "..##..",
    "..##..",
]
RIVET_CAP_D = 10.0
RIVET_PEG_D = 6.2
RIVET_BORE_D = 6.4
RIVET_FLOOR = 2.2       # panel material under the M3 screw head

# --- Printer ---------------------------------------------------------------
BED = 256.0             # Bambu A1
