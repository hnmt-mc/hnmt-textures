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
    """スコープを覗いた画面。画面の中央に、スコープの筒の厚い黒い縁（円環）があり、中は透明なレンズ（細い十字線つき）。
    縁の下には、スコープを載せた銃の本体の影が、画面の下へ伸びる。縁の外も、透明（景色が見える）。
    サーバーが、頭の防具を一時的に、この絵のかぶり物（equippable の camera_overlay）に見せかけて、画面いっぱいに出す（16:9 に引き伸ばされる）。"""
    image = Image.new('RGBA', (SCOPE_W, SCOPE_H), (0, 0, 0, 0))
    cx, cy = SCOPE_W / 2, SCOPE_H * 0.43
    inner, outer = SCOPE_H * 0.27, SCOPE_H * 0.35
    px = image.load()
    # 銃の本体: 筒の下から、画面の下へ向かって、少し広がる暗い青灰色の影。左右の端は、金属のハイライト
    top_y = cy + outer - 12
    for y in range(int(top_y), SCOPE_H):
        f = (y - top_y) / (SCOPE_H - top_y)
        half = 62 + 58 * f
        for x in range(int(cx - half), int(cx + half) + 1):
            u = (x - cx) / half
            shade = 1.0 - 0.55 * abs(u) ** 2
            base = (34, 40, 58)
            lit = tuple(int(c * (0.55 + 0.8 * max(0.0, -u * 0.6 + 0.35))) for c in base)
            px[x, y] = (min(255, int(lit[0] * shade)), min(255, int(lit[1] * shade)), min(255, int(lit[2] * shade)), 255)
    # 筒の縁（円環）。外側は、ややぼかす
    for y in range(SCOPE_H):
        for x in range(SCOPE_W):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if inner - 6 <= d <= outer + 4:
                if d < inner: a = int(255 * (d - (inner - 6)) / 6)             # レンズの内側の縁（なめらかに黒へ）
                elif d <= outer: a = 255
                else: a = int(255 * (1 - (d - outer) / 4))                       # 外側の縁
                shade = 18 + int(26 * max(0.0, 1 - abs((d - (inner + outer) / 2)) / ((outer - inner) / 2)) ** 3 * (0.5 + 0.5 * math.cos(math.atan2(y - cy, x - cx) + 2.3)))
                r, g, b, old = px[x, y]
                px[x, y] = (shade, shade, shade + 4, max(a, old))
    layer = Image.new('RGBA', (SCOPE_W, SCOPE_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    r = inner - 4
    # 十字線: 細い線を、レンズいっぱいに。中央は、少しあける。小さな目盛り
    for sign in (-1, 1):
        draw.line((cx + sign * 14, cy, cx + sign * r, cy), fill=(10, 10, 12, 235), width=2)
        draw.line((cx, cy + sign * 14, cx, cy + sign * r), fill=(10, 10, 12, 235), width=2)
        for k in (1, 2, 3):
            draw.line((cx + sign * k * 34, cy - 4, cx + sign * k * 34, cy + 4), fill=(10, 10, 12, 235), width=2)
            draw.line((cx - 4, cy + sign * k * 34, cx + 4, cy + sign * k * 34), fill=(10, 10, 12, 235), width=2)
    draw.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), fill=(230, 40, 40, 255))
    # レンズの内側を、ほんの少し暗く（筒の中を覗いている感じ）
    for y in range(SCOPE_H):
        for x in range(SCOPE_W):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d < inner - 6:
                a = int(70 * max(0.0, (d / (inner - 6) - 0.55) / 0.45) ** 2)
                if a: layer.putpixel((x, y), (0, 0, 0, a)) if layer.getpixel((x, y))[3] == 0 else None
    image.alpha_composite(layer)
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
