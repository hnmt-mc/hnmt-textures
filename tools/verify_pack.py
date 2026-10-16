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
    if len(expected) != 65:
        failures.append("Expected 65 texture/model variants")
    for group, name, _ in expected:
        relative = "/".join(part for part in (group, name) if part)
        try:
            image = Image.open(TEXTURES / (relative + ".png"))
            dimensions.add(image.size)
            assert image.size == (32, 32), "texture must be 32x32"
            assert image.mode == "RGBA", "texture must be RGBA"
            assert set(image.getchannel("A").get_flattened_data()) == {
                0,
                255,
            }, "expected crisp binary transparency"
            model = json.loads((PACK / "models3d" / (relative + ".json")).read_text())
            assert model.get("elements"), "3D model is empty"
            if group == "fish":
                assert (
                    16 <= len(model["elements"]) <= 32
                ), "fish cuboid budget must be 16..32"
            assert set(model["textures"].values()) == {
                "hnmt:item/" + relative
            }, "3D model must use one texture"
            for element in model["elements"]:
                assert set(element) == {
                    "from",
                    "to",
                    "faces",
                }, "only axis-aligned cuboids are supported"
                for a, b in zip(element["from"], element["to"]):
                    assert math.isfinite(a) and math.isfinite(b) and 0 <= a < b <= 16
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
        archive = BUILD / ("hnmt-resourcepack" + variant + ".zip")
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
                assert ("elements" in exported) == bool(variant), (
                    relative + " wrong model variant"
                )
    if failures:
        raise SystemExit("\n".join(failures))
    print(
        f"PASS: {count} RGBA textures, all 32x32; cuboids, UVs, cast states, model references and archive contents validated"
    )


if __name__ == "__main__":
    verify()
