#!/usr/bin/env python3
"""pack.mcmeta・items 定義・モデル JSON を作る（テクスチャは make_textures.py / make_rods.py）。

使い方:  python3 resourcepack/tools/make_pack.py
pack.mcmeta は、1.21.11 のリソースパック形式 75（client.jar の version.json の resource_major=75 と
Minecraft Wiki の Pack format 表で確認）に合わせている。
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ASSETS = os.path.join(ROOT, "resourcepack", "assets", "hnmt")
PACK = os.path.join(ROOT, "resourcepack")

FISH = ["unagi", "salmon", "kohada", "konoshiro", "tai", "hirame", "saba", "hamachi", "buri", "ika", "kanpachi", "maguro"]
BAITS = ["mimizu", "ebi", "iwashi", "ika_no_mi"]
RODS = ["bamboo", "keiryu_nami", "keiryu_jo", "iso_nami", "iso_jo", "fune_nami", "fune_jo"]


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def model(kind, name):
    return {"type": "minecraft:model", "model": f"hnmt:item/{kind}/{name}"}


def main():
    write(os.path.join(PACK, "pack.mcmeta"), {
        "pack": {"description": "日ノ本鯖 魚と釣竿と餌の見た目", "min_format": 75, "max_format": 75}
    })
    for fid in FISH:
        write(f"{ASSETS}/items/fish/{fid}.json", {"model": model("fish", fid)})
        write(f"{ASSETS}/models/item/fish/{fid}.json",
              {"parent": "minecraft:item/generated", "textures": {"layer0": f"hnmt:item/fish/{fid}"}})
    for bid in BAITS:
        write(f"{ASSETS}/items/bait/{bid}.json", {"model": model("bait", bid)})
        write(f"{ASSETS}/models/item/bait/{bid}.json",
              {"parent": "minecraft:item/generated", "textures": {"layer0": f"hnmt:item/bait/{bid}"}})
    for rid in RODS:
        # バニラの fishing_rod と同じ作り: 投げている間は _cast のモデルに切り替える
        write(f"{ASSETS}/items/rod/{rid}.json", {"model": {
            "type": "minecraft:condition",
            "property": "minecraft:fishing_rod/cast",
            "on_true": model("rod", rid + "_cast"),
            "on_false": model("rod", rid),
        }})
        for suffix in ("", "_cast"):
            write(f"{ASSETS}/models/item/rod/{rid}{suffix}.json",
                  {"parent": "minecraft:item/handheld_rod", "textures": {"layer0": f"hnmt:item/rod/{rid}{suffix}"}})


if __name__ == "__main__":
    main()
