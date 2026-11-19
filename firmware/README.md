# Firmware

Arduino sketch for an **Arduino Nano** (ATmega328P). It senses the hit, runs
the launcher motor, and plays the sound and light show.

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
| Hit | coin chime (`001.wav`) + launch | white flash, gold sparkle fade |
| Every 10th hit | bonus fanfare (`002.wav`) | rainbow spin |
| 10 min with no hit | | LEDs off until the next hit |
| Launcher jammed | | blinking red (next hit retries) |

## Launcher

The block idles **cocked**: the cam holds the lever down against the spring and
its magnet sits in front of the cam Hall sensor (A1). A hit (or `f` in the
Serial Monitor) runs the motor; the cam drops the lever (launch), keeps turning,
re-cocks and stops when the magnet comes back round. That's one revolution,
about 1.2 s with a 50 RPM motor, and hits during that time are ignored.

At power-on the motor turns until it finds the magnet (this may fire once if
the cam stopped mid-way, so keep the hatch clear).

If a step takes longer than `LAUNCH_TIMEOUT` (3 s) the motor stops and the LEDs
blink red. The usual causes:

| Symptom | Fix |
|---|---|
| Motor hums, cam pushes against the drop face | Motor turns backwards: set `MOTOR_REVERSE 1` or swap the two motor wires |
| Cam turns but never stops | Cam sensor not seeing the magnet: check A1 wiring, magnet polarity, or tune with `DEBUG_CAM 1` |
| Motor doesn't move | Driver power / wiring (VM to 5 V, IN1 to D5, IN2 to D9) |

To tune the cam sensor, set `DEBUG_CAM 1`, turn the cam slowly by hand and
watch the readings; `CAM_ON_DELTA` should be about half the peak deviation.

## Tuning the hit sensor

1. Set `DEBUG_HALL 1` in `config.h`, upload, open the Serial Monitor at 115200.
2. With the panel at rest you'll see `raw≈base` (≈ 500-530).
3. Push the panel up slowly. Note how far `raw` moves at roughly half stroke.
4. Set `HIT_THRESHOLD` to about that deviation and `HIT_RELEASE` to ~40 % of it.

All settings live in [`config.h`](mystery_block/config.h). The hit detector
([`hit_detector.h`](mystery_block/hit_detector.h)) and the launcher state machine
([`launcher.h`](mystery_block/launcher.h)) are plain C++ with host-side unit tests:

```bash
g++ -std=c++11 -Imystery_block test/test_hit_detector.cpp -o /tmp/t && /tmp/t
g++ -std=c++11 -Imystery_block test/test_launcher.cpp -o /tmp/l && /tmp/l
```

## Sounds

`audio/make_sounds.py` synthesises the three original 8-bit style WAVs. Copy
the contents of `audio/sd/` to a FAT32 microSD. You can replace any file with
your own MP3/WAV, keeping the folder/number names.
