// Launcher state machine. Pure C++ (no Arduino calls) so it is unit tested
// on a PC: see firmware/test/test_launcher.cpp.
//
// The cam carries a magnet; a Hall sensor sees it only while the cam is
// parked in its dwell (lever fully cocked, ~25 deg before the drop).
//   HOMING  : run until the magnet appears                -> READY
//   READY   : motor off, cocked. fire() starts a cycle    -> LEAVING
//   LEAVING : run until the magnet is gone (cam has passed the drop
//             and the lever has fired)                      -> RETURNING
//   RETURNING: run until the magnet appears again (re-cocked) -> READY
//   FAULT   : motor off. Any step that takes too long ends here (jam,
//             motor wired backwards, sensor missing). fire() retries.
#pragma once
#include <stdint.h>

class Launcher {
 public:
  enum State : uint8_t { HOMING, READY, LEAVING, RETURNING, FAULT };

  explicit Launcher(uint16_t stepTimeoutMs) : timeout_(stepTimeoutMs) {}

  void begin(uint32_t now) { enter(HOMING, now); }

  // Request a launch. Returns false if busy (a cycle is already running).
  bool fire(uint32_t now) {
    if (state_ == READY || state_ == FAULT) {
      enter(state_ == READY ? LEAVING : HOMING, now);
      return true;
    }
    return false;
  }

  // Call every loop with the debounced "magnet at sensor" flag.
  // Returns true while the motor should run.
  bool update(bool magnetPresent, uint32_t now) {
    switch (state_) {
      case HOMING:
        if (magnetPresent) enter(READY, now);
        break;
      case LEAVING:
        if (!magnetPresent) enter(RETURNING, now);
        break;
      case RETURNING:
        if (magnetPresent) { enter(READY, now); cycles_++; }
        break;
      default:
        break;
    }
    bool running = state_ == HOMING || state_ == LEAVING || state_ == RETURNING;
    if (running && (uint32_t)(now - since_) > timeout_) enter(FAULT, now);
    return state_ == HOMING || state_ == LEAVING || state_ == RETURNING;
  }

  State state() const { return state_; }
  uint32_t cycles() const { return cycles_; }

 private:
  void enter(State s, uint32_t now) { state_ = s; since_ = now; }
  uint16_t timeout_;
  State state_ = HOMING;
  uint32_t since_ = 0;
  uint32_t cycles_ = 0;
};

// Hysteresis on the cam Hall sensor (SS49E idles at ~512 counts).
class MagnetSensor {
 public:
  MagnetSensor(int center, int onDelta, int offDelta)
      : center_(center), on_(onDelta), off_(offDelta) {}
  bool update(int raw) {
    int d = raw > center_ ? raw - center_ : center_ - raw;
    if (!present_ && d >= on_) present_ = true;
    else if (present_ && d <= off_) present_ = false;
    return present_;
  }
  bool present() const { return present_; }

 private:
  int center_, on_, off_;
  bool present_ = false;
};
