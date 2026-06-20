#!/usr/bin/env python3
"""Reproducibly generate the QR codes embedded in the promotional site.

Usage:
    pip install segno
    python tools/generate_qr.py

Re-run after editing any URL in TARGETS below — e.g. once the APK is hosted on a
GitHub Release, point "app" at the new URL and regenerate. Outputs PNG + SVG for
each target into site/assets/qr/.
"""
import os
import segno

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "site", "assets", "qr"))

# --- Edit these URLs, then re-run this script ----------------------------------
TARGETS = {
    # Android data-collection app (internal beta on pgyer)
    "app":  "https://www.pgyer.com/nuna-android-cas",
    # Source-available repository
    "repo": "https://github.com/Kevin-Pal/nuna-edu-toolkit-release",
    # This landing page (the single "hub" QR used on the poster/PPT)
    "site": "https://kevin-pal.github.io/nuna-edu-toolkit-release/",
}
# -------------------------------------------------------------------------------

DARK = "#0E2841"   # NunaPin deck navy
LIGHT = "#ffffff"


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    for name, url in TARGETS.items():
        qr = segno.make(url, error="h")  # high error correction (logo-safe, robust)
        png = os.path.join(OUT, f"{name}.png")
        svg = os.path.join(OUT, f"{name}.svg")
        qr.save(png, scale=12, border=2, dark=DARK, light=LIGHT)
        qr.save(svg, scale=12, border=2, dark=DARK, light=LIGHT)
        print(f"  {name:4}  ->  {url}\n        {png}\n        {svg}")
    print(f"\nDone. {len(TARGETS)} QR codes (PNG + SVG) written to {OUT}")


if __name__ == "__main__":
    main()
