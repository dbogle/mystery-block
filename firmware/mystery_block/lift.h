// Lift state machine. Pure C++ (no Arduino calls) so it is unit tested on a
// PC: see firmware/test/test_lift.cpp.
//
// A belt raises the car from the loading position (bottom) until the capsule
// sits on top of the lid, waits for the kid to take it, then goes back down.
// A magnet in the belt clamp passes two Hall sensors: BOTTOM and TOP.
//   HOMING  : drive down until the bottom sensor          -> DOWN
//   DOWN    : motor off, a capsule rolls in. raise()      -> RAISING
//   RAISING : drive up until the top sensor                -> HOLDING
//   HOLDING : motor off, capsule presented for holdMs      -> LOWERING
//   LOWERING: drive down until the bottom sensor           -> DOWN
//   FAULT   : motor off. Any move that takes too long ends here (jam,
//             motor wired backwards, sensor missing). raise() re-homes.
// An untaken capsule simply rides back down and is offered next time.
#pragma once
#include <stdint.h>

class Lift {
 public:
  enum State : uint8_t { HOMING, DOWN, RAISING, HOLDING, LOWERING, FAULT };

  Lift(uint16_t moveTimeoutMs, uint16_t holdMs)
      : timeout_(moveTimeoutMs), hold_(holdMs) {}

  void begin(uint32_t now) { enter(HOMING, now); }

  // Request a lift. Returns false if busy (a cycle is already running).
  bool raise(uint32_t now) {
    if (state_ == DOWN) { enter(RAISING, now); return true; }
    if (state_ == FAULT) { enter(HOMING, now); return true; }
    return false;
  }

  // Call every loop with the debounced sensor flags. Returns the motor
  // command: +1 up, -1 down, 0 stop (brake).
  int8_t update(bool atBottom, bool atTop, uint32_t now) {
    uint32_t dt = now - since_;
    switch (state_) {
      case HOMING:
      case LOWERING:
        if (atBottom) {
          if (state_ == LOWERING) cycles_++;
          enter(DOWN, now);
        }
        break;
      case RAISING:
        if (atTop) enter(HOLDING, now);
        break;
      case HOLDING:
        if (dt >= hold_) enter(LOWERING, now);
        break;
      default:
        break;
    }
    bool moving = state_ == HOMING || state_ == RAISING || state_ == LOWERING;
    if (moving && (uint32_t)(now - since_) > timeout_) enter(FAULT, now);
    return direction();
  }

  int8_t direction() const {
    if (state_ == RAISING) return 1;
    if (state_ == HOMING || state_ == LOWERING) return -1;
    return 0;
  }
  State state() const { return state_; }
  uint32_t cycles() const { return cycles_; }

 private:
  void enter(State s, uint32_t now) { state_ = s; since_ = now; }
  uint16_t timeout_, hold_;
  State state_ = HOMING;
  uint32_t since_ = 0;
  uint32_t cycles_ = 0;
};

// Hysteresis on an SS49E Hall sensor (idles at ~512 counts).
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
