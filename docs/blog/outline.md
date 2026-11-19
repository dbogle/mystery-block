# Blog post draft: "I built a real-life ? block that serves up candy"

Working outline. Photo names refer to `images/photos/`.

## 1. Hook (hero video)
* A kid bonks the block and a capsule rises out of the top. (`08-first-lift.mp4`)
* One sentence: a 3D-printed "?" block that lifts a mystery capsule out of the top when you hit it.

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
* The pivot to v3: a launched capsule has to be *caught*. Small kids don't
  catch, and a missed capsule falls back in or rolls under the sofa. So: an
  elevator. Belt-driven car, capsule rises out of the lid and waits.
* Why a belt (no room for a rack under the car, a lead screw is slow).
* Lift renders (`lift_down.png`, `lift_up.png`) and the section
  (`section.png`, `section_up.png`).

## 4. One capsule at a time, no extra parts
* Funnel floor, one-ball car, the 70 mm tall car closes the window while it's up (no gate).
* Why round capsules.

## 5. CAD as code
* build123d, `params.py`, tests that prove the ball path is clear.
* Render gallery (`assembly.png`, `cutaway.png`, `exploded.png`).

## 6. Printing the faces with the AMS
* Face-down panels, 1.2 mm inlay = only a handful of colour swaps.
* Photo: first layer of a "?" on the textured plate. (`11-first-layer.jpg`)

## 7. Electronics: making it *feel* right
* Hall sensor + magnet, coin chime, LED burst. Wiring diagram.
* Two more Hall sensors + one magnet in the belt clamp = end stops with no
  switches. Jam detection with a timeout; it re-homes on the next hit.
* Original 8-bit sounds generated in Python.

## 8. Assembly + first hit
* Flat lay, inserts, electronics bay, walls, rivets.
* What went wrong (be honest, readers love this).

## 9. Results + what's next
* Capacity, cycle time, how many hits before a refill.
* v2 ideas: hatch flap, empty-detector, battery version, bigger 50 mm capsules.

## 10. Build your own
* Link to the repo, BOM, print guide.
