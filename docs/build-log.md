# Build log & decision record

A running log for the blog post. Newest entries at the bottom. Add a line every
time something is printed, changed, broken or learned, with a photo filename.

## Decisions

| # | Date | Decision | Why | Alternatives |
|---|---|---|---|---|
| D1 | 2026-11-18 | ~~**Mechanical launch** (panel → piston → ball), electronics only for sound/light~~ Replaced by D13 | Human hit has 10-100× the energy needed; no actuator to size; still works if electronics slip past the deadline | Solenoid kicker, servo-cocked spring, servo elevator (see [architecture](architecture.md)) |
| D2 | 2026-11-18 | **Round 32 mm payload** (vending capsules / printed capsules) | Round things singulate and never jam; capsules keep the "mystery" and fit candy or figures | Loose candy (jams), custom per-candy feeders |
| D3 | 2026-11-18 | **160 mm cube** | Fits the A1 bed with margin, room for ~19 capsules, good "block" presence at head height | 200 mm (fewer parts per plate, needs 2 plates per wall) |
| D4 | 2026-11-18 | **Flat mitred wall panels, face-down printing** | Crisp multicolour "?" with colour changes only in the first 1.2 mm → minimal AMS purge | Printing the shell in one piece (hundreds of colour swaps) |
| D5 | 2026-11-18 | **Rivets = screw heads** under press-fit caps | Hides all fasteners in the block's own decoration | Glue (not serviceable), hidden clips (fragile) |
| D6 | 2026-11-18 | **Magnetic lid** | Tool-free refill | Screws, hinges |
| D7 | 2026-11-18 | **SS49E Hall sensor + magnet** for hit detection | Contactless, survives hard hits, no travel limit, tunable threshold | Microswitch (crushed by overtravel), piezo (noisy), accelerometer (triggers when moved) |
| D8 | 2026-11-18 | **Arduino Nano + DFPlayer Mini + WS2812 ring**, 5 V USB-C | Ubiquitous, cheap, fast shipping, one supply voltage | ESP32 (more than needed), buzzer (too quiet inside a box) |
| D9 | 2026-11-18 | **Wall mount** with 2 screws through the back wall | The bottom must be free to hit; shear load suits screws in anchors | Ceiling hang (swings when hit), stand (tips over) |
| D10 | 2026-11-18 | **build123d (Python) parametric CAD** with fit tests | Reviewable code in git, one-line changes, CI checks that parts still fit | OpenSCAD (not installable in CI here), GUI CAD (not diffable) |
| D11 | 2026-11-18 | **Original pixel-art "?" and synthesised sounds**, generic name | Safe to open-source; fan-inspired without copying anyone's assets | Ripped sprites/sounds (not ours to publish) |
| D12 | 2026-11-18 | **MIT licence** | Simple and permissive for code and models | CERN-OHL, CC BY-SA |
| D13 | 2026-11-19 | ~~**Motorized spring launch**~~ Replaced by D16: N20 motor + snail cam cocks a spring lever; hit panel becomes a sensor | With the mechanical launch, pop height depended on how hard a kid hit it (too soft = nothing, too hard = capsule across the room). Spring energy is the same every time. Cam both cocks and releases, so no latch to tune | Keep mechanical (simplest, inconsistent), solenoid (needs 12 V, marginal energy) |
| D14 | 2026-11-19 | _(superseded by D16)_ **Idle cocked**, cam parked by a magnet + second SS49E | Hit-to-launch in ~0.1 s instead of a full motor turn; no limit switch to wear | Fire from rest (≈ 1 s delay), microswitch homing |
| D15 | 2026-11-19 | _(superseded by D16)_ **Relieved lever top + one-sided follower nose** | Simulation showed the cam's drop corner dragging on the lever's flat top after the drop, so the spring released over ~30° of cam turn (~100 ms) and the launch would have been weak. With a 3 mm relief around the nose and a vertical back face on the nose, release takes ~4° (~13 ms). New test guards it | Raise the cam (no room under the hopper), smaller nose (still slow) |
| D16 | 2026-11-19 | **Lift instead of launch**: belt-driven car raises the capsule out of the lid, holds it 8 s, lowers | A thrown capsule has to be caught, or it falls back in or onto the floor. A lift presents it calmly at the kid's pace and nothing gets lost | Spring launch (D13), rack and pinion (no room for the rack under the car), lead screw (slow, more parts) |
| D17 | 2026-11-19 | **Open GT2 belt** loop, ends clamped to the car arm; two Hall sensors for the ends of travel | Cheap, quiet, can't slip; the clamp carries the one magnet both sensors see, so no limit switches | Closed belt + friction clamp, microswitches |
| D18 | 2026-11-19 | **Tall car (70 mm) closes the window** while it is up | One capsule per lift without a gate or a second actuator | Separate gate servo |

## Timeline

| Date | Entry | Photo / video |
|---|---|---|
| 2026-11-18 | Project kicked off. Architecture chosen, BOM sent for ordering (deadline **Dec 13**) | |
| 2026-11-18 | v1 CAD, firmware, sounds, docs in the repo. All fit/interference tests pass in CI | `images/renders/*` |
| 2026-11-19 | v2: switched to a motorized spring launch (D13). New tower, lever and cam; firmware drives the motor | `images/renders/launcher_*.png` |
| 2026-11-19 | Fixed a slow-release flaw in the lever (D15). Added the interactive 3D viewer and animations | `images/renders/*.gif` |
| 2026-11-19 | v3: lift instead of launch (D16-D18). New car, belt housing and tube; firmware runs a lift state machine | `images/renders/lift_*.png` |
| | _Parts ordered_ | |
| | _First wall panel printed (check "?" colours)_ | `photos/..` |
| | _Lift test print (car + tube + housing + chassis): does the car run smoothly end to end?_ | |
| | _Electronics bench test_ | |
| | _Full assembly_ | |
| | _First lift_ | |
| | _Mounted_ | |

## Lessons learned

_(fill in as you go: what surprised you, what you'd change in v2)_
