// Hall-effect hit detector. Pure C++ (no Arduino calls) so it can be unit
// tested on a PC: see firmware/test/test_hit_detector.cpp.
#pragma once
#include <stdint.h>
#include <stdlib.h>

class HitDetector {
 public:
  HitDetector(int threshold, int release, uint16_t refractoryMs)
      : threshold_(threshold), release_(release), refractory_(refractoryMs) {}

  // Call once at boot with the resting reading (average a few samples).
  void begin(int baseline) {
    baseline16_ = (int32_t)baseline << 4;
    armed_ = true;
    lastHit_ = 0;
    hasHit_ = false;
  }

  // Feed one ADC sample. Returns true exactly once per hit.
  bool update(int raw, uint32_t nowMs) {
    int dev = abs(raw - baseline());
    bool hit = false;
    bool cooling = hasHit_ && (uint32_t)(nowMs - lastHit_) < refractory_;
    if (armed_ && !cooling && dev >= threshold_) {
      hit = true;
      armed_ = false;
      lastHit_ = nowMs;
      hasHit_ = true;
    } else if (!armed_ && dev <= release_ && !cooling) {
      armed_ = true;
    }
    // Track slow drift (temperature, supply) only while clearly at rest.
    if (armed_ && dev < release_) {
      baseline16_ += (((int32_t)raw << 4) - baseline16_) >> 6;
    }
    return hit;
  }

  int baseline() const { return (int)(baseline16_ >> 4); }
  bool armed() const { return armed_; }

 private:
  int threshold_, release_;
  uint16_t refractory_;
  int32_t baseline16_ = 512L << 4;
  bool armed_ = true;
  bool hasHit_ = false;
  uint32_t lastHit_ = 0;
};
