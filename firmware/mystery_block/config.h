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
#define PIN_LIFT_BOTTOM A1   // SS49E on the belt housing: car is down
#define PIN_LIFT_TOP    A2   // SS49E on the belt housing: car is up

// ---- Hit detection ----------------------------------------------------------
// The hit panel carries a magnet. When the panel is bonked it jumps up toward
// the Hall sensor under the deck and the reading swings away from its resting
// value. Open the Serial Monitor (115200) with DEBUG_HALL 1 to see the numbers
// and tune these.
#define HIT_THRESHOLD   60    // ADC counts away from baseline that count as a hit
#define HIT_RELEASE     25    // must fall back under this before the next hit
#define HIT_REFRACTORY  250   // ms ignored after a hit (panel bounce)
#define DEBUG_HALL      0     // 1 = stream raw/baseline readings at 20 Hz

// ---- Lift (N20 gear motor + GT2 belt) ------------------------------------------
#define MOTOR_REVERSE   0     // set to 1 if "up" drives the car down (it then
                              // homes the wrong way and reports FAULT)
#define MOTOR_SPEED     255   // PWM 0..255 going up
#define MOTOR_SPEED_DOWN 200  // a little gentler coming down
#define LIFT_ON_DELTA   120   // counts from 512 that mean "magnet at sensor"
#define LIFT_OFF_DELTA  60    // ... and "magnet gone" (hysteresis)
#define LIFT_HOLD_MS    8000  // how long the capsule waits on top of the lid
#define LIFT_TIMEOUT    5000  // ms per move before giving up (jam protection)
#define DEBUG_LIFT      0     // 1 = stream lift sensor readings

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
