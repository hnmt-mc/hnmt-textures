#!/usr/bin/env python3
"""餌4種の 16x16 テクスチャと見本画像を作る。

使い方:  python3 resourcepack/tools/make_baits.py
出力:    resourcepack/assets/hnmt/textures/item/bait/<ID>.png
         resourcepack-build/baits_contact_sheet.png
見た目は、やわらかい色と丸い形のかわいい絵にしてある（目や内臓は描かない。ミミズは桃色、エビは火が通った色、イカは刺身のような白）。
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEX_DIR = os.path.join(ROOT, "resourcepack", "assets", "hnmt", "textures", "item", "bait")
BUILD_DIR = os.path.join(ROOT, "resourcepack-build")
N = 16
OUTLINE = (58, 46, 44)


def light(c, f=0.35):
    return tuple(int(v + (255 - v) * f) for v in c)


def dark(c, f=0.78):
    return tuple(int(v * f) for v in c)


class Canvas:
    def __init__(self):
        self.px = {}

    def put(self, x, y, c):
        if 0 <= x < N and 0 <= y < N:
            self.px[(x, y)] = c

    def ellipse(self, cx, cy, rx, ry, c):
        for y in range(N):
            for x in range(N):
                if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1:
                    self.put(x, y, c)

    def stroke(self, pts, c, w=2.0):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            steps = max(abs(x1 - x0), abs(y1 - y0)) * 4 + 1
            for i in range(int(steps) + 1):
                t = i / steps
                cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                for y in range(N):
                    for x in range(N):
                        if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= (w / 2) ** 2:
                            self.put(x, y, c)

    def outline(self):
        edge = []
        for y in range(N):
            for x in range(N):
                if (x, y) in self.px:
                    continue
                if any((x + dx, y + dy) in self.px for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    edge.append((x, y))
        for p in edge:
            self.px[p] = OUTLINE

    def shade_top(self, f=0.3):
        """各列のいちばん上の色を明るく、いちばん下を暗くする（簡単な陰影）。輪郭は触らない。"""
        for x in range(N):
            ys = [y for y in range(N) if (x, y) in self.px and self.px[(x, y)] != OUTLINE]
            if len(ys) >= 3:
                self.px[(x, ys[0])] = light(self.px[(x, ys[0])], f)
                self.px[(x, ys[-1])] = dark(self.px[(x, ys[-1])])

    def image(self):
        img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
        for (x, y), c in self.px.items():
            img.putpixel((x, y), c + (255,))
        return img


def leaf(cv, cx, cy, rx, ry):
    green = (112, 176, 92)
    cv.ellipse(cx, cy, rx, ry, green)
    for x in range(int(cx - rx + 1), int(cx + rx)):
        cv.put(x, int(cy), dark(green, 0.82))   # 葉脈


def mimizu():
    cv = Canvas()
    leaf(cv, 8, 12.5, 6.5, 2.5)
    cv.outline()   # 葉の輪郭（ミミズを描く前に付けて、ミミズを葉から浮かせる）
    worm = Canvas()
    pink = (240, 162, 176)
    worm.stroke([(2.5, 8), (4, 5), (6.5, 8), (8.5, 4.5), (11, 7.5), (13, 5)], pink, 1.7)
    worm.shade_top(0.4)
    # 体の節（薄い筋）
    edge = []
    for y in range(N):
        for x in range(N):
            if (x, y) not in worm.px and any((x + dx, y + dy) in worm.px for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                edge.append((x, y))
    for p in edge:
        worm.px[p] = (176, 100, 120)
    cv.px.update(worm.px)
    return cv.image()


def ebi():
    cv = Canvas()
    body = (250, 150, 108)
    pts = [(4.5, 9.5), (5, 6.5), (8, 5), (10.8, 6.5), (11.3, 9.5)]
    for k in range(len(pts) - 1):
        cv.stroke([pts[k], pts[k + 1]], body if k % 2 == 0 else light(body, 0.35), 3.6)
    cv.stroke([(11.3, 10), (12.6, 12.8)], (240, 108, 88), 2.2)   # 尾びれ
    cv.stroke([(9.8, 10.5), (10.2, 13)], (240, 108, 88), 1.6)
    cv.stroke([(4.5, 10.5), (3.2, 12.5)], (250, 190, 150), 1.0)   # ひげ
    cv.put(6, 4, (250, 190, 150)); cv.put(7, 3, (250, 190, 150))   # 頭の角
    cv.outline()
    return cv.image()


def iwashi():
    cv = Canvas()
    silver = (206, 216, 226)
    blue = (74, 118, 170)
    cv.ellipse(8.5, 8.5, 5.8, 3.0, silver)
    for x in range(N):
        for y in range(N):
            if cv.px.get((x, y)) == silver and y <= 7:
                cv.px[(x, y)] = blue if y <= 6 else light(blue, 0.35)
    # 尾びれ
    for (x, y) in [(2, 8), (2, 9), (1, 7), (1, 10), (2, 7), (2, 10)]:
        cv.put(x, y, dark(silver, 0.85))
    cv.put(11, 8, (30, 36, 48))   # 目
    cv.put(8, 10, light(silver, 0.5)); cv.put(7, 10, light(silver, 0.5))
    cv.outline()
    return cv.image()


def ika():
    cv = Canvas()
    leaf(cv, 8.5, 11.5, 6.5, 3.2)
    white = (252, 240, 236)
    edge = (238, 196, 200)
    for i, (x0, y0) in enumerate([(3, 4), (4, 7)]):
        for y in range(y0, y0 + 3):
            for x in range(x0, x0 + 9):
                cv.put(x, y, white)
        for x in range(x0, x0 + 9):
            cv.put(x, y0 + 2, edge)
        cv.put(x0, y0, edge); cv.put(x0 + 8, y0, edge)
    cv.outline()
    return cv.image()


BAITS = [("mimizu", "ミミズ", mimizu), ("ebi", "エビ", ebi), ("iwashi", "イワシ", iwashi), ("ika_no_mi", "イカの切り身", ika)]


def main():
    os.makedirs(TEX_DIR, exist_ok=True)
    os.makedirs(BUILD_DIR, exist_ok=True)
    scale, pad = 14, 14
    sheet = Image.new("RGB", (4 * (N * scale + pad) + pad, N * scale + 60), (92, 100, 112))
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc", 18)
    except OSError:
        font = ImageFont.load_default()
    for i, (bid, name, make) in enumerate(BAITS):
        img = make()
        img.save(os.path.join(TEX_DIR, bid + ".png"))
        big = img.resize((N * scale, N * scale), Image.NEAREST)
        x = pad + i * (N * scale + pad)
        sheet.paste(big, (x, pad), big)
        d.text((x, pad + N * scale + 8), f"{name}  {bid}", font=font, fill=(240, 240, 240))
    sheet.save(os.path.join(BUILD_DIR, "baits_contact_sheet.png"))


if __name__ == "__main__":
    main()
