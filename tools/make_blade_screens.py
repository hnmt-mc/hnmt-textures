#!/usr/bin/env python3
"""刀の画面の演出の絵（居合の白い斬撃の線・吸血の赤いにじみ）と、それを文字として登録するフォントを作る。

どちらも 512×256 の透明な絵。サーバーが、タイトルの文字（\\uE000 と \\uE001）として一瞬だけ画面に重ねる。
画面の大きさはさまざまなので、絵は画面の中央に寄せ、縁は大きめにとってある（画面からはみ出した分は、見えなくなる）。

  python3 tools/make_blade_screens.py            絵とフォントを書き出す
  python3 tools/make_blade_screens.py --preview  暗い背景に重ねた見本を作る（build/blades/screens.png）
"""
import argparse
import json
import math
from PIL import Image, ImageDraw, ImageFilter
from artwork import PACK, BUILD

W, H = 512, 256
# （名前, 文字）。文字は、サーバー（BladeEffects）と同じ
SCREENS = [('blade_slash', ''), ('blade_drain', '')]
# 絵の高さ（画面上の大きさの目安）と、基準線の位置。タイトルは画面中央に出るので、絵の中心が画面の中心に来るようにする
HEIGHT, ASCENT = 144, 78


def slash():
    """白い斬撃の線。右上から左下へ、細く尖った3本。"""
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for offset, width, alpha in ((0, 9, 255), (-34, 5, 190), (30, 4, 150)):
        x0, y0, x1, y1 = W * 0.80 + offset, H * 0.06, W * 0.20 + offset, H * 0.94
        steps = 120
        for i in range(steps):
            t = i / steps
            # 中ほどが太く、両端が尖る
            w = width * math.sin(math.pi * t) ** 0.8
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            draw.ellipse((x - w / 2, y - w / 2, x + w / 2, y + w / 2), fill=(255, 255, 255, alpha))
    glow = layer.filter(ImageFilter.GaussianBlur(5))
    glow = Image.merge('RGBA', (*glow.split()[:3], glow.split()[3].point(lambda a: int(a * 0.55))))
    return Image.alpha_composite(glow, layer)


def drain():
    """赤いにじみ。中央は透明で、縁へ向かって濃くなる。"""
    layer = Image.new('RGBA', (W, H))
    px = layer.load()
    for y in range(H):
        for x in range(W):
            dx, dy = (x - W / 2) / (W / 2), (y - H / 2) / (H / 2)
            d = min(1.0, math.hypot(dx * 0.85, dy))
            a = max(0.0, (d - 0.45) / 0.55) ** 1.6
            px[x, y] = (150, 10, 30, int(170 * a))
    return layer


def font():
    return {'providers': [{'type': 'bitmap', 'file': 'hnmt:font/%s.png' % name, 'ascent': ASCENT, 'height': HEIGHT, 'chars': [char]}
                          for name, char in SCREENS]}


def build():
    target = PACK / 'assets/hnmt/textures/font'
    target.mkdir(parents=True, exist_ok=True)
    slash().save(target / 'blade_slash.png')
    drain().save(target / 'blade_drain.png')
    path = PACK / 'assets/hnmt/font/blade.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(font(), ensure_ascii=False, indent=2) + '\n')
    print('Wrote %d screen images' % len(SCREENS))


def preview():
    BUILD.mkdir(parents=True, exist_ok=True)
    sheet = Image.new('RGBA', (W * 2 + 24, H + 16), (58, 66, 80, 255))
    for i, image in enumerate((slash(), drain())):
        sheet.alpha_composite(image, (8 + i * (W + 8), 8))
    out = BUILD / 'blades'
    out.mkdir(parents=True, exist_ok=True)
    sheet.save(out / 'screens.png')
    print('Preview: ' + str(out / 'screens.png'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview', action='store_true')
    args = parser.parse_args()
    preview() if args.preview else build()


if __name__ == '__main__': main()
