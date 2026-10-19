#!/usr/bin/env python3
"""魚12種の32x32の編集元（art/fish.json）を、座標と配色の指定から作る。

スロットの中で小さく見えても魚と分かるよう、体を大きく取り、目・ひれ・模様を大きくはっきり描く。
使い方: python3 resourcepack/tools/make_fish_art.py && python3 resourcepack/tools/make_textures.py
"""

import json
import math
from PIL import Image, ImageDraw
from artwork import PACK

N = 32
OUTLINE = (58, 62, 84)
EYE_W = (255, 255, 255)
EYE_B = (24, 26, 40)


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


class Canvas:
    def __init__(self):
        self.px = {}  # (x, y) -> color

    def set(self, x, y, c):
        if -8 <= x < 48 and 0 <= y < N:
            self.px[(x, y)] = c

    def has(self, x, y):
        return (x, y) in self.px

    def poly(self, pts, c):
        im = Image.new("L", (56, N), 0)
        ImageDraw.Draw(im).polygon([(x + 8, y) for x, y in pts], fill=255)
        for y in range(N):
            for x in range(-8, 48):
                x, x_img = x, x + 8
                if im.getpixel((x_img, y)):
                    self.set(x, y, c)
        return
    def eye(self, x, y, big=True):
        """白目の3x3に、黒い2x2の瞳。小さくても目と分かる。"""
        if big:
            for dy in range(3):
                for dx in range(3):
                    self.set(x + dx, y + dy, EYE_W)
            for dy in (1, 2):
                for dx in (0, 1):
                    self.set(x + dx, y + dy, EYE_B)
        else:
            for dy in range(2):
                for dx in range(2):
                    self.set(x + dx, y + dy, EYE_B)
            self.set(x, y, EYE_W)

    def outline(self):
        out = {}
        for (x, y) in self.px:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                p = (x + dx, y + dy)
                if p not in self.px and -8 <= p[0] < 48 and 0 <= p[1] < N:
                    out[p] = OUTLINE
        self.px.update(out)

    def fit(self):
        """横幅が32以内なら、中央に寄せる。超えるときは、設計の見直しが要るので止める。"""
        xs = [x for x, _ in self.px]
        width = max(xs) - min(xs) + 1
        if width > N:
            raise ValueError(f"幅が{width}で、32を超えている")
        shift = (N - width) // 2 - min(xs)
        self.px = {(x + shift, y): c for (x, y), c in self.px.items()}
        return width

    def rows(self):
        self.fit()
        colors = sorted(set(self.px.values()))
        codes = "123456789ABCDEFGHIJKLMNOPQRSTUV"
        palette = {codes[i]: "#%02x%02x%02x" % c for i, c in enumerate(colors)}
        index = {c: codes[i] for i, c in enumerate(colors)}
        rows = ["".join(index[self.px[(x, y)]] if (x, y) in self.px else "." for x in range(N)) for y in range(N)]
        return {"palette": palette, "rows": rows}


def body(cv, x0, x1, cy, half, colors, shape=lambda t: math.sin(math.pi * t) ** 0.7, band=(-0.35, 0.4), back_fn=None):
    """x0〜x1 の紡錘形の胴。half は最大の半分の高さ。colors=(背, 中, 腹, 腹の明るい線)。"""
    back, mid, belly, light = colors
    for x in range(x0, x1 + 1):
        t = (x - x0 + 0.5) / (x1 - x0 + 1)
        h = max(1.0, half * shape(t))
        top, bot = cy - h, cy + h
        for y in range(int(math.floor(top)), int(math.ceil(bot)) + 1):
            if y < top - 0.0 or y > bot - 0.0:
                if not (top - 0.5 <= y + 0.5 <= bot + 0.5):
                    continue
            v = (y + 0.5 - cy) / h if h else 0
            if abs(v) > 1.15:
                continue
            c = back if v < band[0] else belly if v > band[1] else mid
            if v > band[1] + 0.35:
                c = light
            cv.set(x, y, c)


def tail_fork(cv, x, cy, spread, length, c, c2=None):
    """二股の尾。x から右へ length、上下に spread。"""
    cv.poly([(x, cy - 1), (x + length, cy - spread), (x + length - 2, cy), (x + length, cy + spread), (x, cy + 1)], c)
    if c2:
        cv.poly([(x, cy - 1), (x + length - 2, cy - spread + 2), (x + length - 3, cy), (x, cy)], c2)


def spots(cv, pts, c):
    for p in pts:
        cv.set(*p, c)


def tai():
    cv = Canvas()
    red, pink, belly, light = rgb("#e4474f"), rgb("#f08a85"), rgb("#f7cfc4"), rgb("#fdeee4")
    fin = rgb("#c9323d")
    tail_fork(cv, 23, 15, 7, 7, fin, rgb("#e4474f"))
    cv.poly([(8, 7), (11, 2), (20, 2), (23, 9)], fin)  # 背びれ
    cv.poly([(10, 21), (14, 27), (17, 21)], fin)  # 腹びれ
    body(cv, 2, 24, 15, 8, (red, pink, belly, light), shape=lambda t: (math.sin(math.pi * t) ** 0.55) * (1 - 0.35 * max(0, t - 0.6)))
    spots(cv, [(10, 8), (13, 7), (16, 8), (19, 9), (12, 10)], rgb("#4fb3e8"))  # 青い斑点
    cv.poly([(12, 14), (17, 17), (13, 19)], fin)  # 胸びれ
    cv.eye(4, 10)
    cv.outline()
    return cv


def maguro():
    cv = Canvas()
    navy, steel, silver, light = rgb("#1f3f8a"), rgb("#5f84b8"), rgb("#dfe8f4"), rgb("#ffffff")
    dark = rgb("#17306b")
    yellow = rgb("#f2d03d")
    tail_fork(cv, 24, 15, 9, 6, dark, navy)
    cv.poly([(8, 8), (13, 1), (17, 2), (17, 8)], dark)  # 背びれ
    spots(cv, [(x, 10 + (x % 2)) for x in range(19, 24, 1)], yellow)
    body(cv, 1, 24, 15, 8, (navy, steel, silver, light), shape=lambda t: math.sin(math.pi * min(1, t ** 0.85)) ** 0.6 if t < 0.97 else 0.4)
    cv.poly([(10, 17), (16, 22), (13, 18)], dark)  # 胸びれ
    cv.set(24, 14, yellow); cv.set(23, 12, yellow); cv.set(23, 18, yellow); cv.set(24, 17, yellow)  # 小離鰭
    cv.eye(3, 11)
    cv.outline()
    return cv


def salmon():
    cv = Canvas()
    blue, silver, belly, light = rgb("#4f86a8"), rgb("#b4cfdc"), rgb("#f1c3b0"), rgb("#fbe3d6")
    fin = rgb("#e7936a")
    tail_fork(cv, 24, 15, 6, 6, fin, rgb("#f2b48e"))
    cv.poly([(11, 8), (14, 4), (19, 8)], rgb("#7aa5bf"))  # 背びれ
    cv.poly([(21, 8), (23, 6), (24, 9)], fin)  # 脂びれ
    body(cv, 2, 24, 15, 6.5, (blue, silver, belly, light), shape=lambda t: math.sin(math.pi * t) ** 0.6)
    spots(cv, [(9, 11), (12, 10), (15, 11), (18, 10), (20, 12), (11, 13), (16, 13)], rgb("#25364f"))
    cv.poly([(9, 18), (12, 22), (13, 18)], fin)  # 腹びれ
    cv.eye(4, 11)
    cv.outline()
    return cv


def saba():
    cv = Canvas()
    teal, silver, belly, light = rgb("#2a7f95"), rgb("#9cc3cf"), rgb("#f0f5f7"), rgb("#ffffff")
    fin = rgb("#6aa3b5")
    tail_fork(cv, 24, 15, 5, 6, fin, rgb("#2a7f95"))
    cv.poly([(8, 11), (10, 7), (14, 11)], fin)
    cv.poly([(17, 11), (19, 8), (22, 11)], fin)
    body(cv, 1, 24, 15, 5, (teal, silver, belly, light), band=(-0.2, 0.5), shape=lambda t: math.sin(math.pi * t) ** 0.55)
    dark = rgb("#16384a")
    for x in range(7, 24):  # 背の波模様
        cv.set(x, 11 + (x // 2) % 2, dark)
        if x % 3 == 0:
            cv.set(x, 13, dark)
    cv.poly([(8, 17), (11, 20), (12, 17)], fin)
    cv.eye(3, 12)
    cv.outline()
    return cv


def yellowtail(half, cy, back, mid, belly, light, band_c, bright=True, fin=None):
    cv = Canvas()
    fin = fin or rgb("#c9b35a")
    tail_fork(cv, 24, cy, 7, 6, fin, band_c)
    cv.poly([(9, cy - half), (12, cy - half - 4), (19, cy - half - 4), (21, cy - half + 1)], fin)
    body(cv, 1, 24, cy, half, (back, mid, belly, light), band=(-0.3, 0.45), shape=lambda t: math.sin(math.pi * t) ** 0.6)
    for x in range(4, 25):  # 黄色い帯
        t = (x - 1) / 24
        y = int(cy - 1 + 1.0 * t)
        cv.set(x, y, band_c)
        cv.set(x, y + 1, band_c)
        if bright:
            cv.set(x, y + 2, band_c)
    cv.poly([(10, cy + 3), (13, cy + 7), (14, cy + 3)], fin)
    return cv


def hamachi():
    cv = yellowtail(6, 15, rgb("#3f8c9c"), rgb("#a9d0d3"), rgb("#f3f7f5"), rgb("#ffffff"), rgb("#f4cf45"), bright=False)
    cv.eye(3, 11)
    cv.outline()
    return cv


def buri():
    cv = yellowtail(8, 15, rgb("#23586e"), rgb("#9cc3c6"), rgb("#eef3f1"), rgb("#ffffff"), rgb("#f1c232"))
    cv.eye(3, 10)
    cv.outline()
    return cv


def kanpachi():
    cv = yellowtail(7, 15, rgb("#6d8a3f"), rgb("#bccd94"), rgb("#f4f1d8"), rgb("#fffbea"), rgb("#f2c53b"), fin=rgb("#d9b447"))
    dark = rgb("#3d4f1f")
    for i in range(7):  # 目を通る斜めの黒い帯（「間八」）
        cv.set(7 - i // 2 + 1, 6 + i, dark)
        cv.set(8 - i // 2 + 1, 6 + i, dark)
    cv.eye(3, 10)
    cv.outline()
    return cv


def kohada():
    cv = Canvas()
    blue, silver, belly, light = rgb("#4d86a8"), rgb("#c4d6e2"), rgb("#f2f5f7"), rgb("#ffffff")
    fin = rgb("#9fbfd0")
    tail_fork(cv, 24, 15, 5, 6, fin, rgb("#6fa0ba"))
    cv.poly([(11, 10), (14, 6), (17, 10)], fin)
    body(cv, 3, 24, 15, 5, (blue, silver, belly, light), band=(-0.3, 0.45), shape=lambda t: math.sin(math.pi * t) ** 0.6)
    spots(cv, [(9, 14), (12, 14), (15, 14), (18, 14), (21, 14)], rgb("#2b445e"))  # 銀の体の斑点
    cv.set(8, 12, rgb("#2b445e")); cv.set(8, 13, rgb("#2b445e"))
    cv.eye(5, 11, big=False)
    cv.outline()
    return cv


def konoshiro():
    cv = Canvas()
    blue, silver, belly, light = rgb("#4d82a0"), rgb("#bfd3dc"), rgb("#eef2f3"), rgb("#ffffff")
    fin = rgb("#8fb2c2")
    tail_fork(cv, 24, 14, 6, 7, fin, rgb("#6c9bb2"))
    cv.poly([(9, 7), (11, 2), (12, 2), (13, 7), (18, 7)], fin)  # 背びれと長い糸
    body(cv, 2, 24, 14, 7.5, (blue, silver, belly, light), band=(-0.3, 0.5), shape=lambda t: math.sin(math.pi * t) ** 0.55)
    dark = rgb("#27405a")
    for x in range(9, 22, 3):
        for y in (12, 15):
            cv.set(x, y, dark)
    cv.set(8, 12, dark); cv.set(8, 13, dark)
    cv.poly([(9, 19), (12, 23), (13, 19)], fin)
    cv.eye(4, 10)
    cv.outline()
    return cv


def hirame():
    cv = Canvas()
    sand, dark, edge = rgb("#c9a56f"), rgb("#8a6a3d"), rgb("#e6c88f")
    cx, cy = 16, 16
    for y in range(N):
        for x in range(N):
            dx, dy = (x + 0.5 - cx) / 12.5, (y + 0.5 - cy) / 10
            d = abs(dx) ** 1.7 + abs(dy) ** 1.7
            if d <= 1.0:
                c = sand if d < 0.72 else edge
                cv.set(x, y, c)
    for p in [(12, 14), (15, 12), (18, 15), (14, 18), (20, 12), (17, 19), (11, 17), (22, 16), (19, 9), (15, 22)]:
        cv.set(*p, dark)
        cv.set(p[0] + 1, p[1], dark)
    cv.poly([(27, 14), (31, 12), (30, 16), (31, 20), (27, 18)], edge)  # 尾
    cv.eye(6, 10)
    cv.eye(6, 15)
    cv.outline()
    return cv


def unagi():
    cv = Canvas()
    back, mid, belly = rgb("#2f4766"), rgb("#6d7f8f"), rgb("#f1dfa8")
    fin = rgb("#3f5878")
    for x in range(2, 31):
        t = (x - 2) / 28
        cy = 15 + 6.5 * math.sin(t * 2 * math.pi + 0.3) * (0.5 + 0.5 * t)
        th = 2.2 + 2.4 * math.sin(math.pi * min(1, t * 1.15)) ** 0.5
        if t > 0.85:
            th = max(1.0, th - (t - 0.85) * 10)
        for y in range(N):
            v = (y + 0.5 - cy) / th
            if abs(v) <= 1:
                cv.set(x, y, back if v < -0.15 else mid if v < 0.5 else belly)
    for x in range(6, 28):  # 背びれ
        t = (x - 2) / 28
        cy = 15 + 6.5 * math.sin(t * 2 * math.pi + 0.3) * (0.5 + 0.5 * t)
        yy = int(cy - 3.6 - 2.0 * math.sin(math.pi * t))
        if (x, yy) not in cv.px:
            cv.set(x, yy, fin)
    cv.eye(3, 11 + 0, big=False)
    cv.outline()
    return cv


def line(cv, p0, p1, colors):
    """1ピクセルの線（colors は、先へ向かう色の並び）。"""
    (x0, y0), (x1, y1) = p0, p1
    steps = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(steps + 1):
        t = i / steps
        cv.set(round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t), colors[min(len(colors) - 1, int(t * len(colors)))])


def ika():
    """上から見たイカ。左に頭と腕、右に菱形のひれのついた胴。"""
    cv = Canvas()
    pearl, pink, deep, light = rgb("#fbf0f7"), rgb("#efc5df"), rgb("#cf90c0"), rgb("#ffffff")
    red = rgb("#c2547a")
    cy = 16
    cv.poly([(19, cy), (24, 7), (29, cy), (24, 25)], pink)  # 菱形のひれ
    cv.poly([(20, cy), (24, 9), (27, cy)], pearl)
    cv.poly([(20, cy), (24, 23), (27, cy)], deep)
    for x in range(10, 27):  # 胴（右へ細くなる）
        t = (x - 10) / 16
        h = max(1.0, 5.6 * (1 - t ** 1.7) ** 0.6)
        for y in range(N):
            v = (y + 0.5 - cy) / h
            if abs(v) <= 1:
                cv.set(x, y, pearl if v < -0.3 else pink if v < 0.45 else deep)
    for p in [(13, 13), (16, 14), (19, 13), (14, 19), (17, 18), (20, 19), (23, 16)]:
        cv.set(*p, red)
    for x in range(6, 11):  # 頭
        for y in range(cy - 4, cy + 4):
            cv.set(x, y, pink if y < cy else deep)
    # 腕（先へ開く3本の三角。間をあけて、1本ずつ見えるようにする）
    cv.poly([(8, cy - 4), (6, cy - 1), (1, cy - 9), (3, cy - 4)], pearl)
    cv.poly([(7, cy - 1), (7, cy + 2), (0, cy + 1), (0, cy - 1)], pink)
    cv.poly([(8, cy + 3), (6, cy), (1, cy + 8), (3, cy + 4)], deep)
    gold = rgb("#f2c53d")
    for ey in (cy - 4, cy + 1):  # 金色の縁取りの目（頭の両側）
        for dy in range(4):
            for dx in range(4):
                cv.set(6 + dx, ey + dy, gold)
        for dy in (1, 2):
            for dx in (1, 2):
                cv.set(6 + dx, ey + dy, EYE_B)
    cv.outline()
    return cv


FISH = [("unagi", unagi), ("salmon", salmon), ("kohada", kohada), ("konoshiro", konoshiro), ("tai", tai), ("hirame", hirame),
        ("saba", saba), ("hamachi", hamachi), ("buri", buri), ("ika", ika), ("kanpachi", kanpachi), ("maguro", maguro)]

if __name__ == "__main__":
    data = {name: fn().rows() for name, fn in FISH}
    (PACK / "art/fish.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("wrote", len(data), "fish")
