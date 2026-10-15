#!/usr/bin/env python3
"""釣竿7本の 16x16 テクスチャ（通常・投げた状態）と見本画像を作る。

使い方:  python3 resourcepack/tools/make_rods.py
出力:    resourcepack/assets/hnmt/textures/item/rod/<ID>.png と <ID>_cast.png
         resourcepack-build/rods_contact_sheet.png
バニラの釣竿（16x16、左下が握り・右上が先端）と同じ向きで、
通常の絵には釣り糸が垂れ、「投げた状態」の絵には糸が無い（糸は実体として描かれるため）。
"""
import glob
import math
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEX_DIR = os.path.join(ROOT, "resourcepack", "assets", "hnmt", "textures", "item", "rod")
BUILD_DIR = os.path.join(ROOT, "resourcepack-build")
N = 16


def dark(c, f=0.55):
    return tuple(int(v * f) for v in c)


def light(c, f=0.3):
    return tuple(int(v + (255 - v) * f) for v in c)


GOLD = (236, 190, 60)
SILVER = (196, 204, 212)
LINE = (232, 232, 232)

# start/end: 握りの下端と先端（行ごとに x を補間する）。w0/w1: 握り側と先端側の横幅。
# grip: 握りの行数。bands: 竿の途中の巻き（t は 0..1）。nodes: 竹の節。guides: ガイド（糸通し）の t。
# reel: (色, 大きさ) 握りの手前に付くリール。
RODS = {
    "bamboo": dict(  # 素朴な竹
        start=(2, 14), end=(12, 2), w0=2, w1=1, grip=3, grip_c=(112, 78, 40), body=(196, 164, 84),
        nodes=[0.35, 0.62, 0.84], node_c=(120, 140, 60), bands=[], guides=[0.9], reel=None,
    ),
    "keiryu_nami": dict(  # 細く長い竹
        start=(1, 14), end=(13, 2), w0=2, w1=1, grip=3, grip_c=(150, 110, 70), body=(214, 190, 112),
        nodes=[0.3, 0.5, 0.7, 0.88], node_c=(160, 130, 60), bands=[], guides=[0.45, 0.75, 0.95], reel=None,
    ),
    "keiryu_jo": dict(  # 漆塗りの細竿に金の巻き
        start=(1, 14), end=(13, 2), w0=2, w1=1, grip=4, grip_c=(190, 150, 100), body=(122, 56, 36),
        nodes=[], node_c=None, bands=[(0.30, GOLD), (0.55, GOLD), (0.78, GOLD)], guides=[0.45, 0.75, 0.95],
        reel=None,
    ),
    "iso_nami": dict(  # 少し太くしなやかな濃い緑
        start=(2, 14), end=(12, 2), w0=2, w1=1, grip=4, grip_c=(44, 44, 50), body=(70, 110, 74),
        nodes=[], node_c=None, bands=[(0.42, (30, 40, 34))], guides=[0.5, 0.75, 0.95], reel=None,
    ),
    "iso_jo": dict(  # 紺青の竿・金の巻き・小型リール
        start=(2, 14), end=(12, 2), w0=2, w1=1, grip=4, grip_c=(40, 40, 46), body=(36, 70, 128),
        nodes=[], node_c=None, bands=[(0.30, GOLD), (0.50, GOLD), (0.74, GOLD)], guides=[0.5, 0.75, 0.95],
        reel=(SILVER, 2),
    ),
    "fune_nami": dict(  # 短く太い頑丈な竿＋リール
        start=(3, 14), end=(11, 4), w0=3, w1=2, grip=4, grip_c=(40, 40, 44), body=(84, 88, 98),
        nodes=[], node_c=None, bands=[(0.40, (50, 52, 60))], guides=[0.7, 0.95], reel=((150, 154, 164), 3),
    ),
    "fune_jo": dict(  # 赤黒の竿＋金具が目立つ大型リール
        start=(3, 14), end=(11, 4), w0=3, w1=2, grip=4, grip_c=(32, 30, 34), body=(176, 44, 44),
        nodes=[], node_c=None, bands=[(0.30, GOLD), (0.52, GOLD), (0.74, GOLD)], guides=[0.7, 0.95],
        reel=(GOLD, 3), metal=GOLD,
    ),
}
ORDER = [("bamboo", "竹竿"), ("keiryu_nami", "渓流竿(並)"), ("keiryu_jo", "渓流竿(上)"),
         ("iso_nami", "磯竿(並)"), ("iso_jo", "磯竿(上)"), ("fune_nami", "船竿(並)"), ("fune_jo", "船竿(上)")]


def draw_rod(s, cast):
    px = {}
    sx, sy = s["start"]
    ex, ey = s["end"]
    rows = sy - ey
    for i in range(rows + 1):
        y = sy - i
        t = i / rows
        x = round(sx + (ex - sx) * t)
        w = max(1, round(s["w0"] + (s["w1"] - s["w0"]) * t))
        if i < s["grip"]:
            base = s["grip_c"]
        else:
            base = s["body"]
            for bt, bc in s["bands"]:
                if abs(t - bt) < 0.5 / rows + 0.02:
                    base = bc
            for nt in s["nodes"]:
                if abs(t - nt) < 0.5 / rows + 0.01:
                    base = s["node_c"]
        for k in range(w):
            c = base
            if w >= 2 and k == 0:
                c = light(base, 0.25)
            elif w >= 2 and k == w - 1:
                c = dark(base, 0.7)
            if i < s["grip"] and (x + k + y) % 2 == 0:
                c = dark(c, 0.8)  # 握りの網目
            px[(x + k, y)] = c
        if i == s["grip"] - 1 or i == s["grip"]:
            for k in range(w):
                px[(x + k, y)] = s.get("metal", SILVER) if i == s["grip"] else px[(x + k, y)]
        if any(abs(t - gt) < 0.5 / rows for gt in s["guides"]):
            px[(x - 1, y)] = light(s.get("metal", SILVER), 0.1)
    # リール（握りの手前＝右下）
    if s["reel"]:
        c, size = s["reel"]
        rx, ry = sx + s["w0"] + 2, sy - 3
        for dx in range(size):
            for dy in range(size):
                px[(rx + dx, ry + dy)] = c if (dx, dy) != (0, 0) else light(c, 0.4)
        px[(rx + size, ry)] = dark(c, 0.5)  # ハンドル
        px[(rx + size, ry - 1)] = dark(c, 0.5)
        for dy in range(size):
            px[(rx + size - 1, ry + dy)] = dark(c, 0.75)
    # 先端と釣り糸
    tip = (ex + s["w1"], ey - 1)
    px[tip] = SILVER
    if not cast:
        lx, ly = min(tip[0] + 1, 14), tip[1] + 1
        pts = [(lx, ly + k) for k in range(0, 8)]
        pts += [(lx - 1, ly + 8), (lx - 1, ly + 9), (lx - 2, ly + 10), (lx - 3, ly + 11)]
        for p in pts:
            if p not in px and 0 <= p[0] < N:
                px[p] = LINE
    # 縁取り
    out = {}
    for (x, y), c in px.items():
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in px and 0 <= q[0] < N and 0 <= q[1] < N and (q not in out):
                if not (not cast and (x, y) in px and px[(x, y)] == LINE):
                    out[q] = (28, 22, 14)
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    for p, c in out.items():
        img.putpixel(p, c + (255,))
    for (x, y), c in px.items():
        if 0 <= x < N and 0 <= y < N:
            img.putpixel((x, y), c + (255,))
    return img


def main():
    os.makedirs(TEX_DIR, exist_ok=True)
    os.makedirs(BUILD_DIR, exist_ok=True)
    imgs = {}
    for rid, _ in ORDER:
        for cast in (False, True):
            img = draw_rod(RODS[rid], cast)
            img.save(os.path.join(TEX_DIR, rid + ("_cast" if cast else "") + ".png"))
            imgs[(rid, cast)] = img
    sheet(imgs)


def sheet(imgs):
    fonts = glob.glob("/System/Library/Fonts/ヒラギノ角ゴシック*") + glob.glob("/System/Library/Fonts/*Hiragino*")
    font = ImageFont.truetype(fonts[0], 18) if fonts else ImageFont.load_default()
    sc, pad, lab = 12, 14, 56
    tile = N * sc
    W = len(ORDER) * (tile + pad) + pad
    H = 2 * (tile + pad) + lab + pad
    out = Image.new("RGB", (W, H), (58, 62, 70))
    d = ImageDraw.Draw(out)
    for i, (rid, name) in enumerate(ORDER):
        x = pad + i * (tile + pad)
        for row, cast in enumerate((False, True)):
            y = pad + row * (tile + pad)
            bg = Image.new("RGB", (tile, tile), (92, 100, 112))
            big = imgs[(rid, cast)].resize((tile, tile), Image.NEAREST)
            bg.paste(big, (0, 0), big)
            out.paste(bg, (x, y))
        d.text((x, 2 * (tile + pad) + 4), name, font=font, fill=(240, 240, 240))
        d.text((x, 2 * (tile + pad) + 28), rid, font=font, fill=(170, 176, 186))
    out.save(os.path.join(BUILD_DIR, "rods_contact_sheet.png"))


if __name__ == "__main__":
    main()
