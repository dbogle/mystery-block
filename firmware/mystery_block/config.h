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

// ---- Hit detection ----------------------------------------------------------
// The hit panel carries a magnet. When the panel is bonked it jumps up toward
// the Hall sensor under the deck and the reading swings away from its resting
// value. Open the Serial Monitor (115200) with DEBUG_HALL 1 to see the numbers
// and tune these.
#define HIT_THRESHOLD   60    // ADC counts away from baseline that count as a hit
#define HIT_RELEASE     25    // must fall back under this before the next hit
#define HIT_REFRACTORY  250   // ms ignored after a hit (panel bounce)
#define DEBUG_HALL      0     // 1 = stream raw/baseline readings at 20 Hz

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
