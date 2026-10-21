#!/usr/bin/env python3
"""Export cuboid-only, single-texture item models from 32px source silhouettes."""

import json
import math
from PIL import Image
from make_rice_models import RICE
from artwork import PACK, TEXTURES, FISH, RODS, BAITS, DISHES, EXTRAS, OUTLINE as OUTLINE_HEX

DISPLAY = {
    "gui": {
        "rotation": [30, -42, 0],
        "translation": [0, 0, 0],
        "scale": [0.9, 0.9, 0.9],
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
        "rotation": [28, -40, 0],
        "translation": [0, 0, 0],
        "scale": [0.9, 0.9, 0.9],
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
        ("rice", RICE),
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


FISH_DEPTH = {  # 胴のいちばん厚い所の奥行き（1/16ブロック）
    "unagi": 4.5, "hirame": 3.5, "ika": 4.6, "kohada": 6.0, "salmon": 7.2,
    "konoshiro": 6.6, "tai": 8.0, "saba": 6.6, "hamachi": 7.2, "buri": 8.6,
    "kanpachi": 8.0, "maguro": 10.4,
}
ROUND_GROUPS = ("dish", "bait")
ROUND_FISH = ()  # 輪切りにする魚（今はなし。イカも、上から見た絵なので、ほかの魚と同じ作り）  # 横から見た絵を、行ごとの輪切り（円柱）にする
ROUND_EXTRAS = ("rice", "ikura")
FISH_BUDGET = 160
OUTLINES = {tuple(int(OUTLINE_HEX[i : i + 2], 16) for i in (1, 3, 5)), (58, 62, 84)}  # 旧の輪郭色と、描き直した絵の輪郭色


def slice_count(height):
    return 1 if height <= 3 else min(5, 2 + height // 6)


def quad(x0, x1, y0, y1, depth, side_inner=False, up_row=None, down_row=None, side_pixels=None, front=None, up_span=None, down_span=None):
    """列 [x0,x1)・行 [y0,y1)（ピクセル）の、奥行き depth の直方体。"""
    u1, u2, v1, v2 = x0 / 2, x1 / 2, y0 / 2, y1 / 2
    inner = 0.5 if y1 - y0 >= 2 else 0  # 輪郭の1行内側の色を、上面・下面に使う
    side = 0.5 if side_inner and x1 - x0 >= 3 else 0  # 輪切りの端の面にも、輪郭の内側の色を使う
    faces = {
        "north": [u1, v1, u2, v2],
        "south": [u1, v1, u2, v2],
        "west": [u1 + side, v1, u1 + side + 0.5, v2],
        "east": [u2 - side - 0.5, v1, u2 - side, v2],
        "up": [u1, v1 + inner, u2, v1 + inner + 0.5],
        "down": [u1, v2 - inner - 0.5, u2, v2 - inner],
    }
    if up_row is not None:  # 輪郭の行ではなく、その下の、中身の行の色を上面に使う
        a, b = up_span or (x0, x1)  # 行の両端の輪郭は除き、中身の色だけを、面いっぱいに伸ばす
        faces["up"] = [a / 2, up_row / 2, b / 2, up_row / 2 + 0.5]
    if down_row is not None:
        a, b = down_span or (x0, x1)
        faces["down"] = [a / 2, down_row / 2, b / 2, down_row / 2 + 0.5]
    if side_pixels is not None:  # 端の面は、輪郭の内側にある、最初の中身の1ピクセルの色にする
        (xl, yl), (xr, yr) = side_pixels
        faces["west"] = [xl / 2, yl / 2, xl / 2 + 0.5, yl / 2 + 0.5]
        faces["east"] = [xr / 2, yr / 2, xr / 2 + 0.5, yr / 2 + 0.5]
    return {
        "from": [u1, 16 - v2, (front - depth) if front is not None else 8 - depth / 2],
        "to": [u2, 16 - v1, front if front is not None else 8 + depth / 2],
        "faces": {f: {"uv": uv, "texture": "#0"} for f, uv in faces.items()},
    }


def merge(blocks):
    """隣の列で、高さと奥行きが同じ直方体を、1つにまとめる。(x0,x1,y0,y1,depth)"""
    merged = []
    for block in blocks:
        for i, old in enumerate(merged):
            if old[1] == block[0] and old[2:] == block[2:]:
                merged[i] = (old[0], block[1]) + old[2:]
                break
        else:
            merged.append(block)
    return merged


def fish_loft(name, columns, image):
    """胴の断面を楕円にして、背と腹に向かって薄くなる、丸みのある魚にする。"""
    occupied = [x for x, runs in columns.items() if runs]
    first, span = min(occupied), max(occupied) - min(occupied) + 1
    top = FISH_DEPTH[name]
    blocks = []
    for x in occupied:
        progress = (x - first + 0.5) / span
        along = max(0.35, math.sin(math.pi * progress) ** 0.6)
        for y0, y1 in columns[x]:
            n = slice_count(y1 - y0)
            for i in range(n):
                a, b = y0 + (y1 - y0) * i // n, y0 + (y1 - y0) * (i + 1) // n
                t = ((i + 0.5) / n) * 2 - 1
                depth = 0.5 if y1 - y0 <= 3 else top * along * math.sqrt(max(0.0, 1 - t * t * 0.85))
                if not any(is_body_pixel(image, x, yy) for yy in range(a, b)):
                    depth = 0.5  # 輪郭の線だけの所は、薄い板にする（厚みを付けると、暗い壁になる）
                blocks.append((x, x + 1, a, b, max(0.5, round(depth * 4) / 4)))
    elements = []
    for x0, x1, y0, y1, depth in merge(blocks):
        mid = (x0 + x1) // 2
        # 輪郭の暗い行は、上面・下面・端の面には使わない。その列の、中身の行の色を使う
        up = next((r for r in range(y0, min(32, y1 + 3)) if is_body_pixel(image, mid, r)), y0)
        down = next((r for r in range(y1 - 1, max(-1, y0 - 3), -1) if is_body_pixel(image, mid, r)), y1 - 1)
        sides = ((x0, up), (x1 - 1, up)) if is_body_pixel(image, x0, up) and is_body_pixel(image, x1 - 1, up) else None
        elements.append(quad(x0, x1, y0, y1, depth, up_row=up, down_row=down, side_pixels=sides))
    return elements


def solid(image, x, y):
    pixel = image.getpixel((x, y))
    return pixel[3] > 0


def is_body_pixel(image, x, y):
    pixel = image.getpixel((x, y))
    return pixel[3] > 0 and pixel[:3] not in OUTLINES


def revolve(image, cap, ratio, uniform=None):
    """絵の各行を、横幅に比例した奥行きの輪切りにする（丼・握り・餌など）。正面は絵のまま、奥行きは後ろへ伸ばす。"""
    blocks = []
    for y in range(32):
        x = 0
        while x < 32:
            if not solid(image, x, y):
                x += 1
                continue
            start = x
            while x < 32 and solid(image, x, y):
                x += 1
            depth = uniform or max(1.0, min(cap, round((x - start) / 2 * ratio * 4) / 4))
            # 輪郭の線は、正面の薄い板にする（奥行きまで伸ばすと、側面に暗い壁ができる）。中身だけに奥行きを付ける
            segments = []
            for xx in range(start, x):
                thin = not is_body_pixel(image, xx, y)
                if segments and segments[-1][2] == thin:
                    segments[-1][1] = xx + 1
                else:
                    segments.append([xx, xx + 1, thin])
            for a, b, thin in segments:
                blocks.append((a, b, y, y + 1, 0.5 if thin else depth))
    # 縦に隣り合う、同じ横幅・奥行きの行をまとめる
    merged = []
    for block in blocks:
        for i, old in enumerate(merged):
            if old[3] == block[2] and (old[0], old[1], old[4]) == (block[0], block[1], block[4]):
                merged[i] = old[:3] + (block[3], old[4])
                break
        else:
            merged.append(block)
    def is_body(x, y):
        pixel = image.getpixel((x, y))
        return pixel[3] > 0 and pixel[:3] not in OUTLINES

    # 正面を同じ平面にそろえ、正面から見ると、元の2Dの絵そのままに見える。奥行きは、後ろへ伸ばす
    front = 8 + max(block[4] for block in merged) / 2  # 薄い輪郭の板は、この正面の平面に置く
    elements = []
    for x0, x1, y0, y1, depth in merged:
        mid = (x0 + x1) // 2
        up = next((r for r in range(y0, min(32, y1 + 3)) if is_body(mid, r)), y0)
        if up + 1 < 32 and is_body(mid, up + 1):
            up += 1  # 縁の影の行を飛ばし、ネタ・具そのものの色を、上面に使う
        down = next((r for r in range(y1 - 1, max(-1, y0 - 3), -1) if is_body(mid, r)), y1 - 1)
        def span(r):
            body = [x for x in range(x0, x1) if is_body(x, r)]
            return (body[0], body[-1] + 1) if body else (x0, x1)

        row = y0 if is_body(mid, y0) else up
        xs = [x for x in range(x0, x1) if is_body(x, row)]
        sides = ((xs[0], row), (xs[-1], row)) if xs else None
        elements.append(quad(x0, x1, y0, y1, depth, side_inner=True, up_row=up, down_row=down, side_pixels=sides, front=front, up_span=span(up), down_span=span(down)))
    return elements


def geometry(group, name, image):
    if group == "fish" and name in ROUND_FISH:
        return revolve(image, 5, 0.6)
    if group == "dish" and name.startswith("nigiri_"):
        return revolve(image, 11, 0.7, uniform=9.0)  # シャリとネタの奥行きを、そろえる
    if group in ROUND_GROUPS or (group == "" and name in ROUND_EXTRAS):
        return revolve(image, 11 if group == "dish" else 6, 0.7)
    columns = {x: runs(image, x) for x in range(32)}
    # The side faces retain exact texture alpha. Coalescing only the cross section limits
    # complex fin silhouettes to one cuboid per column, without another texture or rotation.
    if group == "fish" and sum(map(len, columns.values())) > 32:
        columns = {x: ([(r[0][0], r[-1][1])] if r else []) for x, r in columns.items()}
    if group == "fish":
        elements = fish_loft(name, columns, image)
        if len(elements) > FISH_BUDGET:
            raise ValueError(name + " exceeds the cuboid budget")
        return elements
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
                    else 2.0 if height < 5 else 4.25
                )
            u1, u2 = x / 2, (x + 1) / 2
            v1, v2 = top / 2, bottom / 2
            # 輪郭の暗い行は、上面・下面・端の面には使わない（暗い段ができるため）。その列の、中身の行だけを使う
            body = [y for y in range(top, bottom) if image.getpixel((x, y))[:3] not in OUTLINES]
            b0, b1 = (body[0], body[-1] + 1) if body else (top, bottom)
            faces = {
                "north": [u1, v1, u2, v2],
                "south": [u1, v1, u2, v2],
                "west": [u1, b0 / 2, u2, b1 / 2],
                "east": [u1, b0 / 2, u2, b1 / 2],
                "up": [u1, b0 / 2, u2, b0 / 2 + 0.5],
                "down": [u1, b1 / 2 - 0.5, u2, b1 / 2],
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
    if group == "rice":
        # Blockbench で書き出した編集結果を維持する。再制作は専用の手順で行う。
        path = PACK / "models3d/rice" / (name + ".json")
        return len(json.loads(path.read_text())["elements"])
    if group == "dish":
        from make_food_models import build as build_dish
        return len(build_dish(name)["elements"])
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
        if group is None and category == "rod":
            continue  # 釣竿は、3D版でも平らなモデルのまま（--group rod を指定したときだけ作る）
        if group is None or category == group:
            print(category + "/" + name, build(category, name), "elements")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", choices=("fish", "rod", "bait", "dish", "rice", "extras"))
    args = parser.parse_args()
    main("" if args.group == "extras" else args.group)
