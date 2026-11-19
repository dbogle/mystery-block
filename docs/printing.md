# Printing guide (Bambu A1 + AMS)

All files are in [`/stl`](../stl) and [`/3mf`](../3mf). STLs come out already in
the right orientation. Total ~1 kg of PLA and roughly 40-45 h of printer time.

## AMS colour plan

| AMS slot | Colour | Used by |
|---|---|---|
| 1 | Yellow / gold (body) | walls, lid, hit panel |
| 2 | White (or translucent white if you want the "?" to glow) | "?" glyphs |
| 3 | Dark brown / black | glyph shadow, rivet caps |
| 4 | Grey / any (internals) | chassis, tower, lever, cam, hopper, piston, sleeves, collar |

The tube looks great in **translucent PLA/PETG**: the LED ring lights it up and
you can see the ball fly.

## Multicolour wall panels (the important bit)

Panels print **face down** on the **textured PEI plate**. The "?" and its shadow
are only **1.2 mm deep**, so colour changes only happen on the first ~6 layers.
That keeps purge waste to a few grams per panel instead of hundreds.

1. In Bambu Studio: **File → Import → `3mf/panel_front_left.3mf`**.
2. When asked *"Load these files as a single object with multiple parts?"* click **Yes**.
3. In the object list, set filaments: `body` → slot 1, `glyph` → slot 2, `shadow` → slot 3.
4. Enable *Flush into objects' infill* (right-click object → Flushing options) to cut waste.
5. Slice, print. Repeat for `panel_front_left` (2× total), `panel_back`, `panel_right`.

> Using STLs instead: import `panel_back.stl`, `panel_glyph.stl` and
> `panel_shadow.stl` together and answer **Yes** to the same prompt.

## Per-part settings

Defaults: PLA, 0.20 mm layers, 3 walls, 15 % gyroid infill, no supports.

| Part | Qty | Plate / notes | Colour | ≈ time |
|---|---:|---|---|---:|
| `panel_front_left` | 2 | textured PEI, face down, 3MF multicolour | 1+2+3 | 3.5 h each |
| `panel_back` | 1 | same | 1+2+3 | 3.5 h |
| `panel_right` | 1 | same | 1+2+3 | 3.5 h |
| `lid` | 1 | textured PEI, face down | 1 | 3 h |
| `hit_panel` | 1 | textured face down (as exported). 4 walls for stiffness | 1 | 3.5 h |
| `chassis` | 1 | as exported. 20 % infill (inserts go in here). Tree supports **only** under the lever axle posts' holes if your slicer asks | 4 | 6.5 h |
| `hopper` | 1 | as exported. **10 %** infill is plenty, 4 top layers on the funnel | 4 | 8 h |
| `tube` | 1 | upright, **brim 5 mm**, 3 walls. Slow outer wall for a smooth bore | 4 or translucent | 2 h |
| `tower` | 1 | as exported (upside down, lip on the plate). 4 walls, 30 % infill | 4 | 2 h |
| `lever` | 1 | as exported (on its side). **5 walls, 40 % infill**: it takes the spring load | 4 | 40 min |
| `cam` | 1 | as exported (flat). **100 % infill**, 0.12 mm layers for a smooth profile. Pause at the magnet pocket or glue the magnet after | 4 | 30 min |
| `piston` | 1 | flange down, 3 walls | 4 | 1.5 h |
| `sleeve` | 4 | upright, 100 % (they are tiny) | 4 | 20 min |
| `led_collar` | 1 | disc down | 4 | 40 min |
| `rivet_cap` | 20 | face down, 0.12 mm layers look nicer | 3 | 40 min |
| `capsule_bottom/top` | as many as you like | rim down, 0.12 mm layers, 2 walls | any | 30 min/pair |

## Fit checks after printing

* **Print the launcher first** (`tower`, `lever`, `cam`, `piston`, then the
  `chassis`) and bench test it with the motor and spring before printing the walls.
* The **piston must slide freely** through the tower lip and drop under its own
  weight. If it sticks: light sanding, or a puff of dry PTFE lube.
* The **lever must swing freely** on its axle and the cam must sit snug on the
  motor's D-shaft (a drop of CA if it slips).
* A 32 mm capsule must drop through the tube from the top without catching.
* The tube must sit fully in the tower collar and through the hopper.
* Rivet caps: snug push fit. Loose? A dot of glue stick or Blu-Tack. Tight? Sand the peg.

## Changing the size

Everything is generated from [`cad/params.py`](../cad/params.py):

```bash
pip install -r cad/requirements.txt
python cad/build.py          # re-export STL/3MF + renders
pytest cad                   # re-check fits and the ball path
```

Common tweaks: `PAYLOAD_D` (ball size), `S` (block size), `COAST` (piston travel),
`FLOOR_SLOPE`, `GLYPH` (the pixel art).
