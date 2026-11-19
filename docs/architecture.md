# Architecture: how the block launches a candy

## The requirement

Bonk the bottom of a "?" block, and a candy or a small figure pops out of the top.
It has to survive kids, be printable on a Bambu A1 (256 mm bed) with an AMS,
and be buildable by someone who is comfortable with microcontrollers but not
with mechanical design.

## Options considered

| # | Concept | Pros | Cons |
|---|---|---|---|
| **A** | **Direct mechanical launch.** The hit panel pushes a piston. The ball sits on the piston and keeps flying when the piston stops. Electronics only add sound + light | No actuator to size or tune. Instant response. Launch height follows how hard you hit (very "game"). Works with the power off | A very gentle tap won't launch (the ball rises and drops back, harmlessly) |
| B | Sensor + solenoid kicker under the ball | Same launch every time | A small 12 V push solenoid gives roughly 0.02-0.05 J, which is marginal for lifting a 5-8 g capsule 70 mm + flight. Needs 12 V, a MOSFET and a flyback diode. Loud *clack* |
| C | Sensor + servo cocks a spring plunger, then releases it | Strong, repeatable launch | Sear/latch mechanism is the hardest part to get right without iterations. Two moving mechanisms |
| D | Sensor + servo rotary dispenser + servo elevator | Gentle, "item rises out of the block" look | Servo speed can't throw anything. Item just sits on top. Two servos, more parts, slower |

## Decision: A, plus electronics for sound and light

* **Physics is on our side.** A palm bonk moves the panel at ~2-4 m/s. A ball
  needs only `v = sqrt(2·g·h)` ≈ **1.2 m/s** to rise the 70 mm from the chamber
  to the hatch. At 2 m/s it clears the top by ~13 cm, at 3 m/s by ~40 cm. A
  human hit carries 10-100× more energy than any hobby solenoid.
* **Fewest things that can go wrong.** One moving part (panel + piston) and
  gravity. Gravity also returns everything to rest. No springs to buy or tune.
* **Singulation for free.** The piston top is the floor of a one-ball chamber.
  While the piston is up, its side blocks the window, so the next ball can't
  get in until the panel drops back. Then it rolls in on its own.
* **Electronics stay optional.** A Hall sensor sees the panel move and an
  Arduino plays a chime (DFPlayer) and flashes an LED ring. If any of that
  isn't ready by the deadline, the block still dispenses.

## Key mechanisms

![Section](../images/renders/section.png)

1. **Hit panel** (bottom, 147 mm square, 6 mm). Floats on four M4 screws with
   printed sleeves. It hangs on washers by gravity and travels **10 mm** up
   until its bosses hit O-ring bumpers under the deck.
2. **Piston** stands on the hit panel inside the launch tube. Its top has a
   shallow dish that centres the ball. After the panel stops, the piston coasts
   2 mm more and hits felt pads at the tube end. The ball keeps going.
3. **Launch tube** (34.5 mm bore for 32 mm balls) goes from the deck to the lid.
   A side **window** at the bottom lets one ball in from the hopper. Its roof is
   peaked at 45° so the tube prints without support.
4. **Hopper floor** is a funnel (cone) whose lowest point is at that window,
   sloped **15°** everywhere so balls always roll toward it. A diverter ridge
   behind the tube splits balls left/right so none park behind it.
5. **Chassis deck** holds the electronics bay (46 mm tall), the speaker grille,
   the Hall sensor pocket and a 10 mm grid of M3 holes for mounting boards.
6. **Walls** are mitred panels (printed face down for perfect multicolour faces).
   The corner "rivets" are the screw heads, hidden under press-fit caps.
7. **Lid** sits on the mitres and is held by 4 magnet pairs. Lift it off to refill.

![Hit](../images/renders/section_hit.png)

## Why capsules / round payloads

Anything round singulates perfectly: it rolls, it can't wedge, one fits the
chamber. Loose candy of random shapes is what makes real dispensers jam. 32 mm
vending capsules hold a wrapped candy or a small figure and keep the "mystery".
1" gumballs work too after one parameter change (`PAYLOAD_D = 25.4`).

## Hit sensing

A Hall sensor (SS49E) under the deck and a magnet in a post on the hit panel.
Contactless, so it can't be broken by hard hits and has no travel limit (a
microswitch would be crushed by 10 mm of overtravel). The analog reading lets
firmware set the threshold and auto-zero at boot. The magnet's polarity doesn't
matter (the firmware uses the absolute deviation).

## Numbers (defaults)

| Quantity | Value |
|---|---|
| Block | 160 mm cube |
| Payload | 32 mm ball / capsule |
| Hopper capacity | ~19 capsules (computed in `pytest cad`) |
| Stroke | 10 mm panel, +2 mm piston coast |
| Chamber floor → hatch | 70 mm |
| Min. launch speed | ~1.2 m/s |
| Floor slope | 15° |
| Power | 5 V USB-C, < 1 A typical |
