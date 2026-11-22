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
    """火縄銃の狙い方: 銃身の上の、小さな突起（照星と照門）を一直線にそろえて狙う。後ろから銃身を見た絵。
    下に、照門（手前の板。真ん中が U 字に切れている）、中央の先に、照星（銃口の小さな突起）があり、U 字の切れ込みの真ん中に、照星が来る。
    銃身は、手前から奥へ、細くなる。縁の外は、透明（景色が見える）。サーバーが、頭の防具を一時的に、この絵のかぶり物
    （equippable の camera_overlay）に見せかけて、画面いっぱいに出す（16:9 に引き伸ばされる）。"""
    image = Image.new('RGBA', (SCOPE_W, SCOPE_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    cx = SCOPE_W / 2
    apex_y, near_y = 300, SCOPE_H
    apex_w, near_w = 16, 380
    def half_at(y): return (apex_w + (near_w - apex_w) * ((y - apex_y) / (near_y - apex_y)) ** 1.35) / 2
    px = image.load()
    # 銃身: 上面は、八角の面（中央が明るく、左右へ暗くなる）。奥へ向かって、細くなる
    for y in range(apex_y, near_y):
        half = half_at(y)
        depth = (y - apex_y) / (near_y - apex_y)
        for x in range(int(cx - half), int(cx + half) + 1):
            u = (x - cx) / half
            facet = 0.0 if abs(u) < 0.33 else 1.0 if abs(u) < 0.72 else 2.0     # 3つの面
            base = (146, 158, 178) if facet == 0 else (96, 108, 128) if facet == 1 else (52, 60, 76)
            haze = 0.55 + 0.45 * depth                                          # 奥ほど、少し霞む
            px[x, y] = (int(base[0] * haze), int(base[1] * haze), int(base[2] * haze), 255)
    for u in (-0.33, 0.33, -0.72, 0.72):                                        # 面の境目の細い線
        points = [(cx + half_at(y) * u, y) for y in range(apex_y, near_y, 4)]
        draw.line(points, fill=(24, 28, 38, 200), width=2)
    for y0, thick in ((350, 4), (420, 6), (520, 9)):                            # 真鍮の帯（竹の節のように巻く）
        half = half_at(y0) + 2
        draw.rectangle((cx - half, y0, cx + half, y0 + thick), fill=(201, 160, 60, 255))
        draw.line((cx - half, y0, cx + half, y0), fill=(240, 210, 122, 255), width=1)
    # 照星: 銃口の、小さな突起（台と、先の玉）
    draw.rectangle((cx - 9, apex_y - 12, cx + 9, apex_y + 2), fill=(201, 160, 60, 255))                 # 台
    draw.rectangle((cx - 3, apex_y - 34, cx + 3, apex_y - 10), fill=(28, 32, 42, 255))                  # 柱
    draw.ellipse((cx - 6, apex_y - 44, cx + 6, apex_y - 32), fill=(240, 210, 122, 255), outline=(40, 30, 10, 255))   # 先の玉
    # 照門: 手前の板。真ん中が U 字に切れて、そこから照星と銃身が見える
    top, notch_w, notch_bottom = 480, 56, 536
    gate = Image.new('RGBA', (SCOPE_W, SCOPE_H), (0, 0, 0, 0))
    g = ImageDraw.Draw(gate)
    g.rectangle((cx - 230, top, cx + 230, SCOPE_H), fill=(26, 30, 38, 255))
    g.rectangle((cx - 230, top, cx + 230, top + 5), fill=(88, 98, 118, 255))                           # 上の縁のハイライト
    g.rectangle((cx - 230, top + 5, cx - 226, SCOPE_H), fill=(60, 68, 84, 255))
    g.rectangle((cx + 226, top + 5, cx + 230, SCOPE_H), fill=(12, 14, 18, 255))
    for x in range(int(cx - 230), int(cx + 231), 14):                                                  # 側面の削り跡
        g.line((x, top + 14, x, SCOPE_H), fill=(32, 36, 46, 255), width=1)
    notch = Image.new('L', (SCOPE_W, SCOPE_H), 0)
    n = ImageDraw.Draw(notch)
    n.rectangle((cx - notch_w / 2, top - 2, cx + notch_w / 2, notch_bottom - notch_w / 2), fill=255)
    n.ellipse((cx - notch_w / 2, notch_bottom - notch_w, cx + notch_w / 2, notch_bottom), fill=255)       # U 字の底
    a = gate.split()[3]
    a.paste(0, mask=notch)                                                                              # U 字の切れ込みを、透明に抜く
    gate.putalpha(a)
    # 切れ込みの縁の、細い明るい線
    ring = ImageDraw.Draw(gate)
    ring.line((cx - notch_w / 2, top, cx - notch_w / 2, notch_bottom - notch_w / 2), fill=(120, 132, 154, 255), width=2)
    ring.line((cx + notch_w / 2, top, cx + notch_w / 2, notch_bottom - notch_w / 2), fill=(70, 78, 96, 255), width=2)
    ring.arc((cx - notch_w / 2, notch_bottom - notch_w, cx + notch_w / 2, notch_bottom), 0, 180, fill=(120, 132, 154, 255), width=2)
    image.alpha_composite(gate)
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
