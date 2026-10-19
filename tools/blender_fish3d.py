"""Blender で魚の 3D モデル（直方体 elements の JSON）を作り、プレビューも描く（方法B）。

使い方:
  /Applications/Blender.app/Contents/MacOS/Blender --background --python resourcepack/tools/blender_fish3d.py

やること:
  1. 32x32 のテクスチャ（make_textures.py の出力）を読み、列ごとの「不透明な縦の連なり」を直方体にする。
  2. 直方体の厚み（奥行き）は、縦の連なりの長さから決める（胴の中央ほど厚く、尾・ひれは薄く）。
  3. 側面(north/south)は絵そのまま、上下・端は端のピクセルの色を引き伸ばす。テクスチャは魚1枚のまま。
  4. 同じ直方体を Blender のメッシュにして、プレビュー画像を描く。
出力:
  resourcepack/models3d/fish/<ID>.json       3D モデル（build_zip.sh 3d で pack に入れる。Git で管理する）
  resourcepack-build/preview3d/<ID>.png      Blender で描いたプレビュー
"""

import json
import math
import os

import bmesh
import bpy
from mathutils import Vector

ROOT = os.getcwd()  # リポジトリのルートで実行する
TEX_DIR = os.path.join(
    ROOT, "resourcepack", "assets", "hnmt", "textures", "item", "fish"
)
OUT_DIR = os.path.join(ROOT, "resourcepack", "models3d", "fish")
PREV_DIR = os.path.join(ROOT, "resourcepack-build", "preview3d")

FISH = [
    "unagi",
    "salmon",
    "kohada",
    "konoshiro",
    "tai",
    "hirame",
    "saba",
    "hamachi",
    "buri",
    "ika",
    "kanpachi",
    "maguro",
]
# 厚みの最大値(モデル単位 1/16 ブロック)、尾の始まる列(それ以降は薄く)、一定の厚み(薄い魚)
PARAMS = {
    "unagi": dict(tmax=1.8, flat=1.8),
    "hirame": dict(tmax=1.0, flat=1.0, tail_x=26),
    "ika": dict(tmax=3.0),
    "kohada": dict(tmax=2.4, tail_x=21),
    "salmon": dict(tmax=3.2, tail_x=24),
    "konoshiro": dict(tmax=3.4, tail_x=24),
    "tai": dict(tmax=3.6, tail_x=23),
    "saba": dict(tmax=3.0, tail_x=24),
    "hamachi": dict(tmax=3.2, tail_x=23),
    "buri": dict(tmax=3.8, tail_x=24),
    "kanpachi": dict(tmax=3.6, tail_x=24),
    "maguro": dict(tmax=4.4, tail_x=25),
}
THIN = 0.5
GRID = 32
UNIT = 16.0 / GRID  # 1ピクセル = 0.5 モデル単位


def load_alpha(fid):
    img = bpy.data.images.load(
        os.path.join(TEX_DIR, fid + ".png"), check_existing=False
    )
    w, h = img.size
    px = list(img.pixels)
    return [
        [px[((h - 1 - y) * w + x) * 4 + 3] > 0.5 for x in range(w)] for y in range(h)
    ], img


def runs_of(alpha, x):
    runs, y = [], 0
    while y < GRID:
        if alpha[y][x]:
            y0 = y
            while y < GRID and alpha[y][x]:
                y += 1
            runs.append((y0, y))
        else:
            y += 1
    return runs


def snap(v, step=0.25):
    return round(v / step) * step


def build_elements(fid, alpha):
    p = PARAMS[fid]
    cols = {x: runs_of(alpha, x) for x in range(GRID)}
    maxlen = max((b - a) for rs in cols.values() for a, b in rs) or 1
    blocks = []  # (x_from, x_to_exclusive, y0, y1, thickness)
    for x in range(GRID):
        for y0, y1 in cols[x]:
            n = y1 - y0
            if "flat" in p:
                th = p["flat"]
            else:
                th = p["tmax"] * (n / maxlen) ** 0.8
            if n < 3 or ("tail_x" in p and x >= p["tail_x"]):
                th = THIN
            if fid == "ika" and y0 >= 22:
                th = THIN
            if fid == "hirame" and n < 3:
                th = THIN
            th = snap(max(THIN, th))
            if blocks and blocks[-1][1] == x and blocks[-1][2:] == (y0, y1, th):
                blocks[-1] = (blocks[-1][0], x + 1, y0, y1, th)
            else:
                blocks.append((x, x + 1, y0, y1, th))
    elements = []
    for xa, xb, y0, y1, th in blocks:
        u1, u2 = xa * UNIT, xb * UNIT
        v1, v2 = y0 * UNIT, y1 * UNIT
        side = [u1, v1, u2, v2]
        e = {
            "from": [u1, 16 - v2, 8 - th / 2],
            "to": [u2, 16 - v1, 8 + th / 2],
            "faces": {
                "north": {"uv": side},
                "south": {"uv": side},
                "east": {"uv": [(xb - 1) * UNIT, v1, xb * UNIT, v2]},
                "west": {"uv": [xa * UNIT, v1, (xa + 1) * UNIT, v2]},
                "up": {"uv": [u1, v1, u2, v1 + UNIT]},
                "down": {"uv": [u1, v2 - UNIT, u2, v2]},
            },
        }
        elements.append(e)
    return elements


DISPLAY = {  # バニラの item/generated を元に、GUI だけ少し斜めにして立体感を出す
    "gui": {
        "rotation": [15, -30, 0],
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


def write_model(fid, elements):
    data = {
        "gui_light": "front",
        "textures": {"0": f"hnmt:item/fish/{fid}", "particle": f"hnmt:item/fish/{fid}"},
        "elements": [],
        "display": DISPLAY,
    }
    for e in elements:
        data["elements"].append(
            {
                "from": [round(v, 4) for v in e["from"]],
                "to": [round(v, 4) for v in e["to"]],
                "faces": {
                    k: {"uv": [round(u, 4) for u in f["uv"]], "texture": "#0"}
                    for k, f in e["faces"].items()
                },
            }
        )
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, fid + ".json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


# ---------------------------------------------------------------- Blender 側
def corner_sets(x1, y1, z1, x2, y2, z2):
    """各面の 4 隅（外から見て 左上→右上→右下→左下）。Minecraft の UV の向きに合わせる。"""
    return {
        "south": [(x1, y2, z2), (x2, y2, z2), (x2, y1, z2), (x1, y1, z2)],
        "north": [(x2, y2, z1), (x1, y2, z1), (x1, y1, z1), (x2, y1, z1)],
        "east": [(x2, y2, z2), (x2, y2, z1), (x2, y1, z1), (x2, y1, z2)],
        "west": [(x1, y2, z1), (x1, y2, z2), (x1, y1, z2), (x1, y1, z1)],
        "up": [(x1, y2, z1), (x2, y2, z1), (x2, y2, z2), (x1, y2, z2)],
        "down": [(x1, y1, z2), (x2, y1, z2), (x2, y1, z1), (x1, y1, z1)],
    }


def to_blender(p):
    x, y, z = p  # Minecraft: x右, y上, z手前 → Blender: X右, Y奥, Z上
    return Vector(((x - 8) / 8, -(z - 8) / 8, (y - 8) / 8))


def build_object(fid, elements, image):
    mesh = bpy.data.meshes.new(fid)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    for e in elements:
        (x1, y1, z1), (x2, y2, z2) = e["from"], e["to"]
        for name, corners in corner_sets(x1, y1, z1, x2, y2, z2).items():
            verts = [bm.verts.new(to_blender(c)) for c in corners]
            face = bm.faces.new(verts)
            u1, v1, u2, v2 = e["faces"][name]["uv"]
            tl, tr, br, bl = [(u1, v1), (u2, v1), (u2, v2), (u1, v2)]
            for loop, (u, v) in zip(face.loops, (tl, tr, br, bl)):
                loop[uv].uv = (u / 16.0, 1 - v / 16.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(fid, mesh)
    bpy.context.scene.collection.objects.link(obj)
    mat = bpy.data.materials.new(fid)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Closest"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.7
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    obj.data.materials.append(mat)
    return obj


def setup_scene():
    sc = bpy.context.scene
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    try:
        sc.render.engine = "BLENDER_EEVEE"
    except TypeError:
        sc.render.engine = "BLENDER_EEVEE_NEXT"
    sc.render.resolution_x = sc.render.resolution_y = 384
    sc.render.film_transparent = True
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 2.3
    yaw, pitch, dist = math.radians(42), math.radians(30), 6
    cam.location = (
        math.sin(yaw) * dist * math.cos(pitch) * -1,
        -math.cos(yaw) * dist * math.cos(pitch),
        math.sin(pitch) * dist,
    )
    sc.collection.objects.link(cam)
    direction = Vector((0, 0, 0)) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 3.5
    sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-30))
    sc.collection.objects.link(sun)
    world = bpy.data.worlds.new("w")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.9
    sc.world = world


def main():
    import subprocess
    import sys

    sys.path.insert(0, os.path.join(ROOT, "resourcepack", "tools"))
    subprocess.run(
        [
            "python3",
            os.path.join(ROOT, "resourcepack", "tools", "make_models.py"),
            "--group",
            "fish",
        ],
        check=True,
    )
    from blender_preview import render

    render("fish")


if __name__ == "__main__":
    main()
