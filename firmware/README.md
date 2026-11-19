# Firmware

Arduino sketch for an **Arduino Nano** (ATmega328P). It does sound and light only.
The launch is mechanical.

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
| Hit | coin chime (`001.wav`) | white flash, gold sparkle fade |
| Every 10th hit | bonus fanfare (`002.wav`) | rainbow spin |
| 10 min with no hit | | LEDs off until the next hit |

## Tuning the hit sensor

1. Set `DEBUG_HALL 1` in `config.h`, upload, open the Serial Monitor at 115200.
2. With the panel at rest you'll see `raw≈base` (≈ 500-530).
3. Push the panel up slowly. Note how far `raw` moves at roughly half stroke.
4. Set `HIT_THRESHOLD` to about that deviation and `HIT_RELEASE` to ~40 % of it.

All settings live in [`config.h`](mystery_block/config.h). The detector logic is in
[`hit_detector.h`](mystery_block/hit_detector.h) and has host-side unit tests:

```bash
g++ -std=c++11 -Imystery_block test/test_hit_detector.cpp -o /tmp/t && /tmp/t
```

## Sounds

`audio/make_sounds.py` synthesises the three original 8-bit style WAVs. Copy
the contents of `audio/sd/` to a FAT32 microSD. You can replace any file with
your own MP3/WAV, keeping the folder/number names.
