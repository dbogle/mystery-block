// Host-side unit test for HitDetector:  g++ -std=c++11 -I../mystery_block test_hit_detector.cpp && ./a.out
#include <cassert>
#include <cstdio>
#include "hit_detector.h"

static int hits(HitDetector& d, const int* s, int n, uint32_t& t, int dt = 1) {
  int h = 0;
  for (int i = 0; i < n; i++) { if (d.update(s[i], t)) h++; t += dt; }
  return h;
}

int main() {
  uint32_t t = 0;
  {  // a clean bump, either magnet polarity, counts once
    HitDetector d(60, 25, 250);
    d.begin(512);
    int up[] = {512, 515, 540, 600, 700, 760, 700, 580, 530, 512, 512};
    assert(hits(d, up, 11, t) == 1);
    t += 300;
    int down[] = {512, 480, 420, 300, 260, 400, 500, 512};
    assert(hits(d, down, 8, t) == 1);
  }
  {  // noise below threshold never triggers, and baseline tracks drift
    HitDetector d(60, 25, 250);
    d.begin(512);
    int n = 0;
    for (int i = 0; i < 5000; i++) {
      int v = 512 + (i % 7) - 3 + i / 250;  // +20 counts of slow drift
      if (d.update(v, t++)) n++;
    }
    assert(n == 0);
    assert(d.baseline() > 525);
  }
  {  // panel bounce inside the refractory window is ignored
    HitDetector d(60, 25, 250);
    d.begin(512);
    int bounce[] = {512, 700, 512, 700, 512, 700, 512};
    assert(hits(d, bounce, 7, t, 20) == 1);
    t += 300;
    int again[] = {512, 700, 512};
    assert(hits(d, again, 3, t) == 1);
  }
  {  // held up (panel stuck) only counts once until it comes back down
    HitDetector d(60, 25, 250);
    d.begin(512);
    int n = 0;
    for (int i = 0; i < 2000; i++) if (d.update(700, t++)) n++;
    assert(n == 1);
  }
  puts("hit_detector: all tests passed");
  return 0;
}
