#!/usr/bin/env python3
"""Rebuild 32px fish textures from indexed sprite sources, without resampling."""

import json
from PIL import Image, ImageColor
from artwork import PACK, FISH, save, sheet


def main():
    source = json.loads((PACK / "art/fish.json").read_text())
    if set(source) != set(dict(FISH)):
        raise ValueError("Fish source ID mismatch")
    entries = []
    for identifier, label in FISH:
        spec = source[identifier]
        if len(spec["rows"]) != 32 or any(len(row) != 32 for row in spec["rows"]):
            raise ValueError(identifier + " must be 32x32")
        im = Image.new("RGBA", (32, 32))
        for y, row in enumerate(spec["rows"]):
            for x, code in enumerate(row):
                if code != ".":
                    im.putpixel(
                        (x, y), ImageColor.getrgb(spec["palette"][code]) + (255,)
                    )
        save(im, "fish", identifier)
        entries.append((im, label, identifier))
    sheet(entries, "contact_sheet.png")


if __name__ == "__main__":
    main()
