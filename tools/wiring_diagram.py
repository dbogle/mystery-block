"""Draw docs/images/wiring.svg (hand-laid, no dependencies).

    python tools/wiring_diagram.py
"""
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "docs" / "images" / "wiring.svg"

RED, BLK, YEL, BLU, GRN, ORG, PUR = ("#d62828", "#222222", "#e0a800", "#1d6fd1",
                                    "#2a9d4b", "#f07f13", "#7b3fbf")
W, H = 1100, 640
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
       f'viewBox="0 0 {W} {H}" font-family="Helvetica, Arial, sans-serif">',
       f'<rect width="{W}" height="{H}" fill="#ffffff"/>']


def box(x, y, w, h, title, sub="", fill="#f4f6fa"):
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" '
               f'fill="{fill}" stroke="#334" stroke-width="2"/>')
    svg.append(f'<text x="{x + w / 2}" y="{y + 26}" text-anchor="middle" '
               f'font-size="17" font-weight="bold" fill="#223">{title}</text>')
    if sub:
        for i, line in enumerate(sub.split("\n")):
            svg.append(f'<text x="{x + w / 2}" y="{y + 46 + 16 * i}" text-anchor="middle" '
                       f'font-size="12" fill="#556">{line}</text>')


def pin(x, y, label, side):
    svg.append(f'<circle cx="{x}" cy="{y}" r="4.5" fill="#334"/>')
    dx, anchor = (10, "start") if side == "in-left" else (-10, "end")
    svg.append(f'<text x="{x + dx}" y="{y + 4}" text-anchor="{anchor}" '
               f'font-size="13" fill="#223">{label}</text>')


def wire(points, color, label=None, at=0):
    pts = " ".join(f"{x},{y}" for x, y in points)
    svg.append(f'<polyline points="{pts}" fill="none" stroke="{color}" '
               f'stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round"/>')
    if label:
        (x1, y1), (x2, y2) = points[at], points[at + 1]
        svg.append(f'<text x="{(x1 + x2) / 2}" y="{(y1 + y2) / 2 - 7}" text-anchor="middle" '
                   f'font-size="12" fill="{color}" font-weight="bold">{label}</text>')


def resistor(x, y, label, color):
    """Horizontal resistor centred at (x, y)."""
    svg.append(f'<rect x="{x - 22}" y="{y - 8}" width="44" height="16" rx="3" '
               f'fill="#f3e3c4" stroke="{color}" stroke-width="2.5"/>')
    svg.append(f'<text x="{x}" y="{y - 13}" text-anchor="middle" font-size="12" '
               f'fill="#223">{label}</text>')


# ---- components ------------------------------------------------------------
NX, NY, NW, NH = 430, 170, 220, 300
box(NX, NY, NW, NH, "Arduino Nano", "ATmega328P, 5 V")
nano = {
    "5V": (NX, NY + 90), "GND": (NX, NY + 140), "A0": (NX, NY + 240),
    "D6": (NX + NW, NY + 90), "D4": (NX + NW, NY + 140),
    "D10": (NX + NW, NY + 190), "D11": (NX + NW, NY + 240),
}
for k, (x, y) in nano.items():
    side = "in-left" if x == NX else "in-right"
    pin(x, y, {"D10": "D10 (RX)", "D11": "D11 (TX)"}.get(k, k), side)

UX, UY = 40, 70
box(UX, UY, 190, 120, "USB-C jack", "power only, panel mount\n5 V ≥ 2 A adapter", "#eef7ee")
usb = {"VBUS": (UX + 190, UY + 80), "GND": (UX + 190, UY + 104)}
for k, p in usb.items():
    pin(*p, k, "in-right")

HX, HY = 40, 380
box(HX, HY, 190, 150, "SS49E Hall", "under the deck, flat face\ntoward the panel magnet", "#eef3fb")
hall = {"VCC": (HX + 190, HY + 84), "GND": (HX + 190, HY + 108), "OUT": (HX + 190, HY + 132)}
for k, p in hall.items():
    pin(*p, k, "in-right")

DX, DY = 820, 300
box(DX, DY, 200, 230, "DFPlayer Mini", "microSD: /01/001.wav …", "#fbf3ee")
df = {"VCC": (DX, DY + 80), "GND": (DX, DY + 110), "BUSY": (DX, DY + 140),
      "TX": (DX, DY + 170), "RX": (DX, DY + 200),
      "SPK1": (DX + 200, DY + 100), "SPK2": (DX + 200, DY + 140)}
for k, p in df.items():
    pin(*p, k, "in-left" if p[0] == DX else "in-right")

LX, LY = 820, 50
box(LX, LY, 200, 150, "WS2812B ring", "24 LEDs around the tube top", "#fff8e6")
ring = {"5V": (LX, LY + 80), "GND": (LX, LY + 105), "DIN": (LX, LY + 130)}
for k, p in ring.items():
    pin(*p, k, "in-left")

# speaker
sx, sy = 1060, DY + 120
svg.append(f'<rect x="{sx - 12}" y="{sy - 18}" width="14" height="36" fill="#ccd" stroke="#334" stroke-width="2"/>')
svg.append(f'<polygon points="{sx + 2},{sy - 18} {sx + 24},{sy - 36} {sx + 24},{sy + 36} {sx + 2},{sy + 18}" fill="#ccd" stroke="#334" stroke-width="2"/>')
svg.append(f'<text x="{sx + 8}" y="{sy + 58}" text-anchor="middle" font-size="12" fill="#223">40 mm 3 W</text>')
wire([df["SPK1"], (sx - 12, df["SPK1"][1]), (sx - 12, sy - 8)], PUR)
wire([df["SPK2"], (sx - 12, df["SPK2"][1]), (sx - 12, sy + 8)], PUR)

# ---- rails -------------------------------------------------------------------
RAIL5, RAILG = 330, 360  # x of vertical rails
cap_y = 300
wire([usb["VBUS"], (RAIL5, usb["VBUS"][1]), (RAIL5, hall["VCC"][1]), hall["VCC"]], RED, "+5 V")
wire([usb["GND"], (RAILG, usb["GND"][1]), (RAILG, hall["GND"][1]), hall["GND"]], BLK, "GND")
wire([(RAIL5, nano["5V"][1]), nano["5V"]], RED)
wire([(RAILG, nano["GND"][1]), nano["GND"]], BLK)
for x in (RAIL5, RAILG):
    for y in (nano["5V"][1] if x == RAIL5 else nano["GND"][1],):
        svg.append(f'<circle cx="{x}" cy="{y}" r="5" fill="{RED if x == RAIL5 else BLK}"/>')
# bulk capacitor between rails
svg.append(f'<line x1="{RAIL5}" y1="{cap_y}" x2="{RAIL5 + 8}" y2="{cap_y}" stroke="{RED}" stroke-width="3"/>')
svg.append(f'<rect x="{RAIL5 + 8}" y="{cap_y - 12}" width="6" height="24" fill="#334"/>')
svg.append(f'<rect x="{RAIL5 + 17}" y="{cap_y - 12}" width="6" height="24" fill="#fff" stroke="#334" stroke-width="2"/>')
svg.append(f'<line x1="{RAIL5 + 23}" y1="{cap_y}" x2="{RAILG}" y2="{cap_y}" stroke="{BLK}" stroke-width="3"/>')
svg.append(f'<text x="{RAIL5 + 15}" y="{cap_y - 18}" text-anchor="middle" font-size="12" fill="#223">1000 µF</text>')

# top rails to the right-hand modules (run above the Nano)
TOP5, TOPG = 130, 150
wire([(RAIL5, usb["VBUS"][1]), (RAIL5, TOP5), (760, TOP5), (760, ring["5V"][1]), ring["5V"]], RED)
wire([(RAILG, usb["GND"][1]), (RAILG, TOPG), (780, TOPG), (780, ring["GND"][1]), ring["GND"]], BLK)
wire([(760, ring["5V"][1]), (760, df["VCC"][1]), df["VCC"]], RED)
wire([(780, ring["GND"][1]), (780, df["GND"][1]), df["GND"]], BLK)

# ---- signals -----------------------------------------------------------------
wire([hall["OUT"], (300, hall["OUT"][1]), (300, nano["A0"][1]), nano["A0"]], GRN, "OUT → A0", at=1)
resistor(700, nano["D6"][1], "330 Ω", YEL)
wire([nano["D6"], (678, nano["D6"][1])], YEL)
wire([(722, nano["D6"][1]), (740, nano["D6"][1]), (740, ring["DIN"][1]), ring["DIN"]], YEL, "DATA", at=2)
wire([nano["D4"], (720, nano["D4"][1]), (720, df["BUSY"][1]), df["BUSY"]], ORG)
svg.append(f'<text x="{690}" y="{nano["D4"][1] - 8}" text-anchor="middle" font-size="11" fill="{ORG}">BUSY (optional)</text>')
wire([nano["D10"], (700, nano["D10"][1]), (700, df["TX"][1]), df["TX"]], BLU)
resistor(760, df["RX"][1], "1 kΩ", BLU)
wire([nano["D11"], (680, nano["D11"][1]), (680, df["RX"][1]), (738, df["RX"][1])], BLU)
wire([(782, df["RX"][1]), df["RX"]], BLU)

svg.append(f'<text x="40" y="{H - 30}" font-size="13" fill="#556">Red = +5 V, black = GND. '
           'Keep LED + DFPlayer power wires short and thick-ish (22-24 AWG). '
           'Hall sensor: SS49E pins left→right (flat face toward you): VCC, GND, OUT.</text>')
svg.append(f'<text x="40" y="34" font-size="22" font-weight="bold" fill="#223">Mystery Block wiring</text>')
svg.append("</svg>")
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(svg))
print(f"wrote {OUT}")
