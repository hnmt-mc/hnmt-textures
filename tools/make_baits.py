#!/usr/bin/env python3
"""Four intentionally simple, soft-coloured bait sprites without facial features."""

from artwork import canvas, save, sheet, BAITS, OUTLINE, CREAM, IVORY, LEAF


def draw_bait(identifier):
    im, d = canvas()
    if identifier == "mimizu":
        d.ellipse((2, 10, 13, 14), fill="#658874")
        d.line((3, 12, 12, 12), fill="#b1c8a0")
        pts = (3, 8, 4, 5, 6, 5, 7, 9, 9, 9, 10, 5, 12, 5, 12, 7)
        d.line(pts, fill="#ad7885", width=3)
        d.line(pts, fill="#efb5be", width=1)
        for p in ((4, 6), (7, 8), (10, 6)):
            d.point(p, fill="#ffe0d8")
    elif identifier == "ebi":
        d.arc((3, 3, 12, 12), 160, 400, fill="#a57577", width=4)
        d.arc((4, 4, 11, 11), 160, 400, fill="#efb399", width=2)
        for x, y in ((5, 4), (8, 4), (10, 6)):
            d.point((x, y), fill=CREAM)
        d.polygon(((4, 10), (2, 12), (4, 13), (6, 11)), fill="#dd8f88")
        d.line((10, 9, 12, 11, 13, 9), fill="#e8c0a2")
    elif identifier == "iwashi":
        d.polygon(
            (
                (2, 8),
                (4, 5),
                (9, 4),
                (13, 7),
                (13, 9),
                (9, 11),
                (4, 10),
                (2, 8),
                (1, 5),
                (1, 11),
            ),
            fill=OUTLINE,
        )
        d.polygon(((3, 8), (5, 6), (10, 6), (12, 8), (9, 10), (5, 9)), fill="#d7e4da")
        d.line((5, 6, 10, 6, 11, 7), fill="#82a6b1")
        d.line((5, 8, 10, 8), fill=IVORY)
        d.point((6, 5), fill="#98b3bb")
    else:
        d.ellipse((1, 9, 14, 14), fill="#72977d")
        d.line((3, 12, 12, 11), fill="#aac19a")
        for x, y in ((3, 4), (5, 8)):
            d.polygon(
                (
                    (x, y),
                    (x + 6, y - 1),
                    (x + 8, y + 1),
                    (x + 7, y + 3),
                    (x + 1, y + 3),
                ),
                fill="#b69da7",
            )
            d.polygon(
                (
                    (x + 1, y),
                    (x + 6, y),
                    (x + 7, y + 1),
                    (x + 6, y + 2),
                    (x + 1, y + 2),
                ),
                fill="#f7e9e0",
            )
            d.line((x + 2, y, x + 5, y), fill=IVORY)
    return im


def main():
    entries = []
    for identifier, label in BAITS:
        im = draw_bait(identifier)
        save(im, "bait", identifier)
        entries.append((im, label, identifier))
    sheet(entries, "baits_contact_sheet.png")


if __name__ == "__main__":
    main()
