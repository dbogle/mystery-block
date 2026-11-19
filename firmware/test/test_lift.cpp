// g++ -std=c++11 -I../mystery_block test_lift.cpp && ./a.out
#include <cassert>
#include <cstdio>
#include "lift.h"

// Simulated car: 0 mm = down, 75.5 mm = up. 33 mm/s = 0.033 mm/ms.
// The clamp magnet is seen by a sensor within +-3 mm of it.
struct Car {
  double z = 30;
  bool bottom() const { return z <= 3.0; }
  bool top() const { return z >= 72.5; }
};

static void run(Lift& l, Car& c, uint32_t& t, uint32_t ms, bool jam = false) {
  for (uint32_t i = 0; i < ms; i++, t++) {
    int8_t dir = l.update(c.bottom(), c.top(), t);
    if (!jam) c.z += 0.033 * dir;
    assert(c.z > -3 && c.z < 78.5);  // never drives past an end stop
  }
}

int main() {
  uint32_t t = 0;
  {  // homes down, raises, holds, lowers by itself
    Lift l(5000, 8000); Car c; l.begin(t);
    run(l, c, t, 2000);
    assert(l.state() == Lift::DOWN);
    assert(l.raise(t));
    assert(!l.raise(t));           // busy
    run(l, c, t, 2500);
    assert(l.state() == Lift::HOLDING);
    assert(c.top());
    run(l, c, t, 7000);
    assert(l.state() == Lift::HOLDING);  // still presenting the capsule
    assert(!l.raise(t));
    run(l, c, t, 1100);
    assert(l.state() == Lift::LOWERING);
    run(l, c, t, 2500);
    assert(l.state() == Lift::DOWN);
    assert(l.cycles() == 1);
  }
  {  // powered up with the car at the top: homes down
    Lift l(5000, 8000); Car c; c.z = 75; l.begin(t);
    assert(l.update(c.bottom(), c.top(), t) == -1);
    run(l, c, t, 3000);
    assert(l.state() == Lift::DOWN);
  }
  {  // jammed motor ends in FAULT, then raise() re-homes
    Lift l(5000, 8000); Car c; l.begin(t);
    run(l, c, t, 6000, /*jam=*/true);
    assert(l.state() == Lift::FAULT);
    assert(l.update(c.bottom(), c.top(), t) == 0);  // motor off in FAULT
    assert(l.raise(t));
    assert(l.state() == Lift::HOMING);
    run(l, c, t, 2000);
    assert(l.state() == Lift::DOWN);
  }
  {  // jam on the way up (hand on the car) -> FAULT, motor stops
    Lift l(5000, 8000); Car c; c.z = 0; l.begin(t);
    run(l, c, t, 10);
    assert(l.raise(t));
    run(l, c, t, 1000);
    run(l, c, t, 5000, /*jam=*/true);
    assert(l.state() == Lift::FAULT);
  }
  {  // magnet hysteresis
    MagnetSensor m(512, 120, 60);
    assert(!m.update(600));
    assert(m.update(700));
    assert(m.update(590));   // still present (above off threshold)
    assert(!m.update(560));
    assert(m.update(300));   // either polarity
  }
  puts("lift: all tests passed");
  return 0;
}
