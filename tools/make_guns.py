#!/usr/bin/env python3
"""銃と弾（火縄銃・短筒と、それぞれの火縄に火が付いた装填済みの絵、鉄砲弾・焼夷弾・散弾）の絵とモデルを作る。

どれも、64×64の平らなアイコン（斜めに、左下が銃床・右上が銃口）。種子島の実物の姿（細長い八角の銃身・真鍮の帯・火皿・
蛇杖（火縄を挟む腕）・込め矢・短い銃床）に寄せて、形は軸に沿った距離で描く。銃のモデルは、バニラの剣と同じ item/handheld
（手に持ったとき、道具と同じ向きになる）。弾は、持つ物ではないので item/generated。統合版も、平らなアイコンのまま出す。

  python3 tools/make_guns.py            絵とモデルを書き出す
  python3 tools/make_guns.py --preview  絵を拡大して並べる（build/guns/preview.png）
"""
import argparse
import json
import math
from PIL import Image
from artwork import PACK, BUILD
from pixelart import Canvas, mix, noise, rgba

SIZE = 64
# （名前, 持ち方）。持ち方: handheld は道具のように持つ、generated は物のように持つ
GUNS = [('matchlock', 'handheld'), ('matchlock_loaded', 'handheld'), ('tanzutsu', 'handheld'), ('tanzutsu_loaded', 'handheld'),
        ('ammo_teppo', 'generated'), ('ammo_shoidan', 'generated'), ('ammo_sandan', 'generated')]

STEEL = ('#2f3644', '#566072', '#8f9cb0')        # 黒ずんだ銃身（暗・中・ハイライト）
WOOD = ('#4a2c18', '#7a4a26', '#a8703c')         # 銃床（暗・中・明）
BRASS, BRASS_DARK, BRASS_LIGHT = '#c9a03c', '#8a6a1e', '#f0d27a'
CORD, CORD_DARK = '#8a8472', '#5e5848'
EMBER, EMBER_BRIGHT, EMBER_GLOW = '#ff8a1f', '#fff0a0', '#ff4a1a'


def unit(a, b):
    d = math.dist(a, b)
    return ((b[0] - a[0]) / d, (b[1] - a[1]) / d)


def local(point, origin, d):
    """点を、origin から d（単位ベクトル）へ向かう座標に直す。(s=進んだ距離, u=右下側へ測った距離)。"""
    dx, dy = point[0] - origin[0], point[1] - origin[1]
    return dx * d[0] + dy * d[1], dx * -d[1] + dy * d[0]


def at(origin, d, s, u):
    """local の逆。軸の座標 (s, u) の点。"""
    return origin[0] + d[0] * s + -d[1] * u, origin[1] + d[1] * s + d[0] * u


def barrel(canvas, origin, d, start, end, half, bell=2.3):
    """八角の銃身。断面を帯に分けて、光の当たり方を変え、真鍮の帯と、先の朝顔（銃口の広がり）を付ける。"""
    dark, mid, light = (rgba(c) for c in STEEL)
    brass, brass_dark = rgba(BRASS), rgba(BRASS_DARK)
    def width(s): return half + (bell - half) * max(0.0, (s - (end - 5)) / 5) ** 2
    def inside(x, y):
        s, u = local((x, y), origin, d)
        return start <= s <= end and abs(u) <= width(s)
    def shade(x, y):
        s, u = local((x, y), origin, d)
        w = width(s)
        v = u / w
        if end - 1.6 <= s <= end: return brass_dark if v > 0 else brass          # 銃口の口金
        if v < -0.6: return light
        if v < -0.15: return mix(mid, light, 0.5)
        if v < 0.45: return mid
        return dark
    canvas.fill(inside, shade)
    for position in (start + (end - start) * 0.28, start + (end - start) * 0.52, start + (end - start) * 0.76):
        for u in range(-3, 4):                                                    # 真鍮の帯（竹の節のように巻く）
            for s in (0.0, 1.0):
                canvas.put(*at(origin, d, position + s, u * 0.62), brass if u < 1 else brass_dark)
    canvas.put(*at(origin, d, end - 3.5, -half - 0.6), rgba(BRASS_LIGHT))         # 先の照星
    canvas.put(*at(origin, d, start + 3.0, -half - 0.6), rgba(BRASS_LIGHT))       # 手前の照門


def stock(canvas, origin, d, start, end, half_butt, half_lock):
    """銃床。種子島の銃床は、短く、細く、後ろへ向かって、わずかに下がる。"""
    dark, mid, light = (rgba(c) for c in WOOD)
    rng = noise(7)
    def half(s):
        f = (s - start) / (end - start)
        return half_butt + (half_lock - half_butt) * min(1.0, f * 1.4)
    def inside(x, y):
        s, u = local((x, y), origin, d)
        droop = 1.4 * max(0.0, 1 - (s - start) / 7.0) ** 2        # 台尻が、少し下がる
        return start <= s <= end and -half(s) + droop <= u <= half(s) + droop
    def shade(x, y):
        s, u = local((x, y), origin, d)
        v = u / half(s)
        grain = math.sin(s * 1.7 + u * 0.8) * 0.5
        if v < -0.5: return light if grain > -0.2 else mid
        if v > 0.45: return dark
        return mid if grain > -0.1 else dark
    canvas.fill(inside, shade)


def lock(canvas, origin, d, s0, loaded):
    """火縄の仕掛け: 真鍮の側板・火皿（蓋つき）・蛇杖（火縄を挟む腕）と火縄。装填済みは、火縄の先が赤く燃える。"""
    brass, brass_dark, brass_light = rgba(BRASS), rgba(BRASS_DARK), rgba(BRASS_LIGHT)
    def plate(x, y):
        s, u = local((x, y), origin, d)
        return s0 <= s <= s0 + 7.5 and abs(u) <= 3.0
    canvas.fill(plate, lambda x, y: brass_dark if local((x, y), origin, d)[1] > 0.8 else brass)
    for s, u in ((s0 + 1.5, 0.0), (s0 + 5.5, 0.5)): canvas.put(*at(origin, d, s, u), brass_light)   # 留め釘
    # 火皿: 銃身の脇の、小さな皿と蓋
    pan = at(origin, d, s0 + 8.6, -3.0)
    for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)): canvas.put(pan[0] + dx, pan[1] + dy, brass_light if dx + dy < 2 else brass)
    # 蛇杖: 側板から、火皿へ向かって、S字に曲がる腕（暗い鉄）
    arm = rgba('#2a2f3a')
    pts = [at(origin, d, s0 + 2.0, -2.5), at(origin, d, s0 + 1.0, -5.0), at(origin, d, s0 + 3.0, -7.0), at(origin, d, s0 + 6.0, -7.4), at(origin, d, s0 + 8.2, -5.6)]
    for a, b in zip(pts, pts[1:]): canvas.line(a, b, arm, 1)
    # 火縄: 蛇杖の先から、細く垂れる縄。先に火が付く
    tip = pts[-1]
    cord = rgba(CORD)
    end = (tip[0] + 2.0, tip[1] - 2.2)
    canvas.line(tip, end, cord, 1)
    canvas.put(*tip, rgba(CORD_DARK))
    if loaded:
        canvas.put(*end, rgba(EMBER_BRIGHT))
        for gx, gy in ((1, 0), (0, -1), (1, -1), (-1, 0)): canvas.put(end[0] + gx, end[1] + gy, rgba(EMBER_GLOW))
        canvas.put(end[0] + 1, end[1] - 2, rgba(EMBER))
        canvas.put(end[0] - 1, end[1] - 1, rgba(EMBER))
    else:
        canvas.put(*end, rgba(CORD_DARK))


def ramrod(canvas, origin, d, start, end):
    """銃身の下の、込め矢。"""
    rod = (rgba('#c9a874'), rgba('#7a5a34'))
    for s in range(int(start), int(end)):
        canvas.put(*at(origin, d, s, 2.7), rod[0])
        canvas.put(*at(origin, d, s, 3.5), rod[1])


def long_gun(loaded):
    canvas = Canvas(SIZE)
    origin, tip = (2.0, 61.0), (60.0, 3.0)
    d = unit(origin, tip)
    length = math.dist(origin, tip)
    stock(canvas, origin, d, 0.0, 30.0, 2.2, 3.0)
    barrel(canvas, origin, d, 13.0, length - 1.0, 1.6)
    ramrod(canvas, origin, d, 26.0, length - 7.0)
    lock(canvas, origin, d, 13.0, loaded)
    canvas.outline(rgba('#14101a'))
    return canvas.image


def short_gun(loaded):
    canvas = Canvas(SIZE)
    origin, tip = (12.0, 54.0), (49.0, 17.0)
    d = unit(origin, tip)
    length = math.dist(origin, tip)
    # 握り: 銃身の向きから、下へ曲がった短い台。握り玉（真鍮）で終わる
    grip_dir = (math.cos(math.radians(60)) * d[0] - math.sin(math.radians(60)) * d[1] * -1, 0)
    gdir = (-0.45, 0.89)
    def grip(x, y):
        s, u = local((x, y), (origin[0] + d[0] * 9, origin[1] + d[1] * 9), gdir)
        return 0.0 <= s <= 15.0 and abs(u) <= 2.8 - s * 0.05
    canvas.fill(grip, lambda x, y: rgba(WOOD[0]) if local((x, y), origin, gdir)[1] > 0.9 else (rgba(WOOD[2]) if local((x, y), origin, gdir)[1] < -0.9 else rgba(WOOD[1])))
    knob = (origin[0] + d[0] * 9 + gdir[0] * 15.5, origin[1] + d[1] * 9 + gdir[1] * 15.5)
    canvas.fill(lambda x, y: (x - knob[0]) ** 2 + (y - knob[1]) ** 2 <= 9.0, lambda x, y: rgba(BRASS_LIGHT) if x + y < knob[0] + knob[1] else rgba(BRASS_DARK))
    stock(canvas, origin, d, 0.0, 15.0, 2.8, 3.4)
    barrel(canvas, origin, d, 6.0, length - 1.0, 1.8, bell=2.5)
    lock(canvas, origin, d, 6.0, loaded)
    canvas.outline(rgba('#14101a'))
    return canvas.image


def ball(canvas, cx, cy, radius, colors):
    """丸い弾。colors は、明・中・暗。左上から光が当たる。"""
    light, mid, dark = (rgba(c) for c in colors)
    def inside(x, y): return (x - cx) ** 2 + (y - cy) ** 2 <= radius * radius
    def shade(x, y):
        shade_v = ((x - cx) + (y - cy)) / (2 * radius)
        if (x - cx) < -radius * 0.25 and (y - cy) < -radius * 0.25 and shade_v < -0.62: return rgba('#ffffff')
        return light if shade_v < -0.3 else (dark if shade_v > 0.3 else mid)
    canvas.fill(inside, shade)


def ammo(kind):
    canvas = Canvas(SIZE)
    if kind == 'teppo':        # 鉛の丸い弾
        ball(canvas, 32, 34, 14, ('#c8ced8', '#868f9d', '#454c58'))
    elif kind == 'shoidan':    # 火薬を詰めた、火を帯びる弾（赤黒い鉄の玉と、燃える炎）
        ball(canvas, 32, 38, 12, ('#9a4a3a', '#5a2a22', '#2a1210'))
        flame = [(32, 16, '#ffe08a'), (30, 20, '#ff9a2a'), (34, 20, '#ff9a2a'), (28, 24, '#ff5a1f'), (36, 24, '#ff5a1f'), (32, 22, '#ffd36a'),
                 (31, 28, '#ff7a1f'), (33, 28, '#ff7a1f'), (29, 30, '#ff4a1a'), (35, 30, '#ff4a1a')]
        for x, y, c in flame:
            for dx in range(2):
                for dy in range(3): canvas.put(x + dx, y + dy, c)
        for x, y in ((32, 12), (31, 14), (33, 15)): canvas.put(x, y, '#ffd36a')
    else:                      # 散弾: 小さな鉛の弾が、ばらばらに
        for cx, cy in ((20, 40), (32, 44), (44, 40), (26, 30), (38, 30), (32, 20), (22, 52), (42, 52), (32, 33)):
            ball(canvas, cx, cy, 5.5, ('#c8ced8', '#868f9d', '#454c58'))
    canvas.outline(rgba('#15131a'))
    return canvas.image


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
    scale, columns = 6, 4
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
