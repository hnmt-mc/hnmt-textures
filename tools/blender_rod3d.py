"""Blender で釣竿の 3D モデル（直方体 elements の JSON）を作り、プレビューも描く（方法B）。

使い方（リポジトリのルートで）:
  /Applications/Blender.app/Contents/MacOS/Blender --background --python resourcepack/tools/blender_rod3d.py

16x16 のテクスチャを列ごとに直方体へ変換する（魚の blender_fish3d.py と同じ考え方）。
竿は厚み1.5、握りやリールなど縦に3マス以上つながる所は2.0、釣り糸は0.5。
通常用と投げた状態用（_cast）の2つを作る。
出力: resourcepack/models3d/rod/<ID>.json, <ID>_cast.json（Git で管理する）/ resourcepack-build/preview3d/rod_<ID>.png
"""
import json
import os
import sys

import bpy

sys.path.insert(0, os.path.join(os.getcwd(), "resourcepack", "tools"))
import blender_fish3d as F  # noqa: E402  (共通の部品を使う)

ROOT = os.getcwd()
TEX_DIR = os.path.join(ROOT, "resourcepack", "assets", "hnmt", "textures", "item", "rod")
OUT_DIR = os.path.join(ROOT, "resourcepack", "models3d", "rod")
RODS = ["bamboo", "keiryu_nami", "keiryu_jo", "iso_nami", "iso_jo", "fune_nami", "fune_jo"]
GRID = 16
LINE = (232, 232, 232)
TH_ROD, TH_WIDE, TH_LINE = 1.5, 2.0, 0.5

# バニラの item/generated（ground, head, fixed）と item/handheld_rod（手に持つ向き）を合わせたもの
DISPLAY = {
    "gui": {"rotation": [10, -25, 0], "translation": [0, 0, 0], "scale": [0.95, 0.95, 0.95]},
    "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.5, 0.5, 0.5]},
    "head": {"rotation": [0, 180, 0], "translation": [0, 13, 7], "scale": [1, 1, 1]},
    "fixed": {"rotation": [0, 180, 0], "scale": [1, 1, 1]},
    "thirdperson_righthand": {"rotation": [0, 90, 55], "translation": [0, 4.0, 2.5], "scale": [0.85, 0.85, 0.85]},
    "thirdperson_lefthand": {"rotation": [0, -90, -55], "translation": [0, 4.0, 2.5], "scale": [0.85, 0.85, 0.85]},
    "firstperson_righthand": {"rotation": [0, 90, 25], "translation": [0, 1.6, 0.8], "scale": [0.68, 0.68, 0.68]},
    "firstperson_lefthand": {"rotation": [0, -90, -25], "translation": [0, 1.6, 0.8], "scale": [0.68, 0.68, 0.68]},
}


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
    """縦の連なり（釣り糸かどうかで分ける）を (y0, y1, 糸か) で返す。"""
    runs, y = [], 0
    while y < GRID:
        c = grid[y][x]
        if c is None:
            y += 1
            continue
        line = c == LINE
        y0 = y
        while y < GRID and grid[y][x] is not None and (grid[y][x] == LINE) == line:
            y += 1
        runs.append((y0, y, line))
    return runs


def build_elements(grid):
    elements = []
    for x in range(GRID):
        for y0, y1, line in column_runs(grid, x):
            th = TH_LINE if line else (TH_WIDE if y1 - y0 >= 3 else TH_ROD)
            side = [x, y0, x + 1, y1]
            inner = 1 if (y1 - y0 >= 3 and not line) else 0  # 縁取りの暗い1マスを避け、内側の色を上下面に使う
            elements.append({
                "from": [x, 16 - y1, 8 - th / 2], "to": [x + 1, 16 - y0, 8 + th / 2],
                "faces": {"north": {"uv": side}, "south": {"uv": side},
                          "east": {"uv": [x, y0, x + 1, y1]}, "west": {"uv": [x, y0, x + 1, y1]},
                          "up": {"uv": [x, y0 + inner, x + 1, y0 + inner + 1]}, "down": {"uv": [x, y1 - 1 - inner, x + 1, y1 - inner]}},
            })
    return elements


def write_model(name, elements):
    data = {"gui_light": "front",
            "textures": {"0": f"hnmt:item/rod/{name}", "particle": f"hnmt:item/rod/{name}"},
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
    for rid in RODS:
        for name in (rid, rid + "_cast"):
            grid, image = load_pixels(name)
            elements = build_elements(grid)
            write_model(name, elements)
            if name == rid:
                obj = F.build_object(rid, elements, image)
                bpy.context.scene.render.filepath = os.path.join(F.PREV_DIR, f"rod_{rid}.png")
                bpy.ops.render.render(write_still=True)
                bpy.data.objects.remove(obj, do_unlink=True)
            print(name, len(elements), "elements")


main()
