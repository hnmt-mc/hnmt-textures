"""Blender で餌の 3D モデル（直方体 elements の JSON）を作り、プレビューも描く。

使い方（リポジトリのルートで）:
  /Applications/Blender.app/Contents/MacOS/Blender --background --python resourcepack/tools/blender_bait3d.py

16x16 のテクスチャを列ごとに直方体へ変換する（釣竿の blender_rod3d.py と同じ考え方）。縦に3マス以上つながる所は厚み2.0、それ以外は1.5。
出力: resourcepack/models3d/bait/<ID>.json（Git で管理する）/ resourcepack-build/preview3d/bait_<ID>.png
"""
import json
import os
import sys

import bpy

sys.path.insert(0, os.path.join(os.getcwd(), "resourcepack", "tools"))
import blender_fish3d as F  # noqa: E402  (共通の部品を使う)

ROOT = os.getcwd()
TEX_DIR = os.path.join(ROOT, "resourcepack", "assets", "hnmt", "textures", "item", "bait")
OUT_DIR = os.path.join(ROOT, "resourcepack", "models3d", "bait")
BAITS = ["mimizu", "ebi", "iwashi", "ika_no_mi"]
GRID = 16
TH_THIN, TH_WIDE = 1.5, 2.0

DISPLAY = F.DISPLAY   # 魚と同じ（バニラの item/generated を元にした向き）


def load_pixels(name):
    img = bpy.data.images.load(os.path.join(TEX_DIR, name + ".png"), check_existing=False)
    w, h = img.size
    px = list(img.pixels)
    grid = [[None] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            i = ((h - 1 - y) * w + x) * 4
            if px[i + 3] > 0.5:
                grid[y][x] = tuple(int(round(px[i + k] * 255)) for k in range(3))
    return grid, img


def column_runs(grid, x):
    """縦の連なりを (y0, y1) で返す。"""
    runs, y = [], 0
    while y < GRID:
        if grid[y][x] is None:
            y += 1
            continue
        y0 = y
        while y < GRID and grid[y][x] is not None:
            y += 1
        runs.append((y0, y))
    return runs


def build_elements(grid):
    elements = []
    for x in range(GRID):
        for y0, y1 in column_runs(grid, x):
            th = TH_WIDE if y1 - y0 >= 3 else TH_THIN
            side = [x, y0, x + 1, y1]
            inner = 1 if y1 - y0 >= 3 else 0  # 縁取りの暗い1マスを避け、内側の色を上下面に使う
            elements.append({
                "from": [x, 16 - y1, 8 - th / 2], "to": [x + 1, 16 - y0, 8 + th / 2],
                "faces": {"north": {"uv": side}, "south": {"uv": side},
                          "east": {"uv": [x, y0, x + 1, y1]}, "west": {"uv": [x, y0, x + 1, y1]},
                          "up": {"uv": [x, y0 + inner, x + 1, y0 + inner + 1]}, "down": {"uv": [x, y1 - 1 - inner, x + 1, y1 - inner]}},
            })
    return elements


def write_model(name, elements):
    data = {"gui_light": "front",
            "textures": {"0": f"hnmt:item/bait/{name}", "particle": f"hnmt:item/bait/{name}"},
            "elements": [{"from": e["from"], "to": e["to"],
                          "faces": {k: {"uv": f["uv"], "texture": "#0"} for k, f in e["faces"].items()}}
                         for e in elements],
            "display": DISPLAY}
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, name + ".json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def main():
    os.makedirs(F.PREV_DIR, exist_ok=True)
    F.setup_scene()
    for bid in BAITS:
        grid, image = load_pixels(bid)
        elements = build_elements(grid)
        write_model(bid, elements)
        obj = F.build_object(bid, elements, image)
        bpy.context.scene.render.filepath = os.path.join(F.PREV_DIR, f"bait_{bid}.png")
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(obj, do_unlink=True)
        print(bid, len(elements), "elements")


main()
