"""Java 版のモデル（直方体の elements）を、統合版（Bedrock）のジオメトリへ直す。

座標の決まり（Geyser の変換 mod Rainbow の挙動と同じ）:
- 中心を (8, 0, 8) に寄せる。x 軸は逆向きなので、原点の x は -(x + 幅) にする。
- 上と下の面の UV は、始点と終点を入れ替える。
- 回転は、x 軸だけ角度の向きを逆にする。軸の中心（pivot）も x を逆にする。
- UV は Java では 0〜16 だが、統合版は画素なので、テクスチャの大きさに合わせて拡大する。
"""
import json
import struct
import sys

FORMAT_VERSION = "1.21.0"
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
            "bones": [{"name": "model", "pivot": pivot, "cubes": cubes}],
        }],
    }


def png_size(data):
    """PNG の先頭（IHDR）から、幅と高さを読む。"""
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError("PNG ではありません")
    return struct.unpack(">II", data[16:24])


def main(argv):
    if len(argv) != 4:
        print("使い方: make_bedrock.py <モデル.json> <テクスチャ.png> <識別名>", file=sys.stderr)
        return 2
    with open(argv[1], encoding="utf-8") as handle:
        model = json.load(handle)
    with open(argv[2], "rb") as handle:
        size = png_size(handle.read(32))
    json.dump(model_to_geometry(model, argv[3], size), sys.stdout, indent=2, ensure_ascii=False)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
