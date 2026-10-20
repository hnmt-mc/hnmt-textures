#!/usr/bin/env python3
"""統合版用の更新の情報 bedrock.json を作る。専用プラグイン（hnmt-geyserpacks）が、これを読んで、Geyser のフォルダへファイルを置く。

使い方: python3 tools/make_bedrock_manifest.py <タグ> [bedrock の出力先]
  出力先（既定は build/bedrock）の hnmt-bedrock.mcpack と custom_mappings/hnmt.json から、
  それぞれの固定URLと SHA-1 を、bedrock.json に書く。
"""

import hashlib
import json
import re
import sys
from pathlib import Path

REPOSITORY = "hnmt-mc/hnmt-textures"
PACK = "hnmt-bedrock.mcpack"
MAPPINGS = "hnmt.json"
ROOT = Path(__file__).resolve().parents[1]


def _entry(tag, name, target, data):
    return {
        "name": name,
        "target": target,
        "url": f"https://github.com/{REPOSITORY}/releases/download/{tag}/{name}",
        "sha1": hashlib.sha1(data).hexdigest(),
    }


def manifest(tag, pack, mappings):
    if not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        raise ValueError("タグは v1.2.3 の形にしてください: " + tag)
    return {"version": tag, "files": [_entry(tag, PACK, "packs", pack), _entry(tag, MAPPINGS, "custom_mappings", mappings)]}


if __name__ == "__main__":
    tag = sys.argv[1]
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "build" / "bedrock"
    result = manifest(tag, (out / PACK).read_bytes(), (out / "custom_mappings" / MAPPINGS).read_bytes())
    (out / "bedrock.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
