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
HEIGHT, ASCENT = 144, 78


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
    """照準。円の外は黒、円の中は透明。中央に細い十字線と、小さな点。"""
    radius = 0.92
    image = pixels(lambda dx, dy: (0, 0, 0, 238 if math.hypot(dx, dy) > radius else (int(238 * max(0.0, (math.hypot(dx, dy) - (radius - 0.06)) / 0.06)))))
    draw = ImageDraw.Draw(image)
    cx, cy, r = W / 2, H / 2, radius * H / 2
    draw.line((cx - r, cy, cx - 10, cy), fill=(10, 10, 10, 235), width=2)
    draw.line((cx + 10, cy, cx + r, cy), fill=(10, 10, 10, 235), width=2)
    draw.line((cx, cy - r, cx, cy - 10), fill=(10, 10, 10, 235), width=2)
    draw.line((cx, cy + 10, cx, cy + r), fill=(10, 10, 10, 235), width=2)
    draw.ellipse((cx - 2, cy - 2, cx + 2, cy + 2), fill=(200, 30, 30, 255))
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
    print('Preview: ' + str(out / 'screens.png'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview', action='store_true')
    args = parser.parse_args()
    preview() if args.preview else build()


if __name__ == '__main__': main()
