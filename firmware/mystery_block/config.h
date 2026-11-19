// ---------------------------------------------------------------------------
// Mystery Block firmware configuration. Everything you might want to tweak.
// ---------------------------------------------------------------------------
#pragma once

// ---- Pins (Arduino Nano) ---------------------------------------------------
#define PIN_HALL        A0   // SS49E linear Hall sensor output
#define PIN_DF_RX       10   // Nano RX  <- DFPlayer TX
#define PIN_DF_TX       11   // Nano TX  -> 1k resistor -> DFPlayer RX
#define PIN_DF_BUSY     4    // optional: DFPlayer BUSY (LOW while playing)
#define PIN_LEDS        6    // WS2812 data, through a 330 ohm resistor
#define PIN_MOTOR_A     5    // MX1508 / DRV8833 IN1
#define PIN_MOTOR_B     9    // MX1508 / DRV8833 IN2
#define PIN_CAM_HALL    A1   // second SS49E, next to the cam (sees its magnet)

// ---- Hit detection ----------------------------------------------------------
// The hit panel carries a magnet. When the panel is bonked it jumps up toward
// the Hall sensor under the deck and the reading swings away from its resting
// value. Open the Serial Monitor (115200) with DEBUG_HALL 1 to see the numbers
// and tune these.
#define HIT_THRESHOLD   60    // ADC counts away from baseline that count as a hit
#define HIT_RELEASE     25    // must fall back under this before the next hit
#define HIT_REFRACTORY  250   // ms ignored after a hit (panel bounce)
#define DEBUG_HALL      0     // 1 = stream raw/baseline readings at 20 Hz

// ---- Launcher (N20 gear motor + snail cam) ------------------------------------
#define MOTOR_REVERSE   0     // set to 1 if the cam turns the wrong way (it
                              // stalls against the drop and reports FAULT)
#define MOTOR_SPEED     255   // PWM 0..255
#define CAM_ON_DELTA    120   // counts from 512 that mean "magnet at sensor"
#define CAM_OFF_DELTA   60    // ... and "magnet gone" (hysteresis)
#define LAUNCH_TIMEOUT  3000  // ms per step before giving up (jam protection)
#define DEBUG_CAM       0     // 1 = stream cam sensor readings

// ---- Sound (DFPlayer Mini) ---------------------------------------------------
// microSD layout:  /01/001.wav coin   /01/002.wav bonus   /01/003.wav startup
#define SOUND_ENABLED   1
#define SOUND_VOLUME    24    // 0..30
#define SOUND_FOLDER    1
#define SND_COIN        1
#define SND_BONUS       2
#define SND_STARTUP     3
#define BONUS_EVERY     10    // every Nth hit plays the bonus sound + rainbow

// ---- LEDs ---------------------------------------------------------------------
#define LED_COUNT       24
#define LED_BRIGHTNESS  80    // 0..255. Keep < ~100 on a 2 A USB supply
#define IDLE_SLEEP_MS   600000UL  // LEDs turn off after 10 min without a hit
