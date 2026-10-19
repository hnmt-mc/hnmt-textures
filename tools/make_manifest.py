#!/usr/bin/env python3
"""リリース用の pack.json を作る。hnmt-core のプラグインが、これを読んで、参加した人へパックを送る。

使い方: python3 tools/make_manifest.py <タグ> [zip のパス]
  タグ（例: v0.1.0）から、zip の固定URLを作り、zip の SHA-1 と、SHA-1 から決まる ID（UUID）を書く。
  ID は、中身が変わると変わるので、クライアントが、古いキャッシュではなく、新しい zip を取り直す。
"""

import hashlib
import json
import re
import sys
import uuid
from pathlib import Path

REPOSITORY = "hnmt-mc/hnmt-textures"
ASSET = "hnmt-textures.zip"
ROOT = Path(__file__).resolve().parents[1]


def manifest(tag, data):
    if not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        raise ValueError("タグは v1.2.3 の形にしてください: " + tag)
    sha1 = hashlib.sha1(data).hexdigest()
    return {
        "version": tag,
        "url": f"https://github.com/{REPOSITORY}/releases/download/{tag}/{ASSET}",
        "sha1": sha1,
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, sha1)),
    }


if __name__ == "__main__":
    tag = sys.argv[1]
    path = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "build" / ASSET
    result = manifest(tag, path.read_bytes())
    (path.parent / "pack.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
