// ---------------------------------------------------------------------------
// Mystery Block - sound + light firmware
//
// A hit on the bottom panel (Hall sensor + magnet) fires the launcher: the
// N20 motor turns the snail cam past its drop-off so the spring lever kicks
// the piston, then re-cocks and parks on the cam magnet. Plus chime + LEDs.
// Bench test: send 'f' in the Serial Monitor (115200) to fire.
//
// Board: Arduino Nano (ATmega328P). Libraries (Library Manager):
//   - DFRobotDFPlayerMini
//   - Adafruit NeoPixel
// ---------------------------------------------------------------------------
#include <Arduino.h>
#include <Adafruit_NeoPixel.h>
#include <DFRobotDFPlayerMini.h>
#include <SoftwareSerial.h>

#include "config.h"
#include "hit_detector.h"
#include "launcher.h"

Adafruit_NeoPixel leds(LED_COUNT, PIN_LEDS, NEO_GRB + NEO_KHZ800);
SoftwareSerial dfSerial(PIN_DF_RX, PIN_DF_TX);
DFRobotDFPlayerMini player;
HitDetector detector(HIT_THRESHOLD, HIT_RELEASE, HIT_REFRACTORY);
Launcher launcher(LAUNCH_TIMEOUT);
MagnetSensor camSensor(512, CAM_ON_DELTA, CAM_OFF_DELTA);

enum Mode : uint8_t { IDLE, BURST, BONUS, SLEEP, FAULTED };
Mode mode = IDLE;
uint32_t modeStart = 0;
uint32_t lastHitMs = 0;
uint32_t lastFrame = 0;
uint32_t hitCount = 0;

// ---- helpers ----------------------------------------------------------------
static uint32_t gold(uint8_t level) {  // warm "coin" colour scaled 0..255
  return leds.Color((uint16_t)255 * level / 255, (uint16_t)170 * level / 255,
                    (uint16_t)20 * level / 255);
}

static uint8_t tri8(uint32_t t, uint16_t period) {  // 0..255..0 triangle wave
  uint16_t p = t % period;
  uint32_t half = period / 2;
  uint32_t v = p < half ? p : period - p;
  return (uint8_t)(v * 255 / half);
}

static void playSound(uint8_t track) {
#if SOUND_ENABLED
  player.playFolder(SOUND_FOLDER, track);
#else
  (void)track;
#endif
}

static void motor(bool on) {
  if (!on) {  // brake: both inputs high stops the cam quickly
    digitalWrite(PIN_MOTOR_A, HIGH);
    digitalWrite(PIN_MOTOR_B, HIGH);
    return;
  }
#if MOTOR_REVERSE
  digitalWrite(PIN_MOTOR_A, LOW);
  analogWrite(PIN_MOTOR_B, MOTOR_SPEED);
#else
  analogWrite(PIN_MOTOR_A, MOTOR_SPEED);
  digitalWrite(PIN_MOTOR_B, LOW);
#endif
}

static void setMode(Mode m, uint32_t now) {
  mode = m;
  modeStart = now;
}

// ---- LED animations (non-blocking, ~50 fps) ----------------------------------
static void frameIdle(uint32_t now) {
  // gentle shimmer: each pixel breathes with its own phase
  for (uint8_t i = 0; i < LED_COUNT; i++) {
    uint8_t b = 18 + tri8(now + i * 173UL, 2400) / 6;
    leds.setPixelColor(i, gold(b));
  }
}

static void frameBurst(uint32_t now) {
  uint32_t t = now - modeStart;
  if (t < 60) {  // white flash
    leds.fill(leds.Color(255, 255, 255));
    return;
  }
  if (t > 700) {
    setMode(IDLE, now);
    return;
  }
  uint8_t level = 255 - (uint8_t)((t - 60) * 230 / 640);
  for (uint8_t i = 0; i < LED_COUNT; i++) {
    uint8_t sparkle = (random(100) < 15) ? 255 : level;
    leds.setPixelColor(i, gold(sparkle));
  }
}

static void frameBonus(uint32_t now) {
  uint32_t t = now - modeStart;
  if (t > 1800) {
    setMode(IDLE, now);
    return;
  }
  for (uint8_t i = 0; i < LED_COUNT; i++) {
    uint16_t hue = (uint16_t)(i * 65536UL / LED_COUNT + t * 90);
    leds.setPixelColor(i, leds.gamma32(leds.ColorHSV(hue)));
  }
}

static void frameFault(uint32_t now) {
  bool on = (now / 250) % 2;
  leds.fill(on ? leds.Color(255, 0, 0) : 0);
}

// ---- setup / loop ---------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  pinMode(PIN_DF_BUSY, INPUT_PULLUP);
  pinMode(PIN_MOTOR_A, OUTPUT);
  pinMode(PIN_MOTOR_B, OUTPUT);
  motor(false);

  leds.begin();
  leds.setBrightness(LED_BRIGHTNESS);
  leds.clear();
  leds.show();

  // Resting Hall reading: average while the panel hangs still.
  long sum = 0;
  for (int i = 0; i < 64; i++) {
    sum += analogRead(PIN_HALL);
    delay(2);
  }
  detector.begin((int)(sum / 64));
  Serial.print(F("Mystery Block ready. Hall baseline = "));
  Serial.println(detector.baseline());

#if SOUND_ENABLED
  dfSerial.begin(9600);
  // isACK=false: never block waiting for the module (keeps LEDs smooth and
  // lets the block run without a DFPlayer fitted).
  player.begin(dfSerial, false, true);
  delay(800);  // DFPlayer boot + SD scan
  player.volume(SOUND_VOLUME);
  delay(50);
  playSound(SND_STARTUP);
#endif
  randomSeed(analogRead(A7));
  lastHitMs = millis();
  setMode(IDLE, millis());
  launcher.begin(millis());  // finds the parked (cocked) position
}

void loop() {
  uint32_t now = millis();

  bool fireNow = detector.update(analogRead(PIN_HALL), now);
  if (Serial.available() && Serial.read() == 'f') fireNow = true;

  if (fireNow) {
    lastHitMs = now;
    if (launcher.fire(now)) {
      hitCount++;
      bool bonus = BONUS_EVERY > 0 && hitCount % BONUS_EVERY == 0;
      playSound(bonus ? SND_BONUS : SND_COIN);
      setMode(bonus ? BONUS : BURST, now);
      Serial.print(F("HIT #"));
      Serial.println(hitCount);
    }
  }

  bool magnet = camSensor.update(analogRead(PIN_CAM_HALL));
  Launcher::State before = launcher.state();
  motor(launcher.update(magnet, now));
  if (launcher.state() == Launcher::FAULT && before != Launcher::FAULT) {
    Serial.println(F("LAUNCHER FAULT: cam never reached its sensor. Jammed? "
                     "Motor backwards (MOTOR_REVERSE)? Cam sensor wired?"));
    setMode(FAULTED, now);
  } else if (mode == FAULTED && launcher.state() != Launcher::FAULT) {
    setMode(IDLE, now);
  }

#if DEBUG_HALL || DEBUG_CAM
  static uint32_t lastDbg = 0;
  if (now - lastDbg >= 50) {
    lastDbg = now;
#if DEBUG_HALL
    Serial.print(F("hit raw="));
    Serial.print(analogRead(PIN_HALL));
    Serial.print(F(" base="));
    Serial.print(detector.baseline());
    Serial.print(' ');
#endif
#if DEBUG_CAM
    Serial.print(F("cam raw="));
    Serial.print(analogRead(PIN_CAM_HALL));
    Serial.print(magnet ? F(" MAGNET") : F(" -"));
    Serial.print(F(" state="));
    Serial.print(launcher.state());
#endif
    Serial.println();
  }
#endif

  if (mode == IDLE && now - lastHitMs > IDLE_SLEEP_MS) setMode(SLEEP, now);

  if (now - lastFrame >= 20) {
    lastFrame = now;
    switch (mode) {
      case IDLE:    frameIdle(now); break;
      case BURST:   frameBurst(now); break;
      case BONUS:   frameBonus(now); break;
      case SLEEP:   leds.clear(); break;
      case FAULTED: frameFault(now); break;
    }
    leds.show();
  }
}
