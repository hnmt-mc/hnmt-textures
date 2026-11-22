#!/usr/bin/env python3
"""リリース用の pack.json を作る。hnmt-core のプラグインが、これを読んで、参加した人へパックを送る。

使い方: python3 tools/make_manifest.py <タグ> [zip のパス]
  タグ（例: v0.1.0）から、zip の固定URLを作り、zip の SHA-1 と、SHA-1 から決まる ID（UUID）を書く。
  ID は、中身が変わると変わるので、クライアントが、古いキャッシュではなく、新しい zip を取り直す。
"""

import io
import zipfile
import hashlib
import json
import re
import sys
import uuid
from pathlib import Path

REPOSITORY = "hnmt-mc/hnmt-textures"
ASSET = "hnmt-textures.zip"
ROOT = Path(__file__).resolve().parents[1]


BLADE_SOUNDS = ('blade.draw', 'blade.sheath', 'blade.iai', 'blade.dash', 'blade.youtou')
BLADE_ATTACK_SOUNDS = ('blade.swing', 'blade.strike', 'blade.sweep', 'blade.crit')


def blade_sounds(archive, wanted=BLADE_SOUNDS):
    """刀の音は、音の定義と、定義が指す ogg がすべて ZIP に入っているときだけ、使えるとみなす。"""
    events = json.loads(archive.read('assets/hnmt/sounds.json'))
    for event in wanted:
        entries = events[event]['sounds']
        if not entries: return False
        for entry in entries:
            name = entry['name'].split(':', 1)[1]
            if archive.getinfo('assets/hnmt/sounds/' + name + '.ogg').file_size <= 0: return False
    return True


BLADE_SCREEN_CHARS = {'blade_slash': '\ue000', 'blade_drain': '\ue001'}


def blade_screens(archive):
    """画面の演出は、フォントの定義と、それが指す絵がすべて ZIP に入っているときだけ、使えるとみなす。"""
    providers = json.loads(archive.read('assets/hnmt/font/blade.json'))['providers']
    seen = {}
    for provider in providers:
        if provider.get('type') != 'bitmap': continue
        name = provider['file'].split(':', 1)[1]
        if archive.getinfo('assets/hnmt/textures/' + name).file_size <= 0: return False
        seen[name] = ''.join(provider['chars'])
    return all(seen.get('font/' + key + '.png') == char for key, char in BLADE_SCREEN_CHARS.items())


def capabilities(data):
    """Only advertise interaction support when its actual assets are in the ZIP."""
    found = []
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            if blade_sounds(archive): found.append('blade-sounds-v1')
            if blade_sounds(archive, BLADE_SOUNDS + BLADE_ATTACK_SOUNDS): found.append('blade-attack-sounds-v1')
            if blade_screens(archive): found.append('blade-screen-v1')
    except (zipfile.BadZipFile, KeyError, ValueError, TypeError, AttributeError):
        pass
    return found + rice_capabilities(data)


def rice_capabilities(data):
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            names = ('assets/minecraft/blockstates/sculk_vein.json', 'assets/hnmt/models/block/rice_hitbox.json')
            if any(archive.getinfo(n).file_size > 65536 for n in names):
                return []
            states, model = (json.loads(archive.read(n)) for n in names)
            faces = {d: 'false' for d in ('north','east','south','west','up','down')}
            if (model.get('elements') == [] and any(
                p.get('when') == faces and p.get('apply') == {'model':'hnmt:block/rice_hitbox'}
                for p in states.get('multipart', []))):
                return ['rice-held-harvest-v1']
    except (zipfile.BadZipFile, KeyError, ValueError, TypeError, AttributeError):
        pass
    return []


def manifest(tag, data):
    if not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        raise ValueError("タグは v1.2.3 の形にしてください: " + tag)
    sha1 = hashlib.sha1(data).hexdigest()
    return {
        "version": tag,
        "capabilities": capabilities(data),
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
