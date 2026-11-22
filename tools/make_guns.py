#!/usr/bin/env python3
"""銃と弾（火縄銃・短筒と、それぞれの火縄に火が付いた装填済みの絵、鉄砲弾・焼夷弾・散弾）の絵とモデルを作る。

どれも、32×32の平らなアイコン（斜めに、左下が銃床・右上が銃口）。銃のモデルは、バニラの剣と同じ item/handheld
（手に持ったとき、道具と同じ向きになる）。弾は、持つ物ではないので item/generated。統合版も、平らなアイコンのまま出す。

  python3 tools/make_guns.py            絵とモデルを書き出す
  python3 tools/make_guns.py --preview  絵を拡大して並べる（build/guns/preview.png）
"""
import argparse
import json
import math
from PIL import Image
from artwork import PACK, BUILD
from make_blades import diagonal, cross, put, rgba, SIZE

# （名前, 持ち方）。持ち方: handheld は道具のように持つ、generated は物のように持つ
GUNS = [('matchlock', 'handheld'), ('matchlock_loaded', 'handheld'), ('tanzutsu', 'handheld'), ('tanzutsu_loaded', 'handheld'),
        ('ammo_teppo', 'generated'), ('ammo_shoidan', 'generated'), ('ammo_sandan', 'generated')]

STEEL = ('#c4ccd6', '#8a95a4', '#4a5260')
WOOD = ('#b88a52', '#8a5a30', '#5e3d1f')
BRASS, BRASS_DARK = '#d9b04a', '#8f6f22'
EMBER, EMBER_BRIGHT, EMBER_GLOW = '#ff8a1f', '#ffe08a', '#ff5a1f'


def ball(image, cx, cy, radius, colors):
    """丸い弾。colors は、明・中・暗。左上から光が当たる。"""
    light, mid, dark = (rgba(c) for c in colors)
    for y in range(SIZE):
        for x in range(SIZE):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            d = math.hypot(dx, dy)
            if d > radius: continue
            shade = (dx + dy) / (2 * radius)   # -1（左上）〜 1（右下）
            color = light if shade < -0.45 else (dark if shade > 0.35 else mid)
            image.putpixel((x, y), color)


def polygon(image, points, fill):
    from PIL import ImageDraw
    ImageDraw.Draw(image).polygon(points, fill=rgba(fill))


def long_gun(loaded):
    image = Image.new('RGBA', (SIZE, SIZE))
    # 銃床: 後ろへ向かって広がる木の台
    polygon(image, [(0, 24), (6, 31), (16, 24), (13, 19), (9, 20)], WOOD[1])
    polygon(image, [(1, 24), (7, 30), (8, 29), (3, 24)], WOOD[0])          # 上の縁の明るい色
    polygon(image, [(5, 31), (15, 25), (15, 24), (6, 30)], WOOD[2])        # 下の縁の暗い色
    put(image, 2, 27, WOOD[2]); put(image, 4, 28, WOOD[2])
    diagonal(image, (13, 20), (31, 2), STEEL, half=1)                       # 銃身
    for i in range(1, 17, 5): put(image, 14 + i, 19 - i, '#2f3640'); put(image, 15 + i, 19 - i, '#2f3640')
    put(image, 30, 2, '#2f3640'); put(image, 31, 3, '#2f3640')              # 銃口
    for i in range(0, 12, 2): put(image, 12 + i, 23 - i, WOOD[2])           # 銃身の下の込め矢
    cross(image, (14, 19), 2, [BRASS])                                       # 火皿・火挟みの金具
    put(image, 13, 20, BRASS_DARK); put(image, 16, 17, BRASS_DARK)
    # 火縄: 火挟みから、細い縄が前へ伸びる。装填済みは、先に火が付いている
    for dx, dy in ((15, 17), (16, 16), (17, 16), (18, 15)): put(image, dx, dy, '#6b5a3a')
    if loaded:
        put(image, 19, 14, EMBER); put(image, 18, 14, EMBER_BRIGHT)
        for gx, gy in ((20, 14), (19, 13), (19, 15), (20, 13)): put(image, gx, gy, EMBER_GLOW)
    else:
        put(image, 19, 14, '#4a3f28')
    return image


def short_gun(loaded):
    image = Image.new('RGBA', (SIZE, SIZE))
    # 握り: 下へ曲がった木の台と、丸い握り玉
    polygon(image, [(6, 22), (7, 29), (10, 30), (14, 27), (14, 19), (9, 18)], WOOD[1])
    polygon(image, [(7, 22), (8, 28), (9, 27), (8, 22)], WOOD[0])
    polygon(image, [(10, 30), (14, 27), (14, 26), (11, 28)], WOOD[2])
    ball(image, 7.5, 29.5, 2.5, (BRASS, '#b88a2a', BRASS_DARK))
    diagonal(image, (15, 19), (28, 6), STEEL, half=1)                       # 短い銃身
    for i in range(1, 12, 5): put(image, 16 + i, 18 - i, '#2f3640'); put(image, 17 + i, 18 - i, '#2f3640')
    put(image, 27, 6, '#2f3640'); put(image, 28, 7, '#2f3640')
    cross(image, (15, 18), 2, [BRASS])
    put(image, 14, 19, BRASS_DARK); put(image, 17, 16, BRASS_DARK)
    for dx, dy in ((16, 16), (17, 15), (18, 15)): put(image, dx, dy, '#6b5a3a')
    if loaded:
        put(image, 19, 14, EMBER); put(image, 18, 14, EMBER_BRIGHT)
        for gx, gy in ((20, 14), (19, 13), (19, 15), (20, 13)): put(image, gx, gy, EMBER_GLOW)
    else:
        put(image, 19, 14, '#4a3f28')
    return image


def ammo(kind):
    image = Image.new('RGBA', (SIZE, SIZE))
    if kind == 'teppo':        # 鉛の丸い弾
        ball(image, 15.5, 16.5, 7, ('#d9dde2', '#8d96a3', '#4b525d'))
    elif kind == 'shoidan':    # 火を帯びた弾
        ball(image, 15.5, 18, 6, ('#ffd36a', '#ff7a1f', '#a3270f'))
        for x, y, c in ((15, 9, '#ffe08a'), (16, 8, '#ff9a2a'), (14, 10, '#ff9a2a'), (16, 10, '#ff9a2a'), (15, 11, '#ff5a1f'), (17, 11, '#ff5a1f')):
            put(image, x, y, c)
        put(image, 15, 7, '#ffd36a')
    else:                      # 散弾: 小さな弾がいくつか
        for cx, cy in ((10, 20), (16, 22), (22, 20), (13, 14), (19, 14), (16, 9), (11, 25), (21, 25)):
            ball(image, cx, cy, 3, ('#d9dde2', '#8d96a3', '#4b525d'))
    return image


def draw(name):
    if name == 'matchlock': return long_gun(False)
    if name == 'matchlock_loaded': return long_gun(True)
    if name == 'tanzutsu': return short_gun(False)
    if name == 'tanzutsu_loaded': return short_gun(True)
    if name.startswith('ammo_'): return ammo(name[5:])
    raise ValueError('Unknown gun item: ' + name)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def build():
    for name, holding in GUNS:
        path = PACK / 'assets/hnmt/textures/item/gun' / (name + '.png')
        path.parent.mkdir(parents=True, exist_ok=True)
        draw(name).save(path)
        write_json(PACK / 'assets/hnmt/items/gun' / (name + '.json'), {'model': {'type': 'minecraft:model', 'model': 'hnmt:item/gun/' + name}})
        write_json(PACK / 'assets/hnmt/models/item/gun' / (name + '.json'),
                   {'parent': 'minecraft:item/' + holding, 'textures': {'layer0': 'hnmt:item/gun/' + name}})
    print('Wrote %d gun icons' % len(GUNS))


def preview():
    target = BUILD / 'guns'
    target.mkdir(parents=True, exist_ok=True)
    scale, columns = 8, 4
    rows = (len(GUNS) + columns - 1) // columns
    sheet = Image.new('RGBA', (columns * (SIZE * scale + 8) + 8, rows * (SIZE * scale + 8) + 8), (232, 226, 214, 255))
    for i, (name, _) in enumerate(GUNS):
        big = draw(name).resize((SIZE * scale, SIZE * scale), Image.NEAREST)
        sheet.paste(big, (8 + (i % columns) * (SIZE * scale + 8), 8 + (i // columns) * (SIZE * scale + 8)), big)
    sheet.save(target / 'preview.png')
    print('Preview: ' + str(target / 'preview.png'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview', action='store_true', help='絵を拡大して並べる')
    args = parser.parse_args()
    preview() if args.preview else build()


if __name__ == '__main__': main()
