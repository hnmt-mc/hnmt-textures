"""Java 版のモデル（直方体の elements）を、統合版（Bedrock）のジオメトリへ直す。

座標の決まり（Geyser の変換 mod Rainbow の挙動と同じ）:
- 中心を (8, 0, 8) に寄せる。x 軸は逆向きなので、原点の x は -(x + 幅) にする。
- 上と下の面の UV は、始点と終点を入れ替える。
- 回転は、x 軸だけ角度の向きを逆にする。軸の中心（pivot）も x を逆にする。
- UV は Java では 0〜16 だが、統合版は画素なので、テクスチャの大きさに合わせて拡大する。
"""
import json
import os
import re
import shutil
import struct
import sys
import uuid

FORMAT_VERSION = "1.21.0"
BONE = "model"
NAMESPACE = "hnmt"
ENGINE_VERSION = [1, 21, 0]
FACES = ("north", "south", "east", "west", "up", "down")


def clean(value):
    """-0.0 を 0 にし、小数の誤差を丸める。整数になるものは整数で書く。"""
    rounded = round(float(value), 5)
    if rounded == 0:
        return 0
    return int(rounded) if rounded == int(rounded) else rounded


def convert_element(element, uv_space, texture_px):
    """直方体1つを、統合版の cube にする。uv_space は Java の UV の範囲、texture_px はテクスチャの画素数。"""
    start = [element["from"][0] - 8, element["from"][1], element["from"][2] - 8]
    end = [element["to"][0] - 8, element["to"][1], element["to"][2] - 8]
    origin = [min(a, b) for a, b in zip(start, end)]
    size = [abs(a - b) for a, b in zip(start, end)]
    origin[0] = -(origin[0] + size[0])

    scale_u = texture_px[0] / uv_space[0]
    scale_v = texture_px[1] / uv_space[1]
    uv = {}
    for name in FACES:
        face = element["faces"].get(name)
        if face is None:
            continue
        u1, v1, u2, v2 = face["uv"]
        if name in ("up", "down"):
            u1, v1, u2, v2 = u2, v2, u1, v1
        uv[name] = {"uv": [clean(u1 * scale_u), clean(v1 * scale_v)],
                    "uv_size": [clean((u2 - u1) * scale_u), clean((v2 - v1) * scale_v)]}

    cube = {"origin": [clean(v) for v in origin], "size": [clean(v) for v in size], "uv": uv}
    rotation = element.get("rotation")
    if rotation:
        angle = rotation["angle"]
        axis = rotation["axis"]
        cube["pivot"] = [clean(-(rotation["origin"][0] - 8)), clean(rotation["origin"][1]), clean(rotation["origin"][2] - 8)]
        cube["rotation"] = [clean(-angle if axis == "x" else 0), clean(angle if axis == "y" else 0), clean(angle if axis == "z" else 0)]
    return cube


def model_to_geometry(model, identifier, texture_px):
    """Java のモデル1つを、統合版のジオメトリのファイルの中身にする。"""
    elements = model.get("elements") or []
    if not elements:
        raise ValueError("elements がありません: " + identifier)
    uv_space = tuple(model.get("texture_size", (16, 16)))
    cubes = [convert_element(element, uv_space, texture_px) for element in elements]
    low = [min(c["origin"][i] for c in cubes) for i in range(3)]
    high = [max(c["origin"][i] + c["size"][i] for c in cubes) for i in range(3)]
    pivot = [clean((a + b) / 2) for a, b in zip(low, high)]
    return {
        "format_version": FORMAT_VERSION,
        "minecraft:geometry": [{
            "description": {
                "identifier": "geometry." + identifier,
                "texture_width": texture_px[0],
                "texture_height": texture_px[1],
                "visible_bounds_width": 4,
                "visible_bounds_height": 4,
                "visible_bounds_offset": [0, 0.75, 0],
            },
            "bones": [{"name": BONE, "pivot": pivot, "binding": "q.item_slot_to_bone_name(context.item_slot)", "cubes": cubes}],
        }],
    }


def png_size(data):
    """PNG の先頭（IHDR）から、幅と高さを読む。"""
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError("PNG ではありません")
    return struct.unpack(">II", data[16:24])


def safe_name(item_id):
    """統合版の識別名に使えるよう、スラッシュを下線に直す。"""
    return item_id.replace("/", "_")


# ---- 手に持ったとき・頭に乗せたときの向き（Java の display から、統合版のアニメーションへ） ----

def _display(display, key):
    entry = display.get(key, {})
    return (entry.get("rotation", [0, 0, 0]), entry.get("translation", [0, 0, 0]), entry.get("scale", [1, 1, 1]))


def display_to_animations(display, identifier):
    """display の firstperson・thirdperson・head を、3つのアニメーションにする。軸の入れ替えは Rainbow の挙動と同じ。"""
    rotation, translation, scale = _display(display, "firstperson_righthand")
    # 一人称の回転は、Rainbow の式と違う（実機の統合版で見比べて、一番見やすかった向きに合わせた）
    first = {"rotation": [-rotation[1], rotation[2], rotation[0]],
             "position": [-translation[1], 12.5 + translation[2], translation[0]], "scale": scale}
    rotation, translation, scale = _display(display, "thirdperson_righthand")
    third = {"rotation": [90, -rotation[2], -rotation[1]],
             "position": [-translation[0], 12.5 + translation[2], -translation[1]], "scale": scale}
    rotation, translation, scale = _display(display, "head")
    head = {"rotation": [-rotation[0], -rotation[1], rotation[2]],
            "position": [translation[0] * -0.655, translation[1] * 0.655 + 20, translation[2] * 0.655],
            "scale": [value * 0.655 for value in scale]}

    def animation(transform):
        return {"loop": True, "bones": {BONE: {key: [clean(v) for v in transform[key]] for key in ("position", "rotation", "scale")}}}

    return {"format_version": "1.8.0", "animations": {
        "animation.%s.hold_first_person" % identifier: animation(first),
        "animation.%s.hold_third_person" % identifier: animation(third),
        "animation.%s.head" % identifier: animation(head),
    }}


def build_attachable(bedrock_id, geometry_id, texture):
    """手に持ったとき・頭に乗せたときに、3Dモデルを出すための設定。"""
    hand = "(context.item_slot == 'main_hand' || context.item_slot == 'off_hand')"
    return {"format_version": "1.10.0", "minecraft:attachable": {"description": {
        "identifier": bedrock_id,
        "materials": {"default": "entity_alphatest", "enchanted": "entity_alphatest_glint"},
        "textures": {"default": texture, "enchanted": "textures/misc/enchanted_item_glint"},
        "geometry": {"default": "geometry." + geometry_id},
        "animations": {
            "first_person": "animation.%s.hold_first_person" % geometry_id,
            "third_person": "animation.%s.hold_third_person" % geometry_id,
            "head": "animation.%s.head" % geometry_id,
        },
        "scripts": {"animate": [
            {"first_person": "context.is_first_person == 1.0 && " + hand},
            {"third_person": "context.is_first_person == 0.0 && " + hand},
            {"head": "context.is_first_person == 0.0 && context.item_slot == 'head'"},
        ]},
        "render_controllers": ["controller.render.item_default"],
    }}}


def build_manifest(tag):
    match = re.fullmatch(r"v(\d+)\.(\d+)\.(\d+)", tag)
    if not match:
        raise ValueError("タグは v1.2.3 の形にしてください: " + tag)
    version = [int(part) for part in match.groups()]
    base = "https://github.com/hnmt-mc/hnmt-textures/bedrock/"
    return {"format_version": 2,
            "header": {"name": "日ノ本鯖 テクスチャ（統合版）", "description": "日ノ本鯖のアイテムの見た目（統合版用）",
                       "uuid": str(uuid.uuid5(uuid.NAMESPACE_URL, base + "header")), "version": version,
                       "min_engine_version": ENGINE_VERSION},
            "modules": [{"type": "resources", "uuid": str(uuid.uuid5(uuid.NAMESPACE_URL, base + "module")),
                         "description": "日ノ本鯖のアイテムの見た目", "version": version}]}


def build_item_atlas(item_ids, cast=()):
    """持ち物の中の絵の一覧。cast は、投げた状態の絵も持つ品（釣竿）。"""
    data = {}
    for item in item_ids:
        name = safe_name(item)
        data["%s.%s" % (NAMESPACE, name)] = {"textures": ["textures/items/%s/%s" % (NAMESPACE, name)]}
        if item in cast:
            data["%s.%s_cast" % (NAMESPACE, name)] = {"textures": ["textures/items/%s/%s_cast" % (NAMESPACE, name)]}
    return {"resource_pack_name": NAMESPACE, "texture_name": "atlas.items", "texture_data": data}


def build_mappings(bases, flat=frozenset(), cast=frozenset()):
    """Geyser のカスタムアイテムの対応づけ（形式2）。

    bases は {アイテムID: 元の Java のアイテム}。flat は平らな絵の品（道具のように持つ）、cast は投げた状態の絵も持つ品。
    投げた状態は、fishing_rod_cast の条件つきの定義にして、条件のない定義より先に並べる。
    """
    items = {}
    for item, base in bases.items():
        name = safe_name(item)
        definitions = items.setdefault(base, [])
        options = {"allow_offhand": True, "display_handheld": item in flat}
        if item in cast:
            definitions.append({
                "type": "definition",
                "model": "%s:%s" % (NAMESPACE, item),
                "bedrock_identifier": "%s:%s_cast" % (NAMESPACE, name),
                "predicate": {"type": "condition", "property": "fishing_rod_cast"},
                "bedrock_options": dict(options, icon="%s.%s_cast" % (NAMESPACE, name)),
            })
        definitions.append({
            "type": "definition",
            "model": "%s:%s" % (NAMESPACE, item),
            "bedrock_identifier": "%s:%s" % (NAMESPACE, name),
            "bedrock_options": dict(options, icon="%s.%s" % (NAMESPACE, name)),
        })
    return {"format_version": 2, "items": items}


# ---- カスタムブロック（石臼） ----

BLOCKS_FILE = "hnmt_blocks.json"


def block_geometry(model, identifier, texture_px, slab_height, slab_uv=(0, 8, 8, 16)):
    """ハーフブロックの上に立つ置き物（石臼）を、1ブロックぶんのジオメトリにする。

    サーバーの本物のブロックはハーフブロック（高さ slab_height）で、その上に Java 版では ItemDisplay でモデルを重ねている。
    統合版には ItemDisplay がないので、ハーフブロックと置き物を、1つのブロックの絵にする。
    ブロックの絵は高さ 16 までなので、モデルが残りの高さ（16 - slab_height）に収まらないときは、縦だけ縮める。
    ハーフブロックの面は、テクスチャの slab_uv（Java の UV の範囲）を使う。
    """
    elements = model.get("elements") or []
    if not elements:
        raise ValueError("elements がありません: " + identifier)
    if any(element.get("rotation") for element in elements):
        raise ValueError("回転のある直方体は、ブロックにできません: " + identifier)
    room = 16 - slab_height
    top = max(element["to"][1] for element in elements)
    factor = min(1, room / top)
    uv_space = tuple(model.get("texture_size", (16, 16)))
    slab = {"from": [0, 0, 0], "to": [16, slab_height, 16],
            "faces": {name: {"uv": list(slab_uv), "texture": "#0"} for name in FACES}}
    stacked = [slab]
    for element in elements:
        moved = dict(element)
        moved["from"] = [element["from"][0], slab_height + element["from"][1] * factor, element["from"][2]]
        moved["to"] = [element["to"][0], slab_height + element["to"][1] * factor, element["to"][2]]
        stacked.append(moved)
    cubes = [convert_element(element, uv_space, texture_px) for element in stacked]
    return {
        "format_version": FORMAT_VERSION,
        "minecraft:geometry": [{
            "description": {"identifier": "geometry." + identifier,
                            "texture_width": texture_px[0], "texture_height": texture_px[1]},
            "bones": [{"name": "block", "pivot": [0, 0, 0], "cubes": cubes}],
        }],
    }


def block_geometry_name(item):
    """ブロックのジオメトリの名前。アイテム（手に持つ）のジオメトリは hnmt_<名前> なので、別の名前にする（同じだと、片方が上書きされる）。"""
    return "%s_block_%s" % (NAMESPACE, safe_name(item))


def build_block_mappings(blocks):
    """Geyser のカスタムブロックの対応づけ（形式1）。

    blocks は {アイテムID: {java_block, state, slab_height, display_name}}。Java のブロックの状態を、ちょうど1つだけ、
    カスタムブロックに置き換える（only_override_states）。ほかの状態は、そのまま。
    サーバーは、この状態のブロックを、統合版の人にだけ見せかけで送る（本物のブロックは変えない）。
    """
    result = {}
    for item, entry in blocks.items():
        java = entry["java_block"]
        if java in result:
            raise ValueError("同じ Java のブロックを、2つのブロックが使えません: " + java)
        name = "%s_%s" % (NAMESPACE, safe_name(item))
        result[java] = {
            "name": name,
            "display_name": entry["display_name"],
            "geometry": "geometry." + block_geometry_name(item),
            "material_instances": {"*": {"texture": name, "render_method": "alpha_test",
                                         "face_dimming": True, "ambient_occlusion": True}},
            "included_in_creative_inventory": False,
            "only_override_states": True,
            "state_overrides": {entry["state"]: {}},
        }
    return {"format_version": 1, "blocks": result}


def build_terrain_atlas(block_ids):
    """ブロックの絵の一覧。"""
    data = {}
    for item in block_ids:
        name = "%s_%s" % (NAMESPACE, safe_name(item))
        data[name] = {"textures": "textures/blocks/%s/%s" % (NAMESPACE, safe_name(item))}
    return {"resource_pack_name": NAMESPACE, "texture_name": "atlas.terrain", "padding": 8, "num_mip_levels": 4, "texture_data": data}


# ---- パック全体 ----

def _write_json(path, doc):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(doc, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def _copy(source, destination):
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    shutil.copyfile(source, destination)


def _model_path(root, item):
    """3Dモデルの場所。models3d にあればそこ、なければ assets の中（クーラーボックスは、アイコンと同じモデルが3D）。"""
    path = os.path.join(root, "models3d", item + ".json")
    if os.path.exists(path):
        return path
    return os.path.join(root, "assets", "hnmt", "models", "item", item + ".json")


def build_pack(root, out, bases, tag, blocks=None):
    """bases の全アイテムについて、統合版のパックと対応づけを out に作る。3Dモデルのない品は、平らな絵の品として扱う。

    blocks（{アイテムID: ブロックの定義}）があれば、その品は、カスタムブロックとしても作る（見せかけのブロック用）。"""
    pack = os.path.join(out, "pack")
    textures = os.path.join(root, "assets", "hnmt", "textures")
    flat = set()
    cast = set()
    for item in bases:
        name = safe_name(item)
        with open(_model_path(root, item), encoding="utf-8") as handle:
            model = json.load(handle)
        _copy(os.path.join(textures, "item", item + ".png"), os.path.join(pack, "textures", "items", NAMESPACE, name + ".png"))
        if not model.get("elements"):
            flat.add(item)
            cast_icon = os.path.join(textures, "item", item + "_cast.png")
            if os.path.exists(cast_icon):
                cast.add(item)
                _copy(cast_icon, os.path.join(pack, "textures", "items", NAMESPACE, name + "_cast.png"))
            continue
        model_texture = os.path.join(textures, model["textures"]["0"].replace("hnmt:", "") + ".png")
        with open(model_texture, "rb") as handle:
            size = png_size(handle.read(32))
        geometry_id = "%s_%s" % (NAMESPACE, name)
        _write_json(os.path.join(pack, "models", "entity", geometry_id + ".geo.json"), model_to_geometry(model, geometry_id, size))
        _write_json(os.path.join(pack, "animations", geometry_id + ".animation.json"), display_to_animations(model.get("display", {}), geometry_id))
        _write_json(os.path.join(pack, "attachables", geometry_id + ".json"),
                    build_attachable("%s:%s" % (NAMESPACE, name), geometry_id, "textures/entity/%s/%s" % (NAMESPACE, name)))
        _copy(model_texture, os.path.join(pack, "textures", "entity", NAMESPACE, name + ".png"))
    if blocks:
        for item, entry in blocks.items():
            if item not in bases:
                raise ValueError("ブロックにする品が、アイテムの表にありません: " + item)
            with open(_model_path(root, item), encoding="utf-8") as handle:
                model = json.load(handle)
            texture = os.path.join(textures, model["textures"]["0"].replace("hnmt:", "") + ".png")
            with open(texture, "rb") as handle:
                size = png_size(handle.read(32))
            geometry_name = block_geometry_name(item)
            _write_json(os.path.join(pack, "models", "blocks", geometry_name + ".geo.json"),
                        block_geometry(model, geometry_name, size, entry["slab_height"]))
            _copy(texture, os.path.join(pack, "textures", "blocks", NAMESPACE, safe_name(item) + ".png"))
        _write_json(os.path.join(pack, "textures", "terrain_texture.json"), build_terrain_atlas(blocks))
        _write_json(os.path.join(out, "custom_mappings", BLOCKS_FILE), build_block_mappings(blocks))
    _write_json(os.path.join(pack, "textures", "item_texture.json"), build_item_atlas(bases, cast))
    _write_json(os.path.join(pack, "manifest.json"), build_manifest(tag))
    _write_json(os.path.join(out, "custom_mappings", "hnmt.json"), build_mappings(bases, flat, cast))


def zip_pack(out):
    """pack/ の中身を、manifest.json が一番上に来る形で、hnmt-bedrock.mcpack にまとめる。"""
    archive = shutil.make_archive(os.path.join(out, "hnmt-bedrock"), "zip", os.path.join(out, "pack"))
    target = os.path.join(out, "hnmt-bedrock.mcpack")
    os.replace(archive, target)
    return target


def main(argv):
    if len(argv) != 4:
        print("使い方: make_bedrock.py <パックのルート> <出力先> <タグ（v1.2.3）>", file=sys.stderr)
        return 2
    root, out, tag = argv[1], argv[2], argv[3]
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bedrock_bases.json"), encoding="utf-8") as handle:
        bases = json.load(handle)
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bedrock_blocks.json"), encoding="utf-8") as handle:
        blocks = json.load(handle)
    build_pack(root, out, bases, tag, blocks)
    zip_pack(out)
    print("作りました: %d 品（うちブロック %d） → %s" % (len(bases), len(blocks), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
