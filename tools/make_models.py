#!/usr/bin/env python3
"""Export cuboid-only, single-texture item models from 32px source silhouettes."""

import json
import math
from PIL import Image
from artwork import PACK, TEXTURES, FISH, RODS, BAITS, DISHES, EXTRAS

DISPLAY = {
    "gui": {
        "rotation": [12, -25, 0],
        "translation": [0, 0, 0],
        "scale": [0.95, 0.95, 0.95],
    },
    "ground": {
        "rotation": [0, 0, 0],
        "translation": [0, 2, 0],
        "scale": [0.5, 0.5, 0.5],
    },
    "head": {"rotation": [0, 180, 0], "translation": [0, 13, 7], "scale": [1, 1, 1]},
    "thirdperson_righthand": {
        "rotation": [0, 0, 0],
        "translation": [0, 3, 1],
        "scale": [0.55, 0.55, 0.55],
    },
    "firstperson_righthand": {
        "rotation": [0, -90, 25],
        "translation": [1.13, 3.2, 1.13],
        "scale": [0.68, 0.68, 0.68],
    },
    "fixed": {"rotation": [0, 180, 0], "scale": [1, 1, 1]},
}
ROD_DISPLAY = {
    **DISPLAY,
    "gui": {
        "rotation": [10, -25, 0],
        "translation": [0, 0, 0],
        "scale": [0.95, 0.95, 0.95],
    },
    "thirdperson_righthand": {
        "rotation": [0, 90, 55],
        "translation": [0, 4, 2.5],
        "scale": [0.85, 0.85, 0.85],
    },
    "thirdperson_lefthand": {
        "rotation": [0, -90, -55],
        "translation": [0, 4, 2.5],
        "scale": [0.85, 0.85, 0.85],
    },
    "firstperson_righthand": {
        "rotation": [0, 90, 25],
        "translation": [0, 1.6, 0.8],
        "scale": [0.68, 0.68, 0.68],
    },
    "firstperson_lefthand": {
        "rotation": [0, -90, -25],
        "translation": [0, 1.6, 0.8],
        "scale": [0.68, 0.68, 0.68],
    },
}


def inventory():
    for group, entries in (
        ("fish", FISH),
        ("rod", RODS),
        ("bait", BAITS),
        ("dish", DISHES),
        ("", EXTRAS),
    ):
        for name, label in entries:
            yield group, name, label
            if group == "rod":
                yield group, name + "_cast", label + "・投げ"


def runs(image, x):
    result = []
    y = 0
    while y < 32:
        if image.getpixel((x, y))[3] == 0:
            y += 1
            continue
        start = y
        while y < 32 and image.getpixel((x, y))[3]:
            y += 1
        result.append((start, y))
    return result


def geometry(group, name, image):
    columns = {x: runs(image, x) for x in range(32)}
    # The side faces retain exact texture alpha. Coalescing only the cross section limits
    # complex fin silhouettes to one cuboid per column, without another texture or rotation.
    if group == "fish" and sum(map(len, columns.values())) > 32:
        columns = {x: ([(r[0][0], r[-1][1])] if r else []) for x, r in columns.items()}
    max_height = max((b - a for r in columns.values() for a, b in r), default=1)
    maximum = {"fish": 3.5, "rod": 1.6, "bait": 1.8, "dish": 3, "": 2}.get(group, 2)
    maximum = {"unagi": 1.5, "hirame": 0.9, "maguro": 4.1, "ika": 2.4}.get(
        name, maximum
    )
    elements = []
    for x, sections in columns.items():
        for top, bottom in sections:
            height = bottom - top
            depth = round(max(0.5, maximum * (height / max_height) ** 0.8) * 4) / 4
            if group == "fish":
                occupied = [column for column, sections in columns.items() if sections]
                progress = (x - min(occupied) + 0.5) / (
                    max(occupied) - min(occupied) + 1
                )
                # Body depth follows a continuous longitudinal curve instead of fin height.
                # This prevents a dorsal fin from turning into a row of thick slabs.
                depth = max(
                    0.5,
                    round(maximum * 0.65 * math.sin(math.pi * progress) ** 0.6 * 8) / 8,
                )
                if name in ("unagi", "hirame"):
                    depth = 1.0 if name == "unagi" else 0.75
            if group == "rod":
                colors = [image.getpixel((x, y))[:3] for y in range(top, bottom)]
                depth = (
                    0.5
                    if all(c in ((232, 232, 232), (156, 170, 175)) for c in colors)
                    else 1.25 if height < 5 else 2
                )
            u1, u2 = x / 2, (x + 1) / 2
            v1, v2 = top / 2, bottom / 2
            inner = 0.5 if height > 3 else 0
            faces = {
                "north": [u1, v1, u2, v2],
                "south": [u1, v1, u2, v2],
                "west": [u1, v1, u2, v2],
                "east": [u1, v1, u2, v2],
                "up": [u1, v1 + inner, u2, v1 + inner + 0.5],
                "down": [u1, v2 - inner - 0.5, u2, v2 - inner],
            }
            elements.append(
                {
                    "from": [u1, 16 - v2, 8 - depth / 2],
                    "to": [u2, 16 - v1, 8 + depth / 2],
                    "faces": {
                        face: {"uv": uv, "texture": "#0"} for face, uv in faces.items()
                    },
                }
            )
    if group == "fish" and len(elements) > 32:
        raise ValueError(name + " exceeds the cuboid budget")
    return elements


def build(group, name):
    relative = "/".join(x for x in (group, name) if x)
    image = Image.open(TEXTURES / (relative + ".png")).convert("RGBA")
    if image.size != (32, 32):
        raise ValueError(relative + " is not 32px")
    model = {
        "gui_light": "front",
        "textures": {"0": "hnmt:item/" + relative, "particle": "hnmt:item/" + relative},
        "elements": geometry(group, name, image),
        "display": ROD_DISPLAY if group == "rod" else DISPLAY,
    }
    output = PACK / "models3d" / group / (name + ".json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(model, indent=2) + "\n")
    return len(model["elements"])


def main(group=None):
    for category, name, label in inventory():
        if group is None or category == group:
            print(category + "/" + name, build(category, name), "elements")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", choices=("fish", "rod", "bait", "dish", "extras"))
    args = parser.parse_args()
    main("" if args.group == "extras" else args.group)
