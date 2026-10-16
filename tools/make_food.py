#!/usr/bin/env python3
"""Japanese food sprites with species-specific cuts, toppings and serveware."""

from PIL import ImageDraw
from artwork import (
    canvas,
    save,
    sheet,
    DISHES,
    EXTRAS,
    OUTLINE,
    CREAM,
    IVORY,
    LEAF,
    GOLD,
)

# Flesh, highlight, skin, fibre. No eyes, organs, blood or wet photorealistic details.
FLESH = {
    "salmon": ("#eba27e", "#ffe1af", "#8c9b9a", "#c77c6c"),
    "tai": ("#eed0bf", "#fff2d9", "#bd8992", "#dca6a0"),
    "hirame": ("#e4ded3", "#fff9e9", "#a7aaa3", "#c2bcbb"),
    "hamachi": ("#eac7a3", "#fff0ce", "#92a6a3", "#c7a78e"),
    "buri": ("#e3b5a1", "#ffe5c3", "#879da3", "#b88a86"),
    "ika": ("#ece4e4", "#fffbed", "#bca8bb", "#d6c8d5"),
    "kanpachi": ("#e8c7ae", "#fff0d2", "#a8ac87", "#c4a080"),
    "maguro": ("#cd8990", "#f2b4a8", "#897f97", "#a97080"),
    "saba": ("#c7ced1", "#f6ecda", "#718e9e", "#a4adb7"),
    "kohada": ("#d7dbd4", "#fff3d8", "#85a2a1", "#afc1b5"),
    "unagi": ("#b58666", "#e6bc8b", "#786773", "#976d59"),
}


def plate(d, deep=False):
    d.ellipse((1, 6, 14, 13), fill=OUTLINE)
    d.ellipse((1, 5, 14, 11), fill="#9cbbc0")
    d.ellipse((2, 5, 13, 10), fill="#e7efdc")
    d.arc((2, 5, 13, 11), 0, 180, fill="#c1d3cc", width=1)
    if deep:
        d.ellipse((3, 7, 12, 10), fill="#cda781")


def leaf(d, x, y):
    d.polygon(
        ((x, y + 2), (x + 1, y), (x + 3, y - 1), (x + 4, y), (x + 2, y + 3)),
        fill="#71977e",
    )
    d.line((x + 1, y + 2, x + 3, y), fill="#adbf91")


def slice_piece(d, x, y, flesh, flip=False):
    base, highlight, skin, fibre = flesh
    d.polygon(
        (
            (x, y + 1),
            (x + 3, y),
            (x + 5, y + 1),
            (x + 5, y + 4),
            (x + 2, y + 4),
            (x, y + 3),
        ),
        fill=fibre,
    )
    d.polygon(
        ((x, y + 1), (x + 3, y), (x + 4, y + 1), (x + 4, y + 3), (x + 1, y + 3)),
        fill=base,
    )
    d.line((x + 1, y + 1, x + 2, y + 3), fill=highlight)
    d.point((x + 3, y + 1), fill=highlight)
    if flip:
        d.line((x, y + 3, x + 3, y + 4), fill=skin)


def rice_grains(im, area):
    d = ImageDraw.Draw(im)
    for x, y in area:
        if im.getpixel((x, y))[3]:
            d.line((x, y, x + 1, y), fill="#fff9e9")


def nigiri(fish):
    im, _ = canvas()
    d = ImageDraw.Draw(im)
    base, highlight, skin, fibre = FLESH[fish]
    # A small, irregular rice bolster. Warm shadows keep it from looking like a bun.
    d.polygon(
        (
            (5, 16),
            (9, 12),
            (22, 11),
            (26, 14),
            (27, 19),
            (25, 23),
            (20, 25),
            (10, 25),
            (5, 22),
            (4, 19),
        ),
        fill="#939d9c",
    )
    d.polygon(
        ((6, 16), (10, 13), (22, 13), (25, 15), (25, 21), (21, 24), (11, 24), (6, 21)),
        fill="#d6d7c7",
    )
    d.polygon(
        ((6, 16), (10, 14), (22, 14), (25, 16), (24, 20), (19, 22), (10, 22), (6, 20)),
        fill="#f1f0da",
    )
    for x, y in (
        (7, 18),
        (10, 21),
        (13, 19),
        (16, 22),
        (19, 19),
        (23, 18),
        (22, 21),
        (11, 23),
    ):
        d.line((x, y, x + 1, y), fill="#fff9e9")
    # A long slice curls around both ends of the rice. It is not a flat oval cap.
    d.polygon(
        (
            (3, 14),
            (6, 10),
            (12, 7),
            (23, 6),
            (27, 9),
            (29, 14),
            (27, 17),
            (23, 17),
            (19, 15),
            (10, 16),
            (6, 18),
            (3, 17),
        ),
        fill=fibre,
    )
    d.polygon(
        (
            (4, 13),
            (7, 10),
            (13, 8),
            (23, 7),
            (26, 10),
            (27, 14),
            (24, 15),
            (19, 14),
            (10, 15),
            (6, 17),
            (4, 16),
        ),
        fill=base,
    )
    d.line((8, 10, 13, 8, 22, 8), fill=highlight, width=1)
    if fish == "salmon":
        for x, y in ((8, 11), (13, 9), (18, 9), (23, 10)):
            d.line((x, y, x + 2, y + 3, x + 3, y + 3), fill="#ffe3b7", width=1)
    elif fish == "maguro":
        d.line((9, 12, 12, 14), fill="#da99a0")
        d.line((17, 10, 20, 13), fill="#e0a1a5")
        d.line((14, 9, 17, 9), fill="#f4c7b6")
    elif fish in ("kohada", "saba"):
        d.polygon(((6, 12), (12, 8), (23, 7), (26, 10), (19, 11), (11, 14)), fill=skin)
        d.line((9, 11, 14, 9, 22, 9), fill="#dce6df")
        for x, y in ((11, 10), (16, 9), (21, 9)):
            d.line((x, y, x + 2, y + 2), fill="#718a96")
    elif fish == "unagi":
        for x, y in ((7, 12), (11, 10), (16, 9), (21, 9), (25, 11)):
            d.line((x, y, x + 1, y + 3), fill="#795d55")
        d.line((9, 11, 13, 9, 20, 9), fill="#e9c18a")
    elif fish == "ika":
        for x, y in ((9, 11), (14, 9), (19, 9), (24, 10)):
            d.line((x, y, x + 2, y + 3), fill="#d6ced9")
        d.line((10, 10, 16, 8, 23, 8), fill="#fffbed")
    else:
        for x, y in ((10, 11), (16, 9), (22, 10)):
            d.line((x, y, x + 1, y + 2), fill=highlight)
        # A thin skin edge differentiates the pale fish without colouring the whole slice.
        d.line(
            (7, 16, 10, 15, 16, 15),
            fill=skin if fish in ("hamachi", "kanpachi") else fibre,
        )
    if fish in ("kohada", "unagi"):
        d.polygon(((18, 11), (20, 11), (21, 23), (19, 24)), fill="#55776b")
        d.line((19, 12, 20, 21), fill="#7d9a7d")
    return im


def dish(identifier):
    if identifier.startswith("nigiri_"):
        return nigiri(identifier[7:])
    im, d = canvas()
    if identifier.startswith("sashimi_"):
        fish = identifier[8:]
        plate(d)
        leaf(d, 2, 6)
        # A staggered fan makes each slice legible at inventory scale.
        if fish == "ika":
            for x, y in ((4, 5), (6, 4), (8, 4), (10, 5)):
                d.polygon(
                    ((x, y), (x + 1, y), (x + 2, y + 4), (x, y + 4)), fill="#d7c7d2"
                )
                d.line((x, y, x + 1, y + 3), fill=IVORY)
        elif fish == "hirame":
            for x in (4, 6, 8, 10):
                d.polygon(((x, 5), (x + 2, 4), (x + 2, 8), (x, 9)), fill="#c6c5bd")
                d.line((x, 5, x + 1, 8), fill=IVORY)
        else:
            for x, y in ((4, 5), (7, 4), (9, 5)):
                slice_piece(d, x, y, FLESH[fish], fish in ("saba", "hamachi", "tai"))
        d.point((4, 10), fill="#e8c473")
        d.point((5, 11), fill="#f6deb0")
    elif identifier.startswith("don_") or identifier == "soup_tai":
        soup = identifier == "soup_tai"
        d.polygon(((2, 7), (13, 7), (12, 12), (10, 14), (5, 14), (3, 12)), fill=OUTLINE)
        d.polygon(
            ((3, 8), (12, 8), (11, 12), (9, 13), (5, 12)),
            fill="#b47871" if not soup else "#78949b",
        )
        d.line((5, 13, 10, 13), fill="#79667a")
        d.ellipse((1, 4, 14, 9), fill=OUTLINE)
        d.ellipse((2, 4, 13, 8), fill="#eee4ce")
        if soup:
            d.ellipse((3, 5, 12, 8), fill="#d6b284")
            d.rectangle((4, 5, 6, 6), fill=IVORY)
            d.rectangle((9, 6, 10, 7), fill="#e5c1aa")
            d.point((7, 5), fill=LEAF)
            d.point((11, 5), fill=LEAF)
        elif identifier == "don_ikura":
            native = ImageDraw.Draw(im)
            # Closely packed pearls follow the elliptical bowl opening, without hiding the rim.
            for row, cy in enumerate((9, 12, 15)):
                for cx in range(6 + (row % 2) * 2, 27, 4):
                    if ((cx - 16) / 12) ** 2 + ((cy - 12) / 5) ** 2 > 1:
                        continue
                    native.ellipse((cx - 2, cy - 1, cx + 1, cy + 2), fill="#ba7964")
                    native.ellipse((cx - 1, cy - 1, cx + 1, cy + 1), fill="#e9a16d")
                    native.point((cx - 1, cy - 1), fill="#fbd5a0")
            d.point((12, 4), fill=LEAF)
        else:
            fish = identifier[4:]
            f = FLESH[fish]
            for x, y in ((3, 5), (6, 4), (9, 5)):
                d.polygon(((x, y), (x + 3, y), (x + 2, y + 3), (x, y + 2)), fill=f[0])
                d.line((x + 1, y, x + 1, y + 1), fill=f[1])
            if fish == "unagi":
                for x in (4, 7, 10):
                    d.line((x, 5, x + 1, 7), fill="#805d58")
            leaf(d, 9, 4)
    elif identifier.startswith("grill_"):
        fish = identifier[6:]
        plate(d)
        if fish == "konoshiro":
            d.polygon(
                (
                    (2, 8),
                    (5, 6),
                    (10, 6),
                    (12, 8),
                    (14, 6),
                    (14, 10),
                    (12, 9),
                    (7, 11),
                    (4, 10),
                ),
                fill="#899e9a",
            )
            d.polygon(
                ((3, 8), (5, 7), (10, 7), (11, 8), (7, 10), (4, 9)), fill="#d1b78c"
            )
            for x in (5, 8, 10):
                d.line((x, 7, x, 9), fill="#95816f")
        else:
            roasted = {
                "salmon": ("#dfa785", "#b87e6d"),
                "buri": ("#c69a6f", "#8e6c60"),
                "unagi": ("#a78263", "#735d59"),
            }
            base, shadow = roasted[fish]
            d.polygon(
                ((3, 7), (5, 4), (12, 5), (13, 8), (10, 10), (4, 10)), fill=shadow
            )
            d.polygon(((4, 7), (6, 5), (11, 6), (12, 8), (9, 9), (4, 9)), fill=base)
            for x in (5, 8, 11):
                d.line((x, 6, x + 1, 8), fill=shadow)
            d.line((5, 5, 9, 5), fill="#efd09c")
        leaf(d, 2, 9)
        d.ellipse((11, 9, 13, 11), fill="#f4e8c9")
        d.point((12, 9), fill=IVORY)
    elif identifier.startswith("simmer_"):
        fish = identifier[7:]
        plate(d, True)
        d.ellipse((3, 7, 12, 10), fill="#be9b76")
        base = "#a1b1b0" if fish == "saba" else "#ded7bf"
        d.polygon(((4, 6), (10, 5), (12, 7), (10, 10), (5, 10), (3, 8)), fill="#887f77")
        d.polygon(((4, 6), (9, 6), (11, 7), (9, 9), (5, 9), (4, 8)), fill=base)
        for x in (5, 8):
            d.line((x, 6, x + 1, 8), fill="#d9c2a1")
        d.point((5, 5), fill="#e9cd9b")
        leaf(d, 10, 8)
    else:
        raise ValueError(identifier)
    # A few native-resolution glaze highlights; no blur or semi-transparent fringes.
    native = ImageDraw.Draw(im)
    if not identifier.startswith("nigiri_"):
        for x, y in ((5, 19), (6, 20), (23, 20)):
            if im.getpixel((x, y))[3]:
                native.point((x, y), fill="#f5efdb")
    return im


def extra(identifier):
    im, d = canvas()
    if identifier == "board":
        d.polygon(
            ((2, 5), (10, 5), (12, 3), (14, 4), (14, 6), (12, 8), (12, 13), (2, 13)),
            fill=OUTLINE,
        )
        d.polygon(
            ((3, 6), (10, 6), (12, 4), (13, 4), (13, 6), (11, 8), (11, 12), (3, 12)),
            fill="#c9a87b",
        )
        d.line((4, 7, 9, 7), fill="#e5c99c")
        d.line((4, 10, 9, 10), fill="#b58d6c")
        d.point((12, 5), fill=OUTLINE)
    elif identifier == "rice":
        d.polygon(
            ((4, 5), (11, 5), (13, 11), (11, 14), (4, 14), (2, 11)), fill="#9b8c79"
        )
        d.polygon(
            ((4, 6), (10, 6), (12, 11), (10, 13), (4, 13), (3, 11)), fill="#dbca9d"
        )
        d.ellipse((3, 3, 12, 7), fill="#9a8b77")
        d.ellipse((4, 3, 11, 6), fill=IVORY)
        d.line((4, 8, 10, 8), fill="#b09a76")
        d.rectangle((6, 9, 9, 11), fill="#f1e6c4")
        d.point((7, 10), fill="#96ad85")
        rice_grains(im, [(11, 8), (14, 7), (17, 9), (20, 8)])
    elif identifier == "ikura":
        plate(d)
        for x, y in ((4, 5), (7, 4), (10, 5), (3, 7), (6, 7), (9, 7), (11, 7)):
            d.ellipse((x, y, x + 2, y + 2), fill="#b57c6c")
            d.ellipse((x, y, x + 1, y + 1), fill="#e9ac75")
            d.point((x, y), fill="#f9d8a3")
        leaf(d, 10, 4)
    else:
        raise ValueError(identifier)
    return im


def main():
    entries = []
    for identifier, label in DISHES:
        im = dish(identifier)
        save(im, "dish", identifier)
        entries.append((im, label, identifier))
    sheet(entries, "dishes_contact_sheet.png", columns=8, tile=128)
    entries = []
    for identifier, label in EXTRAS:
        im = extra(identifier)
        save(im, "", identifier)
        entries.append((im, label, identifier))
    sheet(entries, "extras_contact_sheet.png", columns=3)


if __name__ == "__main__":
    main()
