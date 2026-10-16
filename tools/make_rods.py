#!/usr/bin/env python3
"""Pixel rod silhouettes based on real keiryu, iso and boat-rod construction."""

from PIL import ImageDraw
from artwork import canvas, save, sheet, RODS, OUTLINE, GOLD

LINE = (232, 232, 232)
SPECS = {
    "bamboo": ("#a4b875", "#d8d899", "#a88760", False, False),
    "keiryu_nami": ("#637b83", "#9eb3ac", "#bda17f", False, False),
    "keiryu_jo": ("#716480", "#b49da7", "#c8ad83", False, False),
    "iso_nami": ("#637b83", "#9eafb2", "#666775", True, False),
    "iso_jo": ("#586b94", "#a1b8d0", "#595d70", True, False),
    "fune_nami": ("#677e8b", "#b2bdc5", "#616470", True, True),
    "fune_jo": ("#9c6570", "#d8a19e", "#545769", True, True),
}


def draw_rod(identifier, cast=False):
    im, d = canvas()
    body, high, grip, reel, boat = SPECS[identifier]
    sx, sy = (3, 14) if boat else (2, 14)
    ex, ey = (12, 3) if boat else (12, 2)
    d.line((sx, sy, ex, ey), fill=OUTLINE, width=3)
    d.line((sx, sy, ex, ey), fill=body, width=2 if boat else 1)
    # Matte butt grip and bright reel-seat collar, rather than random rings along the blank.
    d.line((sx, sy, sx + 3, sy - 3), fill=OUTLINE, width=3)
    d.line((sx, sy, sx + 2, sy - 2), fill=grip, width=2)
    d.point((sx, sy - 1), fill="#e0d2b8" if not reel else high)
    d.point((sx + 3, sy - 3), fill=GOLD if identifier.endswith("_jo") else "#c4cdd1")
    d.point((ex, ey), fill=high)
    d.point((ex - 2, ey + 2), fill=high)
    if identifier == "bamboo":
        for x, y in ((6, 9), (8, 7), (10, 5)):
            d.line((x, y, x + 1, y), fill="#718c65")
    elif not reel:
        # Telescopic joints on a long, reel-less stream rod.
        d.point((7, 8), fill=GOLD if identifier.endswith("_jo") else "#b1c3c1")
        d.point((10, 5), fill=high)
    if reel and not boat:
        # Spinning reel beneath the rod; bail, spool and a small handle.
        d.line((5, 11, 7, 12), fill=OUTLINE, width=1)
        d.rectangle((7, 11, 9, 13), fill=OUTLINE)
        d.line((7, 11, 9, 11), fill=GOLD if identifier.endswith("_jo") else "#c3cdd0")
        d.point((8, 12), fill="#c3cdd0")
        d.line((10, 12, 11, 11), fill=OUTLINE)
        d.point((11, 10), fill=high)
    elif boat:
        # Compact twin-axis reel above the grip, with an off-axis crank.
        d.rectangle((5, 7, 8, 10), fill=OUTLINE)
        d.rectangle(
            (6, 7, 7, 9), fill=GOLD if identifier.endswith("_jo") else "#abb9c3"
        )
        d.point((6, 7), fill="#f7dfb1")
        d.point((8, 10), fill=high)
        d.line((8, 8, 10, 9), fill=OUTLINE)
        d.point((11, 9), fill=grip)
    if reel:
        for x, y in ((8, 7), (10, 5), (ex, ey)):
            d.point((x + 1, y), fill="#c8d2d5")
    if not cast:
        # Normal state only. The cast state leaves the line to Minecraft's entity renderer.
        tx = min(ex + 2, 14)
        d.line((ex, ey, tx, ey + 1, tx, 10, tx - 2, 12), fill=LINE, width=1)
        d.line((tx - 2, 12, tx - 3, 12, tx - 3, 11), fill="#9caaaf", width=1)
    native = ImageDraw.Draw(im)
    # Fine cork/EVA stipple and a single-pixel specular edge use the native 32px grid.
    for x, y in (
        (sx * 2 + 1, sy * 2 - 1),
        (sx * 2 + 3, sy * 2 - 3),
        (sx * 2 + 4, sy * 2 - 5),
    ):
        if im.getpixel((x, y))[3]:
            native.point((x, y), fill="#dfc6a0" if not reel else "#929ca6")
    for k in (4, 7):
        x = round(sx * 2 + (ex - sx) * 2 * k / 12)
        y = round(sy * 2 + (ey - sy) * 2 * k / 12)
        if im.getpixel((x, y))[3]:
            native.point((x, y), fill=high)
    return im


def main():
    entries = []
    for identifier, label in RODS:
        for cast in (False, True):
            name = identifier + ("_cast" if cast else "")
            im = draw_rod(identifier, cast)
            save(im, "rod", name)
            entries.append((im, label + ("・投げ" if cast else ""), name))
    sheet(entries, "rods_contact_sheet.png", columns=7, tile=128)


if __name__ == "__main__":
    main()
