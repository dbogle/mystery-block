# Blog post draft: "I built a real-life ? block that shoots candy"

Working outline. Photo names refer to `images/photos/`.

## 1. Hook (hero video)
* Slow-mo of a kid bonking the block and a capsule flying out. (`08-first-launch.mp4`)
* One sentence: a 3D-printed "?" block that pops a mystery capsule out of the top when you hit it, the same height every time.

## 2. Why / constraints
* Deadline (Dec 13), Bambu A1 + AMS, comfortable with Arduino, not with CAD.
* Goal: something kids can abuse.

## 3. The design problem: how do you get candy *up*?
* Options table from `docs/architecture.md` (solenoid vs servo vs spring vs "let the hit do it").
* v1: the person hitting the block *is* the launcher (1.2 m/s needed vs 2-4 m/s
  for a palm bonk). Simple, but a toddler's tap does nothing and an adult's
  wallop throws candy across the room.
* The pivot to v2: the hit becomes a *signal*. A motor slowly winds a spring via
  a snail cam, and the cam's cliff releases it. Same energy every time, no latch.
* Launcher renders (`launcher_cocked.png`, `launcher_fired.png`) and the
  section (`section.png`, `section_hit.png`). Slow-mo of the lever snapping.

## 4. One capsule at a time, no extra parts
* Funnel floor, one-ball chamber, the piston side blocks the next ball while it's up.
* Why round capsules.

## 5. CAD as code
* build123d, `params.py`, tests that prove the ball path is clear.
* Render gallery (`assembly.png`, `cutaway.png`, `exploded.png`).

## 6. Printing the faces with the AMS
* Face-down panels, 1.2 mm inlay = only a handful of colour swaps.
* Photo: first layer of a "?" on the textured plate. (`11-first-layer.jpg`)

## 7. Electronics: making it *feel* right
* Hall sensor + magnet, coin chime, LED burst. Wiring diagram.
* Waiting *cocked* so the launch is instant; a second Hall sensor + a magnet
  in the cam tells the Nano where the cam is. Jam detection with a timeout.
* Original 8-bit sounds generated in Python.

## 8. Assembly + first hit
* Flat lay, inserts, electronics bay, walls, rivets.
* What went wrong (be honest, readers love this).

## 9. Results + what's next
* Capacity, how far it shoots, how many hits before a refill.
* v2 ideas: hatch flap, empty-detector, battery version, bigger 50 mm capsules.

## 10. Build your own
* Link to the repo, BOM, print guide.
