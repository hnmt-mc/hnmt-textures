#!/usr/bin/env python3
"""刀と鞘（刀3種・妖刀・名刀2振り・刺股・レイピア・鞘2状態）の絵とモデルを作る。

どれも、64×64の平らなアイコン（斜めに、左下が柄・右上が切っ先）。実際の刀の姿（反りのある刃・鍔・柄巻き・鞘）に寄せて、
刃は中心線からの距離で、柄巻きは斜めの網目で描く。モデルは、バニラの剣と同じ item/handheld（手に持ったとき、剣と同じ向きになる）。
鞘は、持つ物ではないので item/generated。統合版も、平らなアイコンのまま出す。

  python3 tools/make_blades.py            絵とモデルを書き出す
  python3 tools/make_blades.py --preview  絵を拡大して並べる（build/blades/preview.png）
"""
import argparse
import json
import math
from PIL import Image
from artwork import PACK, BUILD
from pixelart import Canvas, Curve, mix, noise, rgba

SIZE = 64
# （名前, 表示名, 持ち方）。持ち方: handheld は剣のように持つ、generated は物のように持つ
BLADES = [('katana_iron', '鉄の刀', 'handheld'), ('katana_diamond', 'ダイヤの刀', 'handheld'), ('katana_netherite', 'ネザライトの刀', 'handheld'),
          ('youtou', '妖刀', 'handheld'), ('meito_izumi', '和泉守兼定', 'handheld'), ('meito_nagasone', '長曽祢虎徹', 'handheld'),
          ('sasumata', '刺股', 'handheld'), ('rapier', 'レイピア', 'handheld'), ('sheath', '鞘', 'generated'), ('sheath_full', '鞘（刀入り）', 'generated')]

# 刀ごとの色。blade: 刃の（棟・平地・刃先）、glow: 黒い刃に走る光るひび（なければ、ふつうの鋼の刃）、
# tsuba: 鍔（地・縁）、wrap: 柄巻き（地・巻き）、metal: 鍔元・頭の金具
STYLES = {
    'katana_iron': dict(blade=('#6d7684', '#aab3c0', '#f1f4f8'), hamon='#ffffff', tsuba=('#3a3e48', '#9a7a3a'), wrap=('#d8d2c0', '#26262e'), metal='#9a7a3a'),
    'katana_diamond': dict(blade=('#1f8f8a', '#5fd8d1', '#e4fffc'), hamon='#ffffff', tsuba=('#1c5a58', '#6fe0da'), wrap=('#cfe8ea', '#1f3a52'), metal='#4fc0ba'),
    'katana_netherite': dict(blade=('#3a343f', '#5f566b', '#aaa2b4'), hamon='#c9c0d2', tsuba=('#26202a', '#c19a45'), wrap=('#2a1c1c', '#5a3636'), metal='#c19a45'),
    'youtou': dict(blade=('#07070a', '#15151b', '#34343f'), glow='#ff2a3a', tsuba=('#1a0c10', '#8a1024'), wrap=('#e8e4e0', '#c8182a'), metal='#8a1024'),
    'meito_izumi': dict(blade=('#07070a', '#15151b', '#34343f'), glow='#ffd23a', tsuba=('#16130a', '#e0b030'), wrap=('#16130a', '#f0c030'), metal='#e0b030'),
    'meito_nagasone': dict(blade=('#07070a', '#15151b', '#34343f'), glow='#35e04a', tsuba=('#0c120c', '#52667a'), wrap=('#101410', '#2a3a2a'), metal='#3a4a3a'),
}
LACQUER = ('#16161b', '#2c2c34', '#4a4a56')
GOLD, GOLD_DARK = '#e0b84a', '#8f6f22'

# 刀の幾何（右上へ伸びる。y は下向き）。柄頭（kashira）・鍔の位置（guard）・切っ先（tip）
POMMEL, GUARD, TIP = (5.0, 59.0), (17.5, 46.5), (59.5, 4.5)


def local(point, origin, direction):
    """点を、origin から direction（単位ベクトル）へ向かう座標に直す。(s=進んだ距離, u=右下側へ測った距離)。"""
    dx, dy = point[0] - origin[0], point[1] - origin[1]
    return dx * direction[0] + dy * direction[1], dx * -direction[1] + dy * direction[0]


def unit(a, b):
    d = math.dist(a, b)
    return ((b[0] - a[0]) / d, (b[1] - a[1]) / d)


def blade_curve(start=GUARD, tip=TIP, sori=4.0):
    """反りのある刃の中心線。棟側（左上）へ、中ほどが膨らむ。"""
    mid = ((start[0] + tip[0]) / 2, (start[1] + tip[1]) / 2)
    d = unit(start, tip)
    normal = (d[1], -d[0])          # 左上向き（棟の側）
    return Curve([start, (mid[0] + normal[0] * sori, mid[1] + normal[1] * sori), tip])


def half_width(t, base=2.9, taper=0.22):
    """刃の半分の幅。根元から切っ先へ細り、切っ先のあたり（横手より先）で、とがる。"""
    if t < 0.9: return base * (1 - taper * t)
    return max(0.0, base * (1 - taper * 0.9) * (1 - (t - 0.9) / 0.1) ** 0.8)


def offset(curve, t, u):
    """中心線の位置 t から、右下側（刃先の側）へ u だけ離れた点。"""
    x, y = curve.point(t)
    a, b = curve.point(max(0.0, t - 0.01)), curve.point(min(1.0, t + 0.01))
    d = unit(a, b)
    return x + -d[1] * u, y + d[0] * u


def crack_paths(curve, seed, base):
    """光るひびの経路（(t, u) の並び）。長いひびが数本、棟と刃先のあいだを、ぎざぎざに走り、ときどき枝分かれする。"""
    rng = noise(seed)
    paths = []
    for k in range(3):
        t = 0.08 + k * 0.3 + rng.random() * 0.08
        u = rng.uniform(-0.6, 0.6) * base
        path = [(t, u)]
        for step in range(rng.randint(9, 15)):
            t += rng.uniform(0.014, 0.024)
            u = max(-0.85 * base, min(0.85 * base, u + rng.uniform(-0.9, 0.9)))
            path.append((t, u))
            if rng.random() < 0.12 and t < 0.9:                           # 枝
                branch, bt, bu = [(t, u)], t, u
                drift = rng.choice((-0.5, 0.5))
                for _ in range(rng.randint(2, 4)):
                    bt += rng.uniform(0.008, 0.018)
                    bu = max(-0.85 * base, min(0.85 * base, bu + drift + rng.uniform(-0.3, 0.3)))
                    branch.append((bt, bu))
                paths.append(branch)
        paths.append(path)
    return paths


def draw_blade(canvas, curve, style, seed, base=2.4):
    colors = style['blade']
    ridge, flat, edge = (rgba(c) for c in colors)
    glow = style.get('glow')
    def inside(x, y):
        t, u = curve.locate(x, y)
        return 0.0 <= t <= 1.0 and abs(u) <= half_width(t, base)
    def shade(x, y):
        t, u = curve.locate(x, y)
        w = max(half_width(t, base), 0.01)
        v = u / w                                   # -1（棟）〜 +1（刃先）
        if v < -0.78: return ridge
        if v < -0.45: return mix(ridge, flat, (v + 0.78) / 0.33)
        if 'hamon' in style:                        # 鋼の刃: 刃先寄りに、白く波打つ刃文
            wave = math.sin(t * 38) * 0.12
            if 0.12 + wave < v < 0.38 + wave: return rgba(style['hamon'])
            if v > 0.82: return edge
            return mix(flat, edge, max(0.0, (v - 0.35) / 0.9))
        if v > 0.8: return edge                     # 黒い刃: 刃先だけ、わずかに光る
        return mix(flat, edge, max(0.0, (v - 0.3) / 1.0) ** 1.5)
    canvas.fill(inside, shade)
    if glow:
        halo = mix('#15151b', glow, 0.3)
        lit = rgba(glow)
        for path in crack_paths(curve, seed, base):
            points = [offset(curve, t, u) for t, u in path if 0.0 <= t <= 0.97]
            for (x0, y0), (x1, y1) in zip(points, points[1:]):
                if not (inside(x0, y0) and inside(x1, y1)): continue
                steps = int(max(abs(x1 - x0), abs(y1 - y0))) * 2 + 1
                for i in range(steps + 1):
                    f = i / steps
                    x, y = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        px, py = int(x + dx), int(y + dy)
                        if inside(px + 0.5, py + 0.5) and canvas.get(px, py)[:3] != lit[:3]: canvas.put(px, py, halo)
                for i in range(steps + 1):
                    f = i / steps
                    canvas.put(x0 + (x1 - x0) * f, y0 + (y1 - y0) * f, lit)


def draw_hilt(canvas, style, start=GUARD, end=POMMEL, half=2.6):
    """柄。鍔のそばから柄頭まで。斜めの網目の柄巻きと、頭・縁の金具。"""
    d = unit(start, end)
    length = math.dist(start, end)
    base, wrap = (rgba(c) for c in style['wrap'])
    metal = rgba(style['metal'])
    def inside(x, y):
        s, u = local((x, y), start, d)
        bulge = 0.35 * math.sin(math.pi * min(1.0, max(0.0, s / length)))
        return 0.0 <= s <= length and abs(u) <= half + bulge
    def shade(x, y):
        s, u = local((x, y), start, d)
        if s < 1.6 or s > length - 2.0: return metal                      # 縁（鍔の側）・頭（柄頭）
        a, b = (s + u * 1.5) % 5.0, (s - u * 1.5) % 5.0
        if a < 1.6 or b < 1.6: return wrap                                # 柄巻き（斜めの網目）
        return base
    canvas.fill(inside, shade)


def draw_tsuba(canvas, style, center=GUARD, direction=None, radius=7.2, thick=2.2):
    """鍔。刃の向きに直角な、平たい円盤。地と縁の2色。"""
    d = direction or unit(GUARD, TIP)
    ground, rim = (rgba(c) for c in style['tsuba'])
    def inside(x, y):
        s, u = local((x, y), center, d)
        return (s / thick) ** 2 + (u / radius) ** 2 <= 1.0
    def shade(x, y):
        s, u = local((x, y), center, d)
        return rim if (s / thick) ** 2 + (u / radius) ** 2 > 0.58 else ground
    canvas.fill(inside, shade)


def katana(name):
    style = STYLES[name]
    canvas = Canvas(SIZE)
    curve = blade_curve()
    draw_blade(canvas, curve, style, seed=sum(map(ord, name)))
    habaki = rgba(style['metal'])
    for t in (0.0, 0.015, 0.03):                                        # 鍔の先の、金色の帯（はばき）
        x, y = curve.point(t)
        for u in (-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0):
            d = unit(curve.point(max(0.0, t - 0.01)), curve.point(t + 0.01))
            canvas.put(x + -d[1] * -u, y + d[0] * -u, habaki)
    draw_tsuba(canvas, style)
    draw_hilt(canvas, style)
    canvas.outline(mix('#000000', style['blade'][0], 0.25))
    return canvas.image


def sasumata():
    canvas = Canvas(SIZE)
    wood, wood_dark = rgba('#a07040'), rgba('#6b4524')
    steel, steel_dark, steel_light = rgba('#8a95a4'), rgba('#4a5260'), rgba('#d6dde6')
    start, base = (4.0, 60.0), (38.0, 26.0)
    d = unit(start, base)
    pole_len = math.dist(start, base)
    def pole(x, y):
        s, u = local((x, y), start, d)
        return 0 <= s <= pole_len and abs(u) <= 1.9
    def pole_color(x, y):
        s, u = local((x, y), start, d)
        if (s % 9.0) < 1.3: return rgba('#d8c89a')                      # 棒の巻き
        return wood_dark if u > 0.6 else wood
    canvas.fill(pole, pole_color)
    # U字の先。棒の先の受け金具から、2本の腕が先へ伸び、先端は外へ反る。腕の底は、つなぎでつなぐ
    spread, arm_len, claw = 6.5, 15.0, 3.5
    def head(x, y):
        s, u = local((x, y), base, d)
        if -4.0 <= s <= 0.5 and abs(u) <= 3.4: return True               # 受け金具
        if -0.5 <= s <= 1.8 and abs(u) <= spread + 1.4: return True       # つなぎ
        if 0.0 <= s <= arm_len and abs(abs(u) - spread) <= 1.3: return True   # 腕
        if arm_len < s <= arm_len + claw:                                   # 爪（外へ反る）
            out = (s - arm_len) * 0.7
            return abs(abs(u) - (spread + out)) <= 1.1
        return False
    def head_color(x, y):
        s, u = local((x, y), base, d)
        if s < 0.5: return steel_light if u < 0 else steel_dark
        if abs(abs(u) - spread) < 0.5 and s < arm_len: return steel_light if u < 0 else steel
        return steel_dark if (s < 1.8 or u > 0) else steel
    canvas.fill(head, head_color)
    canvas.outline(rgba('#2a2018'))
    return canvas.image


def rapier():
    canvas = Canvas(SIZE)
    start, tip = (17.0, 47.0), (61.0, 3.0)
    d = unit(start, tip)
    length = math.dist(start, tip)
    steel, steel_dark, steel_light = rgba('#aeb8c4'), rgba('#5d6878'), rgba('#f4f7fa')
    def blade(x, y):
        s, u = local((x, y), start, d)
        return 0 <= s <= length and abs(u) <= max(0.0, 1.45 * (1 - (s / length) ** 3))
    canvas.fill(blade, lambda x, y: steel_dark if local((x, y), start, d)[1] > 0.5 else (steel_light if local((x, y), start, d)[1] < -0.3 else steel))
    # 椀形の護拳（つばの皿）と、握り・柄頭
    gold, gold_dark = rgba(GOLD), rgba(GOLD_DARK)
    guard = (15.5, 48.5)
    def cup(x, y):
        s, u = local((x, y), guard, d)
        return (s / 3.4) ** 2 + (u / 8.4) ** 2 <= 1.0
    canvas.fill(cup, lambda x, y: gold if local((x, y), guard, d)[0] > -0.2 else gold_dark)
    for sign in (-1, 1):                                                  # 十字の鍔
        a = (guard[0] - d[1] * 9.5 * -sign * -1, guard[1] + d[0] * 9.5 * -sign * -1)
    grip_start, grip_end = (14.0, 50.0), (6.0, 58.0)
    grip = unit(grip_start, grip_end)
    glen = math.dist(grip_start, grip_end)
    def handle(x, y):
        s, u = local((x, y), grip_start, grip)
        return 0 <= s <= glen and abs(u) <= 1.7
    canvas.fill(handle, lambda x, y: rgba('#2a1c14') if (local((x, y), grip_start, grip)[0] + local((x, y), grip_start, grip)[1] * 1.2) % 3.5 < 1.2 else rgba('#6a4a30'))
    for cx, cy, r in ((4.8, 59.2, 2.5),):                                # 柄頭の玉
        canvas.fill(lambda x, y, cx=cx, cy=cy, r=r: (x - cx) ** 2 + (y - cy) ** 2 <= r * r, lambda x, y: gold if x + y < 64 else gold_dark)
    canvas.outline(rgba('#2b2f38'))
    return canvas.image


def sheath(full):
    canvas = Canvas(SIZE)
    # 鞘（黒漆）。刀と同じ反りで、口（柄の側）から、先（鐺）まで
    start, tip = (19.0, 45.0), (60.0, 5.0)
    curve = blade_curve(start, tip, sori=3.6)
    dark, mid, light = (rgba(c) for c in LACQUER)
    def inside(x, y):
        t, u = curve.locate(x, y)
        return 0.0 <= t <= 1.0 and abs(u) <= 3.3 * (1 - 0.1 * t)
    def shade(x, y):
        t, u = curve.locate(x, y)
        v = u / 3.3
        if v < -0.55: return light                                       # 漆の艶（棟の側）
        if v > 0.5: return dark
        return mid
    canvas.fill(inside, shade)
    gold, gold_dark = rgba(GOLD), rgba(GOLD_DARK)
    for t, wide in ((0.0, 3.8), (0.04, 3.8)):                            # 口金（鯉口）
        x, y = curve.point(t)
        d = unit(curve.point(max(0.0, t - 0.01)), curve.point(t + 0.01))
        for u in range(-4, 5): canvas.put(x + -d[1] * -u, y + d[0] * -u, gold if u < 2 else gold_dark)
    for t in (0.94, 0.985):                                              # 鐺（先の金具）
        x, y = curve.point(t)
        d = unit(curve.point(max(0.0, t - 0.01)), curve.point(min(1.0, t + 0.01)))
        for u in range(-3, 4): canvas.put(x + -d[1] * -u, y + d[0] * -u, gold if u < 1 else gold_dark)
    x, y = curve.point(0.45)                                             # 帯取りの金具と、下げ緒（赤い組紐）
    for k in range(-4, 5):
        canvas.put(x + k * 0.7, y + k * 0.7 + 1, gold_dark)
    cord = rgba('#b8202c')
    for i in range(10):
        canvas.put(x + 3 + i * 0.5, y + 4 + i * 1.1 + math.sin(i) * 0.6, cord)
    if full:
        # 刀が入っている: 鞘の口から、鍔と柄が見える
        style = STYLES['katana_iron']
        draw_tsuba(canvas, dict(style, tsuba=('#3a3e48', '#9a7a3a')), center=(17.0, 47.0), direction=unit(start, tip), radius=6.4, thick=2.0)
        draw_hilt(canvas, dict(style, wrap=('#d8d2c0', '#1f3a7a'), metal='#9a7a3a'), start=(16.0, 48.0), end=(5.0, 59.0), half=2.4)
    canvas.outline(rgba('#07070a'))
    return canvas.image


def draw(name):
    if name in STYLES: return katana(name)
    if name == 'sasumata': return sasumata()
    if name == 'rapier': return rapier()
    if name == 'sheath': return sheath(False)
    if name == 'sheath_full': return sheath(True)
    raise ValueError('Unknown blade: ' + name)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def build():
    for name, _, holding in BLADES:
        path = PACK / 'assets/hnmt/textures/item/sword' / (name + '.png')
        path.parent.mkdir(parents=True, exist_ok=True)
        draw(name).save(path)
        write_json(PACK / 'assets/hnmt/items/sword' / (name + '.json'), {'model': {'type': 'minecraft:model', 'model': 'hnmt:item/sword/' + name}})
        write_json(PACK / 'assets/hnmt/models/item/sword' / (name + '.json'),
                   {'parent': 'minecraft:item/' + holding, 'textures': {'layer0': 'hnmt:item/sword/' + name}})
    print('Wrote %d blade icons' % len(BLADES))


def preview():
    target = BUILD / 'blades'
    target.mkdir(parents=True, exist_ok=True)
    scale, columns = 6, 5
    rows = (len(BLADES) + columns - 1) // columns
    sheet = Image.new('RGBA', (columns * (SIZE * scale + 8) + 8, rows * (SIZE * scale + 8) + 8), (232, 226, 214, 255))
    for i, (name, _, _) in enumerate(BLADES):
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
