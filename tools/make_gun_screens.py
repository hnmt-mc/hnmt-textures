#!/usr/bin/env python3
"""銃の画面の演出の絵（発射のフラッシュ・スコープの照準・装填中の種火の光・不発の灰色のにじみ）と、文字として登録するフォントを作る。

どれも 512×256 の透明な絵。サーバーが、タイトルの文字（\\uE010〜\\uE013）として画面に重ねる（刀の画面の演出と同じ仕組み）。
画面の大きさはさまざまなので、絵は画面の中央に寄せ、縁は大きめにとってある（画面からはみ出した分は、見えなくなる）。

  python3 tools/make_gun_screens.py            絵とフォントを書き出す
  python3 tools/make_gun_screens.py --preview  暗い背景に重ねた見本を作る（build/guns/screens.png）
"""
import argparse
import json
import math
from PIL import Image, ImageDraw
from artwork import PACK, BUILD

W, H = 512, 256
# （名前, 文字）。文字は、サーバー（GunEffects）と同じ
SCREENS = [('gun_flash', ''), ('gun_scope', ''), ('gun_ember', ''), ('gun_smoke', '')]
# 絵の中心が、画面の中心（クロスヘア）に重なるように、基準線の位置を決める（タイトルの文字は、画面の中心の少し上に基準線が来る）
HEIGHT, ASCENT = 144, 69


def pixels(fn):
    image = Image.new('RGBA', (W, H))
    px = image.load()
    for y in range(H):
        for x in range(W):
            px[x, y] = fn((x - W / 2) / (H / 2), (y - H / 2) / (H / 2))   # 高さを1とした座標（中央が0）
    return image


def flash():
    """発射のフラッシュ。中央が白く、まわりへ薄れる。"""
    def f(dx, dy):
        a = max(0.0, 1.0 - math.hypot(dx * 0.7, dy)) ** 1.5
        return (255, 250, 235, int(215 * a))
    return pixels(f)


def scope():
    """照準（FPS のスコープ）。画面を覆わない。中央の、細い十字線と、小さな輪だけ。白い線に、暗い縁を付けて、明るい所でも見える。"""
    image = Image.new('RGBA', (W, H))
    draw = ImageDraw.Draw(image)
    cx, cy = W / 2, H / 2
    light, shadow = (255, 255, 255, 235), (0, 0, 0, 170)
    def line(points, width=2):
        draw.line(points, fill=shadow, width=width + 2)
        draw.line(points, fill=light, width=width)
    for sign in (-1, 1):
        line((cx + sign * 9, cy, cx + sign * 40, cy))                    # 左右の線（中央は、あける）
        line((cx, cy + sign * 9, cx, cy + sign * 40))                    # 上下の線
        line((cx + sign * 40, cy - 5, cx + sign * 40, cy + 5), 2)        # 目盛り（左右）
        line((cx - 5, cy + sign * 40, cx + 5, cy + sign * 40), 2)        # 目盛り（上下）
    draw.ellipse((cx - 56, cy - 56, cx + 56, cy + 56), outline=(255, 255, 255, 110), width=2)   # 外の細い輪
    draw.ellipse((cx - 2, cy - 2, cx + 2, cy + 2), fill=(230, 40, 40, 255))                      # 中央の赤い点
    return image


SCOPE_W, SCOPE_H = 1024, 576      # 16:9。画面いっぱいに引き伸ばされる（カボチャのかぶり物と同じ）


def scope_view():
    """スコープを覗いた画面。円の外は黒、円の中は透明。円の中に、太い黒の線が縁から中央へ細くなる十字線と、目盛りの点。
    サーバーが、頭の防具を一時的に、この絵のかぶり物（equippable の camera_overlay）に見せかけて、画面いっぱいに出す。"""
    image = Image.new('RGBA', (SCOPE_W, SCOPE_H), (0, 0, 0, 255))
    cx, cy = SCOPE_W / 2, SCOPE_H / 2
    radius = SCOPE_H * 0.47
    px = image.load()
    for y in range(SCOPE_H):
        for x in range(SCOPE_W):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d <= radius - 5: px[x, y] = (0, 0, 0, 0)
            elif d <= radius: px[x, y] = (0, 0, 0, int(255 * (d - (radius - 5)) / 5))    # レンズの縁（なめらかに黒へ）
    ring = Image.new('RGBA', (SCOPE_W, SCOPE_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(ring)
    r = radius - 4
    # 十字線: 縁は太く、中央へ細くなる（先細りの帯）。中央は、あけて、赤い点
    for sign in (-1, 1):
        for step in range(int(r - 26)):
            t = step / (r - 26)
            width = 1 + 6 * (1 - t) ** 2                     # 中央側が細く、縁側が太い
            x = cx + sign * (26 + (r - 26) * (1 - t))
            draw.rectangle((x - 0.5, cy - width / 2, x + 0.5, cy + width / 2), fill=(0, 0, 0, 255))
            y = cy + sign * (26 + (r - 26) * (1 - t))
            draw.rectangle((cx - width / 2, y - 0.5, cx + width / 2, y + 0.5), fill=(0, 0, 0, 255))
    for k in (1, 2, 3, 4):                                    # 目盛りの点
        for sign in (-1, 1):
            for dx, dy in ((k * 42 * sign, 0), (0, k * 42 * sign)):
                draw.ellipse((cx + dx - 3, cy + dy - 3, cx + dx + 3, cy + dy + 3), fill=(0, 0, 0, 255))
    draw.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), fill=(230, 40, 40, 255))
    image.alpha_composite(ring)
    return image


def ember():
    """火縄の種火の光。画面の下の中央から、橙の光が上へ薄れる。"""
    def f(dx, dy):
        a = max(0.0, 1.0 - math.hypot(dx * 0.45, (dy - 1.0) * 0.9)) ** 1.8
        return (255, 120, 30, int(150 * a))
    return pixels(f)


def smoke():
    """不発・火縄の消えの、灰色のにじみ。縁が濃く、中央は透明。"""
    def f(dx, dy):
        d = min(1.0, math.hypot(dx * 0.85, dy))
        a = max(0.0, (d - 0.4) / 0.6) ** 1.5
        return (110, 110, 118, int(150 * a))
    return pixels(f)


def font():
    return {'providers': [{'type': 'bitmap', 'file': 'hnmt:font/%s.png' % name, 'ascent': ASCENT, 'height': HEIGHT, 'chars': [char]}
                          for name, char in SCREENS]}


IMAGES = {'gun_flash': flash, 'gun_scope': scope, 'gun_ember': ember, 'gun_smoke': smoke}


def build():
    target = PACK / 'assets/hnmt/textures/font'
    target.mkdir(parents=True, exist_ok=True)
    for name, make in IMAGES.items(): make().save(target / (name + '.png'))
    misc = PACK / 'assets/hnmt/textures/misc'
    misc.mkdir(parents=True, exist_ok=True)
    scope_view().save(misc / 'gun_scope.png')
    path = PACK / 'assets/hnmt/font/gun.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(font(), ensure_ascii=False, indent=2) + '\n')
    print('Wrote %d gun screen images' % len(SCREENS))


def preview():
    out = BUILD / 'guns'
    out.mkdir(parents=True, exist_ok=True)
    sheet = Image.new('RGBA', (W * 2 + 24, H * 2 + 24), (58, 66, 80, 255))
    for i, name in enumerate(IMAGES):
        sheet.alpha_composite(IMAGES[name](), (8 + (i % 2) * (W + 8), 8 + (i // 2) * (H + 8)))
    sheet.save(out / 'screens.png')
    scope_view().resize((SCOPE_W // 2, SCOPE_H // 2)).save(out / 'scope_view.png')
    print('Preview: ' + str(out / 'screens.png'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview', action='store_true')
    args = parser.parse_args()
    preview() if args.preview else build()


if __name__ == '__main__': main()
