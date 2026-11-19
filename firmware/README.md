# Firmware

Arduino sketch for an **Arduino Nano** (ATmega328P). It senses the hit, runs
the lift motor, and plays the sound and light show.

## Build & flash

**Arduino IDE:** open `mystery_block/mystery_block.ino`, install the libraries
**DFRobotDFPlayerMini** and **Adafruit NeoPixel** (Library Manager), board
*Arduino Nano*, processor *ATmega328P* (cheap clones often need
*ATmega328P (Old Bootloader)*), upload.

**arduino-cli:**

```bash
arduino-cli core install arduino:avr
arduino-cli lib install "DFRobotDFPlayerMini" "Adafruit NeoPixel"
arduino-cli compile --fqbn arduino:avr:nano firmware/mystery_block
arduino-cli upload  --fqbn arduino:avr:nano:cpu=atmega328old -p /dev/ttyUSB0 firmware/mystery_block
```

## Behaviour

| Event | Sound | LEDs |
|---|---|---|
| Power on | start-up chime (`003.wav`) | gold shimmer |
| Hit | coin chime (`001.wav`) + lift | white flash, gold sparkle fade |
| Every 10th hit | bonus fanfare (`002.wav`) | rainbow spin |
| 10 min with no hit | | LEDs off until the next hit |
| Lift jammed | | blinking red (next hit retries) |

## Lift

The car idles **down** (loading position): the magnet in its belt clamp sits in
front of the bottom Hall sensor (A1). A hit (or `f` in the Serial Monitor)
drives the motor up until the magnet reaches the top sensor (A2). The capsule
is now on top of the lid. The car holds there for `LIFT_HOLD_MS` (8 s), then
drives down until the bottom sensor sees the magnet again, and the next capsule
rolls in. Hits while it is moving or holding are ignored.

At power-on the car always drives down to the bottom sensor first.

If a move takes longer than `LIFT_TIMEOUT` (5 s) the motor stops and the LEDs
blink red. The next hit re-homes it. The usual causes:

| Symptom | Fix |
|---|---|
| Car goes up at power-on, then red | Motor turns backwards: set `MOTOR_REVERSE 1` or swap the two motor wires |
| Car reaches the end but the motor keeps running | Sensor not seeing the magnet: check A1/A2 wiring, or tune with `DEBUG_LIFT 1` |
| Something held the car (a hand on the capsule) | Nothing to fix: the next hit retries |
| Motor doesn't move | Driver power / wiring (VM to 5 V, IN1 to D5, IN2 to D9) |

To tune the lift sensors, set `DEBUG_LIFT 1`, move the car slowly by hand
(turn the pulley) and watch the readings; `LIFT_ON_DELTA` should be about half
the peak deviation.

## Tuning the hit sensor

1. Set `DEBUG_HALL 1` in `config.h`, upload, open the Serial Monitor at 115200.
2. With the panel at rest you'll see `raw≈base` (≈ 500-530).
3. Push the panel up slowly. Note how far `raw` moves at roughly half stroke.
4. Set `HIT_THRESHOLD` to about that deviation and `HIT_RELEASE` to ~40 % of it.

All settings live in [`config.h`](mystery_block/config.h). The hit detector
([`hit_detector.h`](mystery_block/hit_detector.h)) and the lift state machine
([`lift.h`](mystery_block/lift.h)) are plain C++ with host-side unit tests:

```bash
g++ -std=c++11 -Imystery_block test/test_hit_detector.cpp -o /tmp/t && /tmp/t
g++ -std=c++11 -Imystery_block test/test_lift.cpp -o /tmp/l && /tmp/l
```

## Sounds

`audio/make_sounds.py` synthesises the three original 8-bit style WAVs. Copy
the contents of `audio/sd/` to a FAT32 microSD. You can replace any file with
your own MP3/WAV, keeping the folder/number names.
