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
import random
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


def _poly_mask(points):
    mask = Image.new('L', (SCOPE_W, SCOPE_H), 0)
    ImageDraw.Draw(mask).polygon(points, fill=255)
    return mask


def _fill(image, points, shader):
    """多角形の中を、shader(x, y) の色で塗る（ドット単位）。"""
    mask = _poly_mask(points)
    box = mask.getbbox()
    if not box: return
    px, mp = image.load(), mask.load()
    for y in range(box[1], box[3]):
        for x in range(box[0], box[2]):
            if mp[x, y]: px[x, y] = shader(x, y) + (255,)


def scope_view():
    """火縄銃の狙い方（実物の姿に寄せる）: 銃を構えて、銃身の上の、照星と照門を一直線にそろえて狙う。目の高さから見た絵。
    下に、銃床の上面（木目）と、手前の照門（U 字の切れ込み）。中央に、八角の銃身（面ごとの光・真鍮の帯・遠くの霞）が奥へ細くなり、
    先に、照星（真鍮の台・鉄の柱・玉）。右の手前に、真鍮の側板・火皿・蛇杖と、火縄の先の燃える火。縁の外は透明（景色が見える）。
    サーバーが、頭の防具の欄に、この絵のかぶり物（equippable の camera_overlay）を着けて、画面いっぱいに出す（16:9 に引き伸ばされる）。"""
    rng = random.Random(5)
    image = Image.new('RGBA', (SCOPE_W, SCOPE_H), (0, 0, 0, 0))
    cx, apex_y = SCOPE_W / 2, 300
    apex_w, near_w = 14, 360
    def half_at(y): return (apex_w + (near_w - apex_w) * ((y - apex_y) / (SCOPE_H - apex_y)) ** 1.3) / 2
    def depth_at(y): return max(0.0, min(1.0, (y - apex_y) / (SCOPE_H - apex_y)))
    def mixc(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

    # 1. 銃床の上面（手前の左右）: 木目が、奥の一点へ向かって集まる
    stock = [(cx - 190, 462), (cx + 190, 462), (cx + 470, SCOPE_H), (cx - 470, SCOPE_H)]
    def wood(x, y):
        u = (x - cx) / max(1.0, 190 + (y - 462) * (280 / (SCOPE_H - 462)))
        grain = math.sin((u * 70) + math.sin(y * 0.05) * 1.2) * 0.5 + rng.random() * 0.25
        base = mixc((74, 44, 24), (150, 96, 52), max(0.0, min(1.0, 0.45 + 0.35 * grain - 0.25 * abs(u))))
        return mixc(base, (28, 18, 10), min(1.0, abs(u) ** 3 * 0.6))
    _fill(image, stock, wood)

    # 2. 銃身の上面: 八角の面（中央が明るく、左右へ暗く）、奥へ向かって細く霞む
    barrel = []
    for y in range(apex_y, SCOPE_H, 6): barrel.append((cx - half_at(y), y))
    for y in range(SCOPE_H - 1, apex_y - 1, -6): barrel.append((cx + half_at(y), y))
    def steel(x, y):
        half = max(1.0, half_at(y)); u = (x - cx) / half; d = depth_at(y)
        facet = abs(u)
        if facet < 0.30: c = (162, 174, 194)
        elif facet < 0.52: c = (118, 130, 152)
        elif facet < 0.80: c = (82, 92, 112)
        else: c = (44, 52, 68)
        streak = 1.0 + 0.18 * math.exp(-((u + 0.12) ** 2) / 0.01) * (1 - d * 0.5)        # 細い光の筋
        c = tuple(min(255, int(v * streak)) for v in c)
        c = mixc(c, (150, 170, 200), (1 - d) * 0.38)                                    # 奥の霞
        speck = rng.random()
        if speck > 0.992: c = mixc(c, (150, 96, 60), 0.6)                               # 錆の点
        return c
    _fill(image, barrel, steel)
    draw = ImageDraw.Draw(image)
    for u in (-0.80, -0.52, -0.30, 0.30, 0.52, 0.80):                                    # 面の境目
        draw.line([(cx + half_at(y) * u, y) for y in range(apex_y, SCOPE_H, 4)], fill=(22, 26, 36, 190 if abs(u) > 0.7 else 120), width=2 if abs(u) > 0.7 else 1)
    for y0, thick in ((338, 3), (372, 4), (432, 6), (520, 10)):                          # 真鍮の帯（近いほど太く、大きい）
        half = half_at(y0) + 2
        for k in range(thick):
            t = k / max(1, thick - 1)
            draw.line((cx - half, y0 + k, cx + half, y0 + k), fill=mixc((240, 210, 122), (138, 106, 30), t) + (255,), width=1)
        draw.line((cx - half, y0 + thick, cx + half, y0 + thick), fill=(30, 24, 10, 150), width=1)   # 帯の下の影
    # 銃口の近く: 口金（銃身より少し太い）
    mouth_y = apex_y + 8
    draw.rectangle((cx - half_at(mouth_y) - 3, mouth_y - 2, cx + half_at(mouth_y) + 3, mouth_y + 3), fill=(201, 160, 60, 255))

    # 3. 右手前: 火縄の仕掛け（真鍮の側板・火皿・蛇杖・燃える火縄）
    plate = [(cx + 120, 440), (cx + 300, 470), (cx + 330, SCOPE_H), (cx + 110, SCOPE_H)]
    def brass(x, y):
        t = max(0.0, min(1.0, (x - (cx + 110)) / 230)); sh = 0.55 + 0.45 * (1 - t) * (1 - (y - 440) / 220 * 0.4)
        return tuple(int(c * sh) for c in mixc((236, 200, 100), (140, 104, 30), t))
    _fill(image, plate, brass)
    draw.line([(cx + 120, 440), (cx + 300, 470)], fill=(250, 226, 150, 255), width=2)         # 側板の上の縁
    for sx, sy in ((cx + 160, 520), (cx + 250, 530)): draw.ellipse((sx - 7, sy - 7, sx + 7, sy + 7), fill=(90, 66, 20, 255)); draw.ellipse((sx - 3, sy - 3, sx + 3, sy + 3), fill=(220, 190, 110, 255))
    pan = [(cx + 100, 414), (cx + 150, 410), (cx + 156, 436), (cx + 104, 442)]               # 火皿（蓋つき）
    _fill(image, pan, lambda x, y: mixc((226, 190, 90), (130, 96, 26), (y - 410) / 32))
    draw.line([pan[0], pan[1]], fill=(255, 232, 160, 255), width=2)
    arm = [(cx + 170, 520), (cx + 200, 420), (cx + 230, 380), (cx + 252, 360), (cx + 266, 352)]   # 蛇杖（S 字の鉄の腕）
    draw.line(arm, fill=(18, 20, 28, 255), width=11)
    draw.line([(x - 2, y - 1) for x, y in arm], fill=(70, 78, 96, 255), width=3)
    cord = [(cx + 266, 352), (cx + 284, 330), (cx + 288, 318)]                              # 火縄
    draw.line(cord, fill=(120, 114, 98, 255), width=5)
    glow = Image.new('RGBA', (SCOPE_W, SCOPE_H), (0, 0, 0, 0))
    gp = glow.load()
    gx, gy = cx + 288, 314
    for y in range(int(gy - 36), int(gy + 36)):
        for x in range(int(gx - 36), int(gx + 36)):
            d = math.hypot(x - gx, y - gy)
            if d < 36:
                a = int(210 * (1 - d / 36) ** 2)
                gp[x, y] = (255, int(140 - 60 * d / 36), 30, a)
    image.alpha_composite(glow)
    draw.ellipse((gx - 5, gy - 5, gx + 5, gy + 5), fill=(255, 238, 160, 255))              # 火縄の先の、赤熱した芯

    # 4. 照門（手前の板。真ん中が U 字に切れて、銃身と照星が見える）
    top, notch_w, notch_bottom = 478, 54, 534
    gate = Image.new('RGBA', (SCOPE_W, SCOPE_H), (0, 0, 0, 0))
    g = ImageDraw.Draw(gate)
    def blade(x, y):
        edge = min(abs(x - (cx - 215)), abs(x - (cx + 215)))
        t = max(0.0, 1 - edge / 30)
        base = mixc((20, 24, 32), (44, 50, 64), (y - top) / 100 * 0.5)
        return mixc(base, (84, 94, 114), t * 0.4)
    _fill(gate, [(cx - 215, top), (cx + 215, top), (cx + 224, SCOPE_H), (cx - 224, SCOPE_H)], blade)
    g.rectangle((cx - 215, top, cx + 215, top + 4), fill=(128, 140, 164, 255))                  # 上の縁のハイライト
    g.rectangle((cx - 215, top + 4, cx + 215, top + 7), fill=(10, 12, 18, 255))
    g.rectangle((cx - 215, SCOPE_H - 22, cx + 215, SCOPE_H - 15), fill=(201, 160, 60, 255))  # 下の真鍮の座
    notch = Image.new('L', (SCOPE_W, SCOPE_H), 0)
    n = ImageDraw.Draw(notch)
    n.rectangle((cx - notch_w / 2, top - 2, cx + notch_w / 2, notch_bottom - notch_w / 2), fill=255)
    n.ellipse((cx - notch_w / 2, notch_bottom - notch_w, cx + notch_w / 2, notch_bottom), fill=255)
    a = gate.split()[3]
    a.paste(0, mask=notch)
    gate.putalpha(a)
    ring = ImageDraw.Draw(gate)
    ring.line((cx - notch_w / 2, top, cx - notch_w / 2, notch_bottom - notch_w / 2), fill=(150, 162, 186, 255), width=2)
    ring.line((cx + notch_w / 2, top, cx + notch_w / 2, notch_bottom - notch_w / 2), fill=(64, 72, 90, 255), width=2)
    ring.arc((cx - notch_w / 2, notch_bottom - notch_w, cx + notch_w / 2, notch_bottom), 0, 180, fill=(150, 162, 186, 255), width=2)
    for x in range(int(cx - 205), int(cx + 206), 16):                                         # 側面の削り跡
        if abs(x - cx) > notch_w: ring.line((x, top + 14, x, SCOPE_H - 26), fill=(30, 34, 44, 255), width=1)
    image.alpha_composite(gate)

    # 5. 照星（真鍮の台・鉄の柱・玉）。切れ込みの真ん中に来る
    draw = ImageDraw.Draw(image)
    draw.rectangle((cx - 11, apex_y - 10, cx + 11, apex_y + 3), fill=(201, 160, 60, 255))
    draw.line((cx - 11, apex_y - 10, cx + 11, apex_y - 10), fill=(250, 226, 150, 255), width=2)
    draw.polygon([(cx - 4, apex_y - 10), (cx + 4, apex_y - 10), (cx + 2, apex_y - 36), (cx - 2, apex_y - 36)], fill=(26, 30, 40, 255))
    draw.line((cx - 3, apex_y - 10, cx - 1, apex_y - 36), fill=(96, 108, 130, 255), width=1)
    draw.ellipse((cx - 7, apex_y - 47, cx + 7, apex_y - 33), fill=(236, 200, 96, 255), outline=(60, 44, 12, 255))
    draw.ellipse((cx - 4, apex_y - 44, cx, apex_y - 40), fill=(255, 244, 190, 255))
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
