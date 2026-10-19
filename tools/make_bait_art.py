#!/usr/bin/env python3
"""餌4種（ミミズ・エビ・イワシ・イカの切り身）の32x32の絵を、座標と配色の指定から作る。

魚・料理と同じく、枠いっぱいに大きく、1ピクセルの暗い輪郭で、種類が色と形で見分けられるようにする。
使い方: python3 tools/make_bait_art.py
"""

import math
from PIL import Image
from artwork import save, sheet
from make_fish_art import Canvas, rgb, body, tail_fork, spots
from make_food_art import ell, hline, vline, to_image, shiso, GREEN, GREEN_D, GREEN_L

C = rgb


def mimizu():
    cv = Canvas()
    base, belly, ring, band = C("#e07b72"), C("#f4ada0"), C("#b54f56"), C("#f7cdb8")
    pts = []
    for x in range(3, 29):
        t = (x - 3) / 25
        cy = 15.5 + 5.5 * math.sin(t * 2 * math.pi * 1.1)
        pts.append((x, cy))
        th = 3.0 if 0.05 < t < 0.95 else 1.8
        for y in range(32):
            v = (y + 0.5 - cy) / th
            if abs(v) <= 1:
                cv.set(x, y, base if v < 0.1 else belly)
    for i, (x, cy) in enumerate(pts):  # 体節の輪
        if i % 3 == 1 and 1 < i < 24:
            for y in range(32):
                if (x, y) in cv.px and abs(y + 0.5 - cy) <= 3.0:
                    cv.set(x, y, ring)
    for (x, cy) in pts[8:12]:  # 環帯
        for y in range(32):
            if (x, y) in cv.px:
                cv.set(x, y, band)
    cv.set(4, round(pts[1][1]) - 1, C("#fff0e6"))
    cv.outline()
    return to_image_noout(cv)


def to_image_noout(cv):
    im = Image.new("RGBA", (32, 32))
    for (x, y), c in cv.px.items():
        if 0 <= x < 32:
            im.putpixel((x, y), c + (255,))
    return im


def ebi():
    cv = Canvas()
    shell, belly, stripe, deep = C("#ff8a4d"), C("#ffc79c"), C("#d9502b"), C("#bf3f23")
    cx, cy, r = 15, 17, 8.5
    # 曲がった体（三日月）を、小さな円をならべて描く
    segs = []
    for i in range(13):
        a = math.radians(205 - i * 17)
        x, y = cx + r * math.cos(a), cy - r * math.sin(a)
        size = 3.6 - 0.12 * i
        segs.append((x, y, size))
    for i, (x, y, size) in enumerate(segs):
        ell(cv, x, y, size, size, stripe if i % 2 else shell)
    for (x, y, size) in segs:  # 腹側
        ell(cv, x - 0.5 * size * 0.3, y + size * 0.35, size * 0.55, size * 0.4, belly)
    for i, (x, y, size) in enumerate(segs):
        if i % 2 == 0:
            cv.set(round(x), round(y - size * 0.5), C("#ffe2c4"))
    # 尾びれ
    tx, ty = segs[-1][0], segs[-1][1]
    cv.poly([(tx - 1, ty), (tx + 4, ty + 6), (tx + 1, ty + 7), (tx - 3, ty + 4)], deep)
    # 頭・目・ひげ
    hx, hy = segs[0][0], segs[0][1]
    cv.eye(round(hx) - 1, round(hy) - 3, big=False)
    for k in range(5):
        cv.set(round(hx) - 3 - k, round(hy) - 3 - k // 2, C("#ffd0a8"))
        cv.set(round(hx) - 2 - k, round(hy) - 1 - k // 2, C("#ffd0a8"))
    cv.outline()
    return to_image_noout(cv)


def iwashi():
    cv = Canvas()
    blue, silver, belly, light = C("#2e6f9e"), C("#c8dde8"), C("#f4f8fa"), C("#ffffff")
    fin = C("#7fb0cc")
    tail_fork(cv, 23, 15, 6, 6, fin, C("#4f86a8"))
    cv.poly([(10, 10), (12, 6), (16, 10)], fin)
    body(cv, 1, 24, 15, 6, (blue, silver, belly, light), band=(-0.2, 0.5), shape=lambda t: math.sin(math.pi * t) ** 0.55)
    spots(cv, [(8, 14), (11, 14), (14, 14), (17, 14)], C("#1f3f66"))  # 体側の黒い点
    cv.poly([(9, 19), (12, 22), (13, 19)], fin)
    cv.eye(3, 11)
    cv.outline()
    return to_image_noout(cv)


def ika_no_mi():
    cv = Canvas()
    shiso(cv, 1, 19)
    shiso(cv, 21, 21)
    ell(cv, 16, 24, 15, 5.5, GREEN)
    ell(cv, 16, 24, 12.5, 3.5, GREEN_L)
    base, hatch, edge = C("#fbeef5"), C("#e6a9cb"), C("#c597b6")
    for ox, oy in ((2, 12), (9, 5)):  # 2枚の切り身
        cv.poly([(ox, oy + 2), (ox + 4, oy), (ox + 19, oy), (ox + 21, oy + 4), (ox + 17, oy + 9), (ox + 2, oy + 9)], edge)
        cv.poly([(ox + 1, oy + 2), (ox + 4, oy + 1), (ox + 18, oy + 1), (ox + 19, oy + 4), (ox + 16, oy + 8), (ox + 3, oy + 8)], base)
        for k in range(0, 18, 4):  # 鹿の子切りの格子
            for j in range(6):
                cv.set(ox + 3 + k + j // 2, oy + 2 + j, hatch)
        hline(cv, ox + 3, ox + 16, oy + 1, C("#ffffff"))
    cv.outline()
    return to_image_noout(cv)


BAITS = [("mimizu", "ミミズ", mimizu), ("ebi", "エビ", ebi), ("iwashi", "イワシ", iwashi), ("ika_no_mi", "イカの切り身", ika_no_mi)]

if __name__ == "__main__":
    entries = []
    for name, label, fn in BAITS:
        im = fn()
        save(im, "bait", name)
        entries.append((im, label, name))
    sheet(entries, "baits_contact_sheet.png", columns=4)
