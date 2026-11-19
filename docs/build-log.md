# Build log & decision record

A running log for the blog post. Newest entries at the bottom. Add a line every
time something is printed, changed, broken or learned, with a photo filename.

## Decisions

| # | Date | Decision | Why | Alternatives |
|---|---|---|---|---|
| D1 | 2026-11-18 | **Mechanical launch** (panel → piston → ball), electronics only for sound/light | Human hit has 10-100× the energy needed; no actuator to size; still works if electronics slip past the deadline | Solenoid kicker, servo-cocked spring, servo elevator (see [architecture](architecture.md)) |
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

## Timeline

| Date | Entry | Photo / video |
|---|---|---|
| 2026-11-18 | Project kicked off. Architecture chosen, BOM sent for ordering (deadline **Dec 13**) | |
| 2026-11-18 | v1 CAD, firmware, sounds, docs in the repo. All fit/interference tests pass in CI | `images/renders/*` |
| | _Parts ordered_ | |
| | _First wall panel printed (check "?" colours)_ | `photos/..` |
| | _Tube + piston test print: piston slides freely?_ | |
| | _Electronics bench test_ | |
| | _Full assembly_ | |
| | _First launch_ | |
| | _Mounted_ | |

## Lessons learned

_(fill in as you go: what surprised you, what you'd change in v2)_
