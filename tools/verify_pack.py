#!/usr/bin/env python3
"""Validate the complete item-model/texture graph and the exported archives."""

import json
import math
import sys
import zipfile
from pathlib import Path
from PIL import Image
from artwork import PACK, TEXTURES, BUILD
from make_models import inventory


def verify():
    failures = []
    count = 0
    dimensions = set()
    expected = list(inventory())
    if len(expected) != 72:
        failures.append("Expected 72 texture/model variants")
    for group, name, _ in expected:
        relative = "/".join(part for part in (group, name) if part)
        try:
            image = Image.open(TEXTURES / (relative + ".png"))
            dimensions.add(image.size)
            expected_size = (16, 16) if group == "rice" else (32, 32)   # 米作りは、バニラの作物に近い16px
            assert image.size == expected_size, "texture must be %dx%d" % expected_size
            assert image.mode == "RGBA", "texture must be RGBA"
            alpha = set(image.getchannel("A").get_flattened_data())
            if group == "rice" and name == "mill":
                assert alpha == {255}, "mill texture is an opaque swatch sheet"
            else:
                assert alpha == {0, 255}, "expected crisp binary transparency"
            if group == "rod":
                model = None  # 釣竿は、3D版でも平らなモデルのまま
            else:
                model = json.loads((PACK / "models3d" / (relative + ".json")).read_text())
                assert model.get("elements"), "3D model is empty"
            if group == "fish":
                assert (
                    16 <= len(model["elements"]) <= 160
                ), "fish cuboid budget must be 16..160"
            if model is not None:
                texture_relative = "dish3d/" + name if group == "dish" else relative
                assert set(model["textures"].values()) == {
                    "hnmt:item/" + texture_relative
                }, "3D model must use one texture"
                if group == "dish":
                    dish_texture = Image.open(TEXTURES / (texture_relative + ".png"))
                    assert dish_texture.size == (32, 32) and dish_texture.mode == "RGBA"
                    assert set(dish_texture.getchannel("A").get_flattened_data()) <= {0, 255}
                    assert len(model["elements"]) <= 150, "dish cuboid budget must be <=150"
                for element in model["elements"]:
                    assert set(element) <= ({"name", "rotation"} if group in ("dish", "rice") else set()) | {
                        "from",
                        "to",
                        "faces",
                    }, "unsupported element fields"
                    if "rotation" in element:
                        rotation = element["rotation"]
                        assert group in ("dish", "rice")
                        assert rotation["axis"] in (("y",) if group == "dish" else ("x", "y", "z"))
                        assert rotation["angle"] in (-45, -22.5, 0, 22.5, 45)
                        assert not rotation.get("rescale", False)
                        assert len(rotation["origin"]) == 3
                        assert all(math.isfinite(v) for v in rotation["origin"])
                    for axis, (a, b) in enumerate(zip(element["from"], element["to"])):
                        if group == "rice" and name.startswith("plant_"):
                            # 交差した板（バニラの作物と同じ）。足元は耕地の面より1下、幅は回転で収まるよう、はみ出して置く。
                            assert math.isfinite(a) and math.isfinite(b) and -16 <= a <= b <= 32
                            continue
                        assert math.isfinite(a) and math.isfinite(b) and 0 <= a < b <= 16
                    if group == "rice" and (name.startswith("plant_") or name in ("seedling", "stalk", "grain")):
                        assert set(element["faces"]) == {"north", "south"}, "flat planes have two faces"
                    else:
                        assert set(element["faces"]) == {
                            "north",
                            "south",
                            "east",
                            "west",
                            "up",
                            "down",
                        }
                    for face in element["faces"].values():
                        assert face["texture"] == "#0"
                        assert len(face["uv"]) == 4 and all(
                            math.isfinite(v) and 0 <= v <= 16 for v in face["uv"]
                        )
            flat = json.loads(
                (PACK / "assets/hnmt/models/item" / (relative + ".json")).read_text()
            )
            assert flat["textures"]["layer0"] == "hnmt:item/" + relative
            if not name.endswith("_cast"):
                definition = json.loads(
                    (PACK / "assets/hnmt/items" / (relative + ".json")).read_text()
                )["model"]
                if group == "rod":
                    assert definition["property"] == "minecraft:fishing_rod/cast"
                    assert (
                        definition["on_true"]["model"]
                        == "hnmt:item/" + relative + "_cast"
                    )
                    assert definition["on_false"]["model"] == "hnmt:item/" + relative
                else:
                    assert definition["model"] == "hnmt:item/" + relative
            count += 1
        except (OSError, ValueError, KeyError, AssertionError) as error:
            failures.append(relative + ": " + str(error))
    for name in (
        "bamboo",
        "keiryu_nami",
        "keiryu_jo",
        "iso_nami",
        "iso_jo",
        "fune_nami",
        "fune_jo",
    ):
        regular = Image.open(TEXTURES / "rod" / (name + ".png")).convert("RGBA")
        cast = Image.open(TEXTURES / "rod" / (name + "_cast.png")).convert("RGBA")
        assert regular.tobytes() != cast.tobytes(), "rod states must differ"
        assert (
            232,
            232,
            232,
            255,
        ) in regular.get_flattened_data(), "normal rod must have a line"
        assert (
            232,
            232,
            232,
            255,
        ) not in cast.get_flattened_data(), "cast rod must not have a line"
    meta = json.loads((PACK / "pack.mcmeta").read_text())["pack"]
    assert meta["min_format"] == meta["max_format"] == 75
    for variant in ("", "-3d"):
        archive = BUILD / {"": "hnmt-textures-flat.zip", "-3d": "hnmt-textures.zip"}[variant]
        if not archive.exists():
            continue
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            names = z.namelist()
            assert "pack.mcmeta" in names and all(
                not n.startswith("/") and ".." not in Path(n).parts for n in names
            )
            assert not any(
                ".DS_Store" in n or "__pycache__" in n or n.endswith(".py")
                for n in names
            )
            for group, name, _ in expected:
                relative = "/".join(part for part in (group, name) if part)
                exported = json.loads(
                    z.read("assets/hnmt/models/item/" + relative + ".json")
                )
                assert ("elements" in exported) == (bool(variant) and group != "rod"), (
                    relative + " wrong model variant"
                )
                if variant and group == "dish":
                    texture_path = "assets/hnmt/textures/item/dish3d/" + name + ".png"
                    assert z.read(texture_path) == (TEXTURES / "dish3d" / (name + ".png")).read_bytes()
                    assert exported == json.loads((PACK / "models3d/dish" / (name + ".json")).read_text())
    if failures:
        raise SystemExit("\n".join(failures))
    print(
        f"PASS: {count} item variants and 32 dish atlases, all 32x32; cuboids, UVs, cast states, model references and archive contents validated"
    )


if __name__ == "__main__":
    verify()
