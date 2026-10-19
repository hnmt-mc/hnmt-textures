"""Blender 4.x以降で、直方体だけの保冷箱とJava版アイテムモデルを生成する。

実行例:
  blender --background --factory-startup --python resourcepack/tools/blender_coolers.py -- --render

既存のシーンや配布パックは変更しない。成果物はresourcepack-build/coolerへ出す。
PNGの生成には標準ライブラリだけを使い、色数・輪郭・UVを固定する。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct
import sys
import zlib
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[2]
SIZES = {"small": (10, 6, 7), "medium": (12, 7, 8), "large": (14, 8, 9)}
# 輪郭・本体の影/基準/明部・蓋・氷・明るい灰色・留め具/縁の計8色。
PALETTES = {
    "small": ("172729", "294e50", "4f7975", "6f9690", "cad6d4", "a5d5df", "e5eeea", "ae9774"),
    "medium": ("121f30", "203a57", "365777", "587d97", "cad6d4", "a5d5df", "e5eeea", "ae9774"),
    "large": ("111824", "182b43", "243e5c", "46627d", "c7d3d8", "9ccbd8", "e2ebe8", "c8a65c"),
}
# PNGの左上原点の矩形。面同士で共有し、1枚32x32に収める。
PANELS = {
    "body": (0, 0, 16, 10), "side": (16, 0, 26, 10),
    "lid_top": (0, 10, 16, 20), "bottom": (16, 10, 26, 20),
    "lid": (0, 20, 16, 24), "lid_side": (16, 20, 26, 24),
    "handle": (0, 24, 16, 28), "latch": (16, 24, 20, 28),
    "ice": (20, 24, 24, 28), "ice_top": (24, 24, 28, 28),
}
FACE_VERTICES = {
    "north": (1, 0, 3, 2), "south": (4, 5, 6, 7),
    "west": (0, 4, 7, 3), "east": (5, 1, 2, 6),
    "up": (3, 7, 6, 2), "down": (0, 1, 5, 4),
}
DISPLAY = {
    "gui": {"rotation": [30, 225, 0], "translation": [0, 0, 0], "scale": [0.92] * 3},
    "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.5] * 3},
    "fixed": {"rotation": [0, 180, 0], "translation": [0, 0, 0], "scale": [0.8] * 3},
    "firstperson_righthand": {"rotation": [0, -45, 0], "translation": [0, 1, -1], "scale": [0.55] * 3},
    "thirdperson_righthand": {"rotation": [75, 45, 0], "translation": [0, 2, 0], "scale": [0.45] * 3},
}


def texture_indices(variant):
    """ぼかしや乱数を使わず、1px輪郭と少数の色面で描く。"""
    if variant not in SIZES:
        raise ValueError(f"Unknown cooler variant: {variant}")
    pixels = [[0] * 32 for _ in range(32)]
    gold = variant == "large"
    for panel, (x0, y0, x1, y1) in PANELS.items():
        for y in range(y0 + 1, y1 - 1):
            for x in range(x0 + 1, x1 - 1):
                dx, dy = x - x0, y - y0
                if panel in ("body", "side"):
                    color = 3 if dy == 1 or (dy == 2 and dx == 2) else 1 if dy >= y1 - y0 - 3 else 2
                    # 素朴な板の継ぎ目。規則的な全面ノイズは入れない。
                    if dx in (4, 11) and dy > 2:
                        color = 1
                    if gold and (dx in (1, x1 - x0 - 2) or dy in (1, y1 - y0 - 2)):
                        color = 7
                elif panel == "lid_top":
                    color = 6 if dy < 3 else 4
                    if dx in (3, 12) and 3 <= dy <= 6:
                        color = 5
                    if gold and (dx in (1, 14) or dy in (1, 8)):
                        color = 7
                elif panel == "bottom":
                    color = 1
                elif panel in ("lid", "lid_side"):
                    color = 6 if dy == 1 else 4
                    if gold and dy == 2:
                        color = 7
                elif panel == "handle":
                    color = 7 if dy == 1 else 1
                elif panel == "latch":
                    color = 7 if dx == 1 else 4
                else:
                    color = 6 if panel == "ice_top" or dx == 1 else 5
                pixels[y][x] = color
    return pixels


def png_bytes(variant):
    """指定8色をそのままRGBA PNGへ保存し、色管理による色数増加を避ける。"""
    palette = [bytes.fromhex(value) + b"\xff" for value in PALETTES[variant]]
    raw = b"".join(b"\x00" + b"".join(palette[i] for i in row) for row in texture_indices(variant))

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 32, 32, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def element(name, low, high, side, top=None, bottom=None, omit=()):
    faces = {}
    for direction in FACE_VERTICES:
        if direction in omit:
            continue
        panel = top if direction == "up" and top else bottom if direction == "down" and bottom else side
        if direction in ("east", "west") and side in ("body", "lid"):
            panel = "side" if side == "body" else "lid_side"
        faces[direction] = {"uv": [p / 2 for p in PANELS[panel]], "texture": "#0"}
    return {"name": name, "from": list(low), "to": list(high), "faces": faces}


def model(variant):
    """本体+蓋+留め具+角形の持ち手3個。中/大だけ氷を1/2個足す。"""
    width, height, depth = SIZES[variant]
    x0, x1 = 8 - width / 2, 8 + width / 2
    z0, z1 = 8 - depth / 2, 8 + depth / 2
    floor = 1.0
    lid_y = floor + height + 0.25
    lid_top = lid_y + 2
    parts = [
        element("body", (x0, floor, z0), (x1, floor + height, z1), "body", "lid_top", "bottom"),
        element("lid", (x0, lid_y, z0), (x1, lid_top, z1), "lid", "lid_top", "bottom"),
        element("latch", (7, lid_y - 1, z0 - 1), (9, lid_y + 1, z0), "latch"),
        element("handle_left", (5, lid_top, 7.5), (6, lid_top + 1.25, 8.5), "handle", omit=("up", "down")),
        element("handle_right", (10, lid_top, 7.5), (11, lid_top + 1.25, 8.5), "handle", omit=("up", "down")),
        element("handle_grip", (5, lid_top + 1.25, 7.5), (11, lid_top + 2, 8.5), "handle"),
    ]
    if variant != "small":
        parts.append(element("ice_left", (x0 + 1, lid_top, z1 - 2.5), (x0 + 3, lid_top + 0.5, z1 - 1), "ice", "ice_top", omit=("down",)))
    if variant == "large":
        parts.append(element("ice_right", (x1 - 3, lid_top, z1 - 2.5), (x1 - 1, lid_top + 0.5, z1 - 1), "ice", "ice_top", omit=("down",)))
    data = {"credit": "HNMT procedural cooler", "texture_size": [32, 32], "gui_light": "front",
            "textures": {"0": f"hnmt:item/cooler/{variant}", "particle": "#0"}, "elements": parts, "display": DISPLAY}
    validate_model(data)
    return data


def validate_model(data):
    for part in data["elements"]:
        if not all(0 <= a < b <= 16 for a, b in zip(part["from"], part["to"])):
            raise ValueError(f"Invalid cooler bounds: {part['name']}")
        for face in part["faces"].values():
            u0, v0, u1, v1 = face["uv"]
            if not (0 <= u0 < u1 <= 16 and 0 <= v0 < v1 <= 16):
                raise ValueError(f"Invalid cooler UV: {part['name']}")


def write_assets(output):
    """確認用コピーと、指定の参照先へ配置済みの単独パックを出力する。"""
    texture_dir = output / "pack/assets/hnmt/textures/item/cooler"
    model_dir = output / "pack/assets/hnmt/models/item/cooler"
    item_dir = output / "pack/assets/hnmt/items/cooler"
    for directory in (output, texture_dir, model_dir, item_dir):
        directory.mkdir(parents=True, exist_ok=True)
    all_models = {}
    for variant in SIZES:
        data = model(variant)
        encoded = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        texture = png_bytes(variant)
        (output / f"cooler_{variant}.png").write_bytes(texture)
        (output / f"cooler_{variant}.json").write_text(encoded, encoding="utf-8")
        (texture_dir / f"{variant}.png").write_bytes(texture)
        (model_dir / f"{variant}.json").write_text(encoded, encoding="utf-8")
        (item_dir / f"{variant}.json").write_text(json.dumps({"model": {"type": "minecraft:model", "model": f"hnmt:item/cooler/{variant}"}}, indent=2) + "\n", encoding="utf-8")
        all_models[variant] = data
    # 対象バージョンは既存パックと同じ1.21.11。配布中のパック自体は変更しない。
    (output / "pack/pack.mcmeta").write_text(json.dumps({"pack": {"description": "HNMT cooler models", "min_format": 75, "max_format": 75}}, indent=2) + "\n", encoding="utf-8")
    with ZipFile(output / "hnmt-coolers-pack.zip", "w", ZIP_DEFLATED) as archive:
        for file in sorted((output / "pack").rglob("*")):
            if file.is_file():
                archive.write(file, file.relative_to(output / "pack"))
    return all_models


def vertices(part):
    x0, y0, z0 = part["from"]
    x1, y1, z1 = part["to"]
    return [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
            (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]


def face_uv(direction, rect):
    """Minecraftの面ごとの向きに合わせ、PNG上原点からBlender下原点へ変換する。"""
    u0, v0, u1, v1 = [p / 16 for p in rect]
    if direction == "up":
        coords = [(u0, v0), (u0, v1), (u1, v1), (u1, v0)]
    else:
        coords = [(u0, v1), (u1, v1), (u1, v0), (u0, v0)]
    return [(u, 1 - v) for u, v in coords]


def make_scene(output, models):
    import bpy
    from mathutils import Vector

    if bpy.app.version < (4, 0, 0):
        raise RuntimeError("Blender 4.0 or newer is required")
    scene = bpy.data.scenes.new("HNMT Coolers")
    engines = scene.render.bl_rna.properties["engine"].enum_items.keys()
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.render.filter_size = 0.01
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast" if "Medium High Contrast" in scene.view_settings.bl_rna.properties["look"].enum_items.keys() else "None"
    scene.world = bpy.data.worlds.new("Cooler World")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.055, 0.075, 0.10, 1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7
    for index, (variant, data) in enumerate(models.items()):
        group = bpy.data.collections.new(f"Cooler {variant}")
        scene.collection.children.link(group)
        image = bpy.data.images.load(str(output / f"cooler_{variant}.png"), check_existing=False)
        image.pack()
        material = bpy.data.materials.new(f"Cooler {variant} 8 colors")
        material.use_nodes = True
        nodes = material.node_tree.nodes
        texture = nodes.new("ShaderNodeTexImage")
        texture.image = image
        texture.interpolation = "Closest"
        texture.extension = "EXTEND"
        shader = nodes.get("Principled BSDF")
        shader.inputs["Roughness"].default_value = 1
        material.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
        for part in data["elements"]:
            coords = [((x - 8) / 16 + (index - 1) * 1.15, (8 - z) / 16, y / 16) for x, y, z in vertices(part)]
            directions = list(part["faces"])
            mesh = bpy.data.meshes.new(f"{variant}_{part['name']}")
            mesh.from_pydata(coords, [], [FACE_VERTICES[direction] for direction in directions])
            mesh.update()
            uv_layer = mesh.uv_layers.new(name="Minecraft UV")
            for polygon, direction in zip(mesh.polygons, directions):
                for loop_index, uv in zip(polygon.loop_indices, face_uv(direction, part["faces"][direction]["uv"])):
                    uv_layer.data[loop_index].uv = uv
            obj = bpy.data.objects.new(mesh.name, mesh)
            group.objects.link(obj)
            obj.data.materials.append(material)
            obj["minecraft_element"] = part["name"]
        print(f"COOLER {variant}: {len(data['elements'])} cuboids, {sum(len(p['faces']) for p in data['elements'])} quads", flush=True)

    def aim(obj, target):
        obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()

    camera_data = bpy.data.cameras.new("Cooler Camera")
    camera = bpy.data.objects.new("Cooler Camera", camera_data)
    scene.collection.objects.link(camera)
    camera.location = (2.0, 5.5, 3.3)
    aim(camera, (0, 0, 0.4))
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 4.35
    scene.camera = camera
    for name, position, power, size in [("Key", (0, 3, 5), 450, 4), ("Fill", (-3, -1, 3), 250, 3)]:
        light_data = bpy.data.lights.new(name, "AREA")
        light_data.energy = power
        light_data.shape = "DISK"
        light_data.size = size
        light = bpy.data.objects.new(name, light_data)
        scene.collection.objects.link(light)
        light.location = position
        aim(light, (0, 0, 0.4))
    return scene


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "resourcepack-build/cooler")
    parser.add_argument("--render", action="store_true", help="3種類を並べたBlenderプレビューも出力")
    args = parser.parse_args(argv)
    output = args.output.expanduser().resolve()
    models = write_assets(output)
    scene = make_scene(output, models)
    if args.render:
        import bpy
        scene.render.filepath = str(output / "preview.png")
        bpy.ops.render.render(write_still=True, scene=scene.name)
    # factory-startup で起動するので、いま開いているファイルには、このスクリプトのデータしかない。
    import bpy
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "coolers.blend"), copy=True)
    print(f"COOLER_OUTPUT {output}", flush=True)


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
