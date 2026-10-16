#!/usr/bin/env python3
"""Review every current render, including all cast states and food items."""

from PIL import Image
from artwork import BUILD, FISH, RODS, BAITS, DISHES, EXTRAS, sheet


def main():
    for group, entries, output, columns in (
        ("fish", FISH, "contact_sheet_3d.png", 4),
        (
            "rod",
            [
                (name + suffix, label + ("・投げ" if suffix else ""))
                for name, label in RODS
                for suffix in ("", "_cast")
            ],
            "rods_contact_sheet_3d.png",
            7,
        ),
        ("bait", BAITS, "baits_contact_sheet_3d.png", 4),
        ("dish", DISHES, "dishes_contact_sheet_3d.png", 8),
        ("", EXTRAS, "extras_contact_sheet_3d.png", 3),
    ):
        review = []
        for name, label in entries:
            file = (name if group in ("", "fish") else group + "_" + name) + ".png"
            review.append(
                (Image.open(BUILD / "preview3d" / file).convert("RGBA"), label, name)
            )
        sheet(review, output, columns=columns, tile=192 if group == "fish" else 144)


if __name__ == "__main__":
    main()
