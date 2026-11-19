// g++ -std=c++11 -I../mystery_block test_launcher.cpp && ./a.out
#include <cassert>
#include <cstdio>
#include "launcher.h"

// Simulated cam: magnet visible for degrees [10, 50) of each turn,
// motor turns 0.3 deg/ms (50 rpm) while running.
struct Cam {
  double deg = 200;
  bool magnet() const { double d = deg - 360.0 * (int)(deg / 360.0); return d >= 10 && d < 50; }
};

static void run(Launcher& l, Cam& c, uint32_t& t, uint32_t ms, bool jam = false) {
  for (uint32_t i = 0; i < ms; i++, t++) {
    bool on = l.update(c.magnet(), t);
    if (on && !jam) c.deg += 0.3;
  }
}

int main() {
  uint32_t t = 0;
  {  // homes, fires one full turn, parks again
    Launcher l(3000); Cam c; l.begin(t);
    run(l, c, t, 2000);
    assert(l.state() == Launcher::READY);
    double parked = c.deg;
    assert(l.fire(t));
    assert(!l.fire(t));            // busy
    run(l, c, t, 2000);
    assert(l.state() == Launcher::READY);
    assert(l.cycles() == 1);
    assert(c.deg - parked > 300 && c.deg - parked < 420);  // ~one revolution
  }
  {  // jammed motor ends in FAULT, then a fire() retries homing
    Launcher l(3000); Cam c; l.begin(t);
    run(l, c, t, 4000, /*jam=*/true);
    assert(l.state() == Launcher::FAULT);
    assert(!l.update(c.magnet(), t));  // motor off in FAULT
    assert(l.fire(t));
    assert(l.state() == Launcher::HOMING);
    run(l, c, t, 2000);
    assert(l.state() == Launcher::READY);
  }
  {  // magnet hysteresis
    MagnetSensor m(512, 120, 60);
    assert(!m.update(600));
    assert(m.update(700));
    assert(m.update(590));   // still present (above off threshold)
    assert(!m.update(560));
    assert(m.update(300));   // either polarity
  }
  puts("launcher: all tests passed");
  return 0;
}
