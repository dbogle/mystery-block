# Bill of Materials

Everything here is common stock with fast (Prime-style) shipping in the US.
Links are **search links** on purpose: listings change constantly, so pick any
well-reviewed listing that matches the spec column. Specs are what matter.

> Deadline tip: order the electronics and hardware first. Printing takes
> about 3 days of printer time and can happen while parts ship.

## 1. Electronics

A hit is sensed by a Hall sensor, and a small gear motor drives a belt that lifts
the capsule up out of the lid, the same way every time no matter how hard (or
softly) the block is hit.

| Qty | Part | Spec that matters | Approx. | Link |
|---:|---|---|---:|---|
| 1 | Arduino Nano (ATmega328P) | 5 V, USB-C or Mini-USB clone is fine. 3-pack is cheap insurance | $15 / 3 | [search](https://www.amazon.com/s?k=arduino+nano+atmega328p+usb-c) |
| 1 | DFPlayer Mini MP3 module | DFRobot DFR0299 or clone (YX5200/MH2024K chip) | $8 / 2-5 | [search](https://www.amazon.com/s?k=dfplayer+mini+mp3+module) |
| 1 | microSD card | 1-32 GB, FAT32 | $5 | any |
| 1 | Speaker | **40 mm round, 4-8 Ω, 3 W**, ≤ 6 mm deep | $8 / 2-4 | [search](https://www.amazon.com/s?k=40mm+speaker+4+ohm+3w) |
| 3 | Linear Hall sensor | **SS49E** (aka 49E / AH49E), TO-92. One for the hit panel, two for the lift (bottom + top) | $6 / 10 | [search](https://www.amazon.com/s?k=ss49e+linear+hall+sensor) |
| 1 | Gear motor | **N20, 6 V, 50-100 RPM**, metal gearbox, **3 mm D-shaft**. Runs on 5 V. 50 RPM lifts in ~2.3 s, 100 RPM in ~1.2 s | $10 / 2 | [search](https://www.amazon.com/s?k=n20+gear+motor+6v+50rpm) |
| 1 | Motor driver | **MX1508** dual H-bridge board (or DRV8833). Only one channel is used | $8 / 5 | [search](https://www.amazon.com/s?k=mx1508+motor+driver) |
| 1 | Capacitor | 100 nF ceramic, soldered across the motor terminals (noise) | kit | [search](https://www.amazon.com/s?k=ceramic+capacitor+assortment) |
| 1 | WS2812B LED ring | **24 LEDs, ~66 mm OD / ~52 mm ID** (Adafruit #1586 or clone) | $8-15 | [search](https://www.amazon.com/s?k=ws2812b+24+led+ring) |
| 1 | USB-C power jack | **2-pin "power only" USB-C female, panel mount, M12 thread with nut**, pre-wired | $8 / 5 | [search](https://www.amazon.com/s?k=usb+c+panel+mount+waterproof+2+pin+power+socket+nut) |
| 1 | 5 V USB-C power adapter | ≥ 2 A + USB-C cable ≥ 2 m (you probably own one) | $0-10 | any |
| 1 | Protoboard | 5×7 cm double-sided perfboard | $8 / kit | [search](https://www.amazon.com/s?k=5x7+double+sided+perfboard) |
| 1 | Capacitor | 1000 µF, ≥ 6.3 V electrolytic (LED supply) | kit | [search](https://www.amazon.com/s?k=electrolytic+capacitor+assortment) |
| 1 | Resistor | 1 kΩ (DFPlayer RX line) | kit | any |
| 1 | Resistor | 330 Ω (LED data line) | kit | any |
| – | Wire | 22-26 AWG silicone hookup wire, Dupont / JST-XH connectors if you like plugs | kit | any |

## 2. Hardware

| Qty | Part | Spec | Approx. | Link |
|---:|---|---|---:|---|
| 16 | Heat-set inserts | **M3**, short (≈ 4-5.7 mm long, ≈ 4.5 mm OD). Holes are 4.0 mm | $10 / kit | [search](https://www.amazon.com/s?k=m3+heat+set+inserts+kit) |
| 4 | Heat-set inserts | **M4** (≈ 5.6-6 mm OD, ≤ 8 mm long). Holes are 5.6 mm | (same kit) | ↑ get a kit with M3 + M4 |
| 16 | Screws | **M3 × 8 button head** (ISO 7380) | $8 / kit | [search](https://www.amazon.com/s?k=m3+button+head+screw+assortment) |
| 2 | Screws | **M3 × 8** (same as above): belt housing to deck, from underneath | (same kit) | ↑ so 18 in total |
| 1 | Screw | **M3 × 25** socket head (idler axle) | (same kit) | ↑ get a kit with 8-30 mm lengths |
| 1 | Screw | **M3 × 12** (belt clamp pinch screw, self-taps into the clamp) | (same kit) | ↑ |
| 1 | Nut | **M3 nyloc** (idler axle) | (same kit) | ↑ |
| 1 | Timing belt | **GT2, 6 mm wide, open** (cut to length, ≈ 26 cm used). Usually sold as 5 m rolls | $8 | [search](https://www.amazon.com/s?k=gt2+timing+belt+6mm+open) |
| 1 | Pulley | **GT2 20 tooth, 3 mm bore, 6 mm belt**, with set screws (fits the N20 D-shaft) | $8 / 5 | [search](https://www.amazon.com/s?k=gt2+20+tooth+pulley+3mm+bore) |
| 1 | Idler | **GT2 20 tooth toothless idler, 3 mm bore, 6 mm belt** (flanged, with bearings) | $8 / 5 | [search](https://www.amazon.com/s?k=gt2+toothless+idler+3mm+bore) |
| 2 | Zip ties | small, ≤ 3.5 mm wide (holds the motor in its cradle) | – | any |
| 4 | Screws | **M4 × 30 button head** (ISO 7380) | (same kit) | ↑ get a kit with M3 + M4 |
| 4 | Washers | **M4 fender / penny washer, 12 mm OD, ~1 mm thick** | $6 / kit | [search](https://www.amazon.com/s?k=m4+fender+washer+12mm) |
| 10 | Magnets | **6 × 3 mm** neodymium discs (8 for the lid, 1 for the hit sensor, 1 in the belt clamp) | $8 / 50 | [search](https://www.amazon.com/s?k=6x3mm+neodymium+magnets) |
| 4 | O-rings | **8 mm ID × 2 mm** cross-section (nitrile kit) | $8 / kit | [search](https://www.amazon.com/s?k=o+ring+assortment+kit+nitrile) |
| 2 | Wall screws + anchors | #8 / 4 mm wood screws or drywall anchors (only for wall mounting) | – | any |

## 3. Payload (pick one or mix)

The mechanism is tuned for **round** things. Round = no jams. Default size is **32 mm**.

| Option | Notes | Link |
|---|---|---|
| 32 mm vending capsules (empty) | Put any candy or a mini figurine inside. The "mystery" is what's inside. Fits ~20 in the hopper | [search](https://www.amazon.com/s?k=32mm+vending+capsules+empty) |
| Printed capsules | `stl/capsule_top.stl` + `capsule_bottom.stl`, any color | in repo |
| 1 inch (25 mm) gumballs / jawbreakers | Rebuild CAD with `PAYLOAD_D = 25.4` (one line) | [search](https://www.amazon.com/s?k=1+inch+gumballs) |

Loose small candy (M&Ms, Skittles) will **not** singulate. Put them in capsules.

## 4. Filament (Bambu A1 + AMS)

| Slot | Color | Use | Approx. amount |
|---|---|---|---:|
| 1 | Yellow / gold PLA (e.g. Bambu PLA Basic "Sunflower Yellow" or Matte "Mandarin Orange") | block body | ~450 g |
| 2 | White PLA (or translucent "Jade White" for glow) | "?" glyphs | ~15 g |
| 3 | Dark brown / black PLA | glyph shadow + rivet caps | ~15 g |
| 4 | Any PLA (or translucent PETG for the light tube) | internals | ~400 g |

About **1 kg** total. Two 1 kg spools of yellow is the safe buy.

## 5. Tools

Soldering iron (also used to set heat-set inserts), hex keys 2 / 2.5 mm, CA glue
(for magnets), hot glue gun, wire strippers.

## Cost

Roughly **$110-140** if you buy everything new as kits, much less if you have a
parts bin. Most kits leave plenty of spares.
