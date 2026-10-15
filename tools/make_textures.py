#!/usr/bin/env python3
"""魚12種の 32x32 テクスチャと見本画像（コンタクトシート）を作る。

使い方:  python3 resourcepack/tools/make_textures.py
出力:    resourcepack/assets/hnmt/textures/item/fish/<ID>.png
         resourcepack-build/contact_sheet.png
絵はすべて手続きで描くので、色や形はこのファイルの SPECS を直して作り直せる。
"""
import glob
import math
import os
import random

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEX_DIR = os.path.join(ROOT, "resourcepack", "assets", "hnmt", "textures", "item", "fish")
BUILD_DIR = os.path.join(ROOT, "resourcepack-build")
N = 32


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def dark(c, f=0.45):
    return tuple(int(v * f) for v in c)


def light(c, f=0.25):
    return tuple(int(v + (255 - v) * f) for v in c)


class Canvas:
    def __init__(self):
        self.px = {}

    def set(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < N and 0 <= y < N:
            self.px[(x, y)] = c

    def get(self, x, y):
        return self.px.get((x, y))

    def outline(self):
        """不透明ピクセルの外周を、自分の色を暗くした線にする。"""
        edge = {}
        for (x, y), c in self.px.items():
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (x + dx, y + dy) not in self.px:
                    edge[(x, y)] = dark(c, 0.4)
                    break
        self.px.update(edge)

    def image(self):
        img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
        for (x, y), c in self.px.items():
            img.putpixel((x, y), c + (255,))
        return img


# ---------------------------------------------------------------- 横向きの魚
def profile(t, H, peak, tail_frac):
    """頭(t=0)から尾の付け根(t=1)までの半分の厚み。"""
    if t < peak:
        return H * math.sqrt(max(0.0, 1 - ((peak - t) / peak) ** 2))
    u = (t - peak) / (1 - peak)
    return H * (1 - (1 - tail_frac) * u ** 1.3)


def side_fish(s):
    cv = Canvas()
    x0, x1, cy, H = s["x0"], s["x1"], s["cy"], s["H"]
    peak, tf = s.get("peak", 0.38), s.get("tail_frac", 0.22)
    fin = s["fin"]
    span = x1 - x0

    def half(x):
        t = (x - x0) / span
        return max(0.6, profile(min(max(t, 0), 1), H, peak, tf))

    # 背びれ・尻びれ（胴体より先に描いて、後ろに回す）
    def tri_fin(a, b, hgt, top, lean=0.3):
        for x in range(int(x0 + a * span), int(x0 + b * span) + 1):
            u = (x - (x0 + a * span)) / max(1, (b - a) * span)
            prof = u / lean if u < lean else (1 - u) / (1 - lean)
            fh = max(1, round(hgt * prof))
            edge = cy - half(x) if top else cy + half(x)
            for k in range(fh + 1):
                y = edge - k - 0 if top else edge + k
                cv.set(x, round(y), fin if k % 2 == 0 else lerp(fin, dark(fin), 0.35))

    for a, b, h, lean in s.get("dorsal", []):
        tri_fin(a, b, h, True, lean)
    for a, b, h, lean in s.get("anal", []):
        tri_fin(a, b, h, False, lean)

    # 尾びれ
    tw, th, fk = s["tail_w"], s["tail_h"], s.get("fork", 0.0)
    xe = int(x1)
    for x in range(xe, xe + tw + 1):
        u = (x - xe) / tw
        hh = 0.9 + th * u
        for y in range(int(cy - hh) - 1, int(cy + hh) + 2):
            dy = y + 0.5 - cy - 0.5
            if abs(dy) > hh:
                continue
            if fk and u > 0.3 and abs(dy) < (u - 0.3) * fk * th * 1.0:
                continue
            c = fin if (y + x) % 4 else lerp(fin, dark(fin), 0.25)
            cv.set(x, y, c)

    # 胴体
    pal = s["pal"]  # 背(暗) 背 腹寄り 腹
    cut = s.get("cut", (-0.55, -0.05, 0.45))
    for x in range(int(x0), int(x1) + 1):
        h = half(x)
        for y in range(int(cy - h) - 1, int(cy + h) + 2):
            v = (y + 0.5 - cy) / h
            if abs(v) > 1.0:
                continue
            c = pal[0] if v < cut[0] else pal[1] if v < cut[1] else pal[2] if v < cut[2] else pal[3]
            cv.set(x, y, c)

    # 模様
    for fn in s.get("pattern", []):
        for (x, y), c in list(cv.px.items()):
            t = (x - x0) / span
            h = half(x)
            v = (y + 0.5 - cy) / h
            if 0 <= t <= 1 and abs(v) <= 1:
                r = fn(x, y, t, v, c)
                if r is not None:
                    cv.set(x, y, r)

    # えら・胸びれ・目
    gx = x0 + span * s.get("gill", 0.24)
    for y in range(int(cy - H), int(cy + H) + 1):
        v = (y + 0.5 - cy) / max(H, 1)
        px = round(gx + 0.9 * v * v)
        c = cv.get(px, y)
        if c and abs(v) < 0.85:
            cv.set(px, y, lerp(c, dark(c), 0.55))
    pf = s.get("pec", fin)
    px, py = round(gx + 2), round(cy + H * 0.25)
    for dx, dy in ((0, 0), (1, 0), (2, 1), (1, 1), (0, 1)):
        if cv.get(px + dx, py + dy):
            cv.set(px + dx, py + dy, lerp(pf, dark(pf), 0.25))
    ex, ey = round(x0 + span * s.get("eye_t", 0.09)) + 1, round(cy - H * s.get("eye_v", 0.28))
    eye = s.get("eye_big", False)
    cv.set(ex, ey, (15, 15, 20))
    cv.set(ex + 1, ey, (15, 15, 20))
    cv.set(ex, ey + 1, (15, 15, 20))
    cv.set(ex + 1, ey + 1, (70, 70, 80) if not eye else (230, 230, 220))
    if eye:
        cv.set(ex, ey - 1, (235, 235, 225))
        cv.set(ex - 1, ey, (235, 235, 225))
    # 口
    mx, my = round(x0) + 0, round(cy + H * 0.15)
    if cv.get(mx, my):
        cv.set(mx, my, dark(cv.get(mx, my), 0.5))
    cv.outline()
    # 縁取りの後に描く飾り（細い線など）
    for fn in s.get("post", []):
        fn(cv)
    return cv


# 模様の部品
def hash_spots(seed, density, vmax, tmin=0.28, color=(30, 30, 40), vmin=-1.0):
    rnd = random.Random(seed)
    cache = {}

    def f(x, y, t, v, c):
        if (x, y) not in cache:
            cache[(x, y)] = rnd.random()
        if cache[(x, y)] < density and vmin <= v <= vmax and t > tmin and t < 0.92:
            return color
        return None

    return f


def stripe(vlo, vhi, color, tmin=0.2, tmax=0.95):
    def f(x, y, t, v, c):
        if vlo <= v <= vhi and tmin <= t <= tmax:
            return color
        return None

    return f


def wave_bars(color, vmax=0.12, period=3, amp=1.3, tmin=0.28, tmax=0.97):
    def f(x, y, t, v, c):
        if v < vmax and tmin <= t <= tmax and (y + round(amp * math.sin(x * 0.85))) % period == 0:
            return color
        return None

    return f


def dot_row(vc, step, color, tmin=0.3):
    def f(x, y, t, v, c):
        if t > tmin and t < 0.92 and abs(v - vc) < 0.16 and x % step == 0:
            return color
        return None

    return f


def blob(tc, vc, tw, vw, color):
    def f(x, y, t, v, c):
        if abs(t - tc) <= tw and abs(v - vc) <= vw:
            return color
        return None

    return f


def diag_band(color, t0=0.1, slope=0.55, width=1.6, vmax=0.45):
    def f(x, y, t, v, c):
        xs = (t - t0) * 24
        if v < vmax and abs(xs + (v + 0.2) * 7 * slope * 2 - 0) < width and t < 0.6:
            return color
        return None

    return f


def sheen(color, vlo=-0.88, vhi=-0.7, tmin=0.3, tmax=0.7):
    def f(x, y, t, v, c):
        if vlo <= v <= vhi and tmin <= t <= tmax and (x + y) % 2 == 0:
            return color
        return None

    return f


# ---------------------------------------------------------------- 個別の魚
def make_unagi():
    cv = Canvas()
    back, mid, belly = (28, 38, 56), (44, 58, 80), (214, 204, 150)
    fin = (36, 46, 66)
    pts = []
    for x in range(2, 31):
        cy = 16 + 4.2 * math.sin((x - 4) * 0.27)
        u = (x - 2) / 28
        h = 2.9 if x < 6 else 2.5 - 1.2 * max(0, u - 0.55) / 0.45
        h = max(0.8, h) + abs(4.2 * 0.27 * math.cos((x - 4) * 0.27)) * 0.75
        pts.append((x, cy, h))
    # 背びれ・尻びれ（体の全長に沿う）
    for x, cy, h in pts:
        if 8 <= x <= 30:
            cv.set(x, round(cy - h) - 1, fin)
        if 14 <= x <= 29:
            cv.set(x, round(cy + h), lerp(fin, belly, 0.4))
    for x, cy, h in pts:
        for y in range(int(cy - h) - 2, int(cy + h) + 3):
            v = (y + 0.5 - cy) / h
            if abs(v) > 1:
                continue
            cv.set(x, y, back if v < -0.35 else mid if v < 0.2 else lerp(belly, mid, 0.25) if v < 0.5 else belly)
    # 蒲焼きのような照り
    for x, cy, h in pts:
        if x > 7 and x % 3 == 0:
            c = cv.get(x, round(cy - h * 0.55))
            if c:
                cv.set(x, round(cy - h * 0.55), light(c, 0.25))
    # 胸びれ
    hx, hy = pts[4][0], pts[4][1]
    cv.set(hx + 1, round(hy + 1), lerp(fin, belly, 0.3))
    cv.outline()
    ex, ey = 4, round(pts[2][1] - 1)
    cv.set(ex, ey, (240, 235, 200))
    cv.set(ex + 1, ey, (10, 10, 14))
    cv.set(ex + 1, ey + 1, (10, 10, 14))
    cv.set(2, round(pts[0][1] + 1), dark(back, 0.6))
    return cv


def make_hirame():
    cv = Canvas()
    base, dk, lt, belly = (122, 98, 66), (80, 60, 40), (166, 142, 100), (208, 196, 168)
    cx, cy, rx, ry = 14.5, 16.5, 12.0, 8.6
    rnd = random.Random(7)
    # 縁びれ
    for x in range(32):
        for y in range(32):
            dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            d = dx * dx + dy * dy
            if d <= 1.0:
                c = base
                n = rnd.random()
                if n < 0.22:
                    c = dk
                elif n < 0.34:
                    c = lt
                if d > 0.68:  # ふち
                    c = lerp(c, dk, 0.35) if (x + y) % 2 == 0 else lt if n < 0.5 else c
                cv.set(x, y, c)
    # 尾
    for x in range(26, 31):
        hh = 1 + (x - 26) * 0.7
        for y in range(int(cy - hh), int(cy + hh) + 1):
            cv.set(x, y, dk if (x + y) % 2 else base)
    # 斑点
    for (sx, sy) in ((9, 12), (14, 20), (18, 13), (21, 18), (12, 16), (23, 15)):
        cv.set(sx, sy, (230, 220, 190))
        cv.set(sx + 1, sy, lt)
    # 側線
    for x in range(8, 26):
        y = round(cy - 0.5 + 1.0 * math.sin((x - 8) * 0.25) * (-1))
        if cv.get(x, y):
            cv.set(x, y, dark(base, 0.7))
    cv.outline()
    # 左に寄った目（ヒラメは左ヒラメ）と口
    for ex, ey in ((5, 10), (8, 9)):
        cv.set(ex, ey, (240, 235, 210))
        cv.set(ex + 1, ey, (10, 10, 14))
        cv.set(ex, ey + 1, (10, 10, 14))
        cv.set(ex + 1, ey + 1, (10, 10, 14))
    cv.set(3, 18, dark(base, 0.4))
    cv.set(4, 19, dark(base, 0.4))
    return cv


def make_ika():
    cv = Canvas()
    body, spot, lt, fin = (238, 222, 214), (178, 92, 86), (252, 242, 236), (222, 196, 192)
    # ひれ（矢じり型）
    for y in range(2, 14):
        w = 6 - abs(y - 8) * 0.9
        if w > 0.5:
            for x in range(int(16 - w - 3), int(16 + w + 3)):
                if abs(x + 0.5 - 16) > 1.5:
                    cv.set(x, y, fin)
    # 胴
    for y in range(2, 19):
        w = 1.4 + 4.6 * math.sin(min(1, (y - 2) / 11) * math.pi / 2) if y < 14 else 6.0 - (y - 14) * 0.4
        for x in range(int(16 - w), int(16 + w) + 1):
            if abs(x + 0.5 - 16) <= w:
                c = lt if x < 14 else body if x < 18 else lerp(body, spot, 0.12)
                cv.set(x, y, c)
    # 頭と腕
    for y in range(18, 22):
        for x in range(11, 21):
            cv.set(x, y, lerp(body, spot, 0.2))
    for x, ln in ((11, 7), (13, 8), (15, 9), (17, 9), (19, 8), (21, 7)):
        for k in range(ln):
            cv.set(x if k < 3 else x + (1 if x > 15 else -1) * (k - 2) // 3, 22 + k, lerp(body, spot, 0.35 + (k * 0.04)))
    for x, ln in ((12, 11), (20, 11)):  # 長い触腕
        for k in range(ln):
            cv.set(x + (-1 if x < 16 else 1) * (k // 4), 21 + k, lerp(body, spot, 0.5))
    # 色素胞の斑点
    rnd = random.Random(3)
    for _ in range(26):
        x, y = rnd.randint(12, 20), rnd.randint(3, 18)
        if cv.get(x, y) and abs(x - 16) < 5:
            cv.set(x, y, spot)
    cv.outline()
    for ex in (12, 19):
        cv.set(ex, 19, (245, 245, 235))
        cv.set(ex, 20, (10, 10, 14))
        cv.set(ex + 1, 19, (10, 10, 14))
        cv.set(ex + 1, 20, (10, 10, 14))
    return cv


# ---------------------------------------------------------------- 仕様
def silver_pal(back_d, back, side, belly):
    return [back_d, back, side, belly]


SPECS = {
    "salmon": dict(  # ★1
        x0=3, x1=24, cy=16, H=6.2, peak=0.4, tail_frac=0.28, tail_w=6, tail_h=6.3, fork=0.5,
        fin=(150, 126, 128), pal=silver_pal((70, 88, 104), (108, 130, 146), (196, 190, 190), (240, 214, 206)),
        dorsal=[(0.40, 0.62, 3, 0.4)], anal=[(0.55, 0.72, 2, 0.4)],
        pattern=[hash_spots(11, 0.16, 0.0, 0.3, (40, 44, 58)), stripe(0.35, 0.5, (226, 168, 160), 0.3, 0.9)],
    ),
    "kohada": dict(  # ★1 小さい若魚
        x0=6, x1=21, cy=16, H=4.0, peak=0.4, tail_frac=0.3, tail_w=5, tail_h=4.4, fork=0.6,
        fin=(150, 168, 186), pal=silver_pal((52, 72, 110), (92, 120, 160), (186, 204, 220), (240, 246, 250)),
        dorsal=[(0.42, 0.62, 2, 0.4)], anal=[(0.55, 0.74, 1, 0.4)], eye_big=False,
        pattern=[dot_row(-0.2, 3, (36, 48, 82), 0.35), dot_row(0.1, 3, (110, 134, 172), 0.38)],
    ),
    "konoshiro": dict(  # ★2 コハダの成魚
        x0=3, x1=24, cy=16, H=7.2, peak=0.42, tail_frac=0.22, tail_w=6, tail_h=6.5, fork=0.55,
        fin=(140, 158, 176), pal=silver_pal((46, 66, 100), (88, 118, 156), (180, 200, 218), (238, 244, 250)),
        dorsal=[(0.38, 0.64, 3, 0.35)], anal=[(0.55, 0.74, 2, 0.4)],
        pattern=[blob(0.27, -0.28, 0.07, 0.2, (24, 30, 52)), dot_row(-0.02, 3, (60, 84, 128), 0.38), sheen((130, 160, 200))],
        post=[lambda cv: [cv.set(x, 5 + (x - 15), (140, 158, 176)) for x in range(15, 19)]],
    ),
    "tai": dict(  # ★2
        x0=3, x1=23, cy=16.5, H=8.2, peak=0.4, tail_frac=0.2, tail_w=6, tail_h=6.5, fork=0.5,
        fin=(214, 84, 84), pal=silver_pal((196, 66, 74), (226, 92, 98), (238, 140, 138), (250, 214, 206)),
        dorsal=[(0.28, 0.66, 4, 0.3)], anal=[(0.55, 0.74, 3, 0.4)], eye_big=True, eye_t=0.07, eye_v=0.1, gill=0.27,
        pattern=[hash_spots(5, 0.1, -0.1, 0.3, (84, 160, 216)), sheen((250, 160, 156), -0.85, -0.65)],
    ),
    "saba": dict(  # ★1
        x0=2, x1=24, cy=16, H=5.2, peak=0.36, tail_frac=0.16, tail_w=6, tail_h=5.6, fork=0.7,
        fin=(104, 132, 140), pal=silver_pal((34, 90, 108), (52, 124, 134), (170, 190, 192), (240, 244, 240)),
        dorsal=[(0.32, 0.52, 3, 0.4), (0.66, 0.78, 2, 0.4)], anal=[(0.6, 0.72, 2, 0.4)],
        pattern=[wave_bars((16, 44, 60)), sheen((110, 190, 180), -0.95, -0.8, 0.3, 0.9)],
    ),
    "hamachi": dict(  # ★2 ブリの若魚
        x0=2, x1=23, cy=16, H=5.6, peak=0.4, tail_frac=0.18, tail_w=7, tail_h=6.0, fork=0.8,
        fin=(196, 204, 150), pal=silver_pal((58, 96, 120), (92, 134, 150), (196, 210, 196), (244, 246, 236)),
        dorsal=[(0.36, 0.55, 3, 0.4), (0.62, 0.8, 2, 0.4)], anal=[(0.58, 0.74, 2, 0.4)],
        pattern=[stripe(0.0, 0.2, (232, 214, 96), 0.18, 0.96)],
    ),
    "buri": dict(  # ★3 成魚（太く、金の線が濃い）
        x0=1, x1=24, cy=16, H=7.6, peak=0.4, tail_frac=0.16, tail_w=7, tail_h=7.2, fork=0.85,
        fin=(232, 200, 72), pal=silver_pal((34, 66, 98), (56, 98, 130), (176, 198, 206), (246, 246, 238)),
        dorsal=[(0.34, 0.52, 3, 0.4), (0.62, 0.8, 3, 0.4)], anal=[(0.56, 0.74, 3, 0.4)], pec=(232, 200, 72),
        pattern=[stripe(-0.05, 0.3, (246, 202, 52), 0.14, 0.97), sheen((120, 170, 210))],
    ),
    "kanpachi": dict(  # ★3
        x0=2, x1=24, cy=16, H=7.0, peak=0.4, tail_frac=0.16, tail_w=6, tail_h=6.6, fork=0.7,
        fin=(180, 150, 70), pal=silver_pal((78, 92, 70), (116, 130, 94), (200, 204, 164), (248, 246, 226)),
        dorsal=[(0.34, 0.5, 3, 0.4), (0.58, 0.82, 2, 0.4)], anal=[(0.58, 0.76, 3, 0.4)],
        pattern=[diag_band((26, 30, 22)), stripe(0.0, 0.18, (238, 196, 70), 0.3, 0.97)],
    ),
    "maguro": dict(  # ★3 大きな紡錘形
        x0=1, x1=25, cy=16, H=8.4, peak=0.42, tail_frac=0.1, tail_w=6, tail_h=8.0, fork=0.95,
        fin=(40, 62, 108), pal=silver_pal((14, 30, 74), (28, 56, 112), (150, 170, 196), (232, 238, 244)),
        dorsal=[(0.38, 0.56, 4, 0.35), (0.6, 0.7, 3, 0.4)], anal=[(0.58, 0.68, 3, 0.4)], eye_big=True, eye_t=0.07, eye_v=0.15,
        pattern=[sheen((86, 132, 196), -0.92, -0.76, 0.2, 0.9), stripe(0.15, 0.25, (110, 136, 190), 0.3, 0.9)],
    ),
}

CUSTOM = {"unagi": make_unagi, "hirame": make_hirame, "ika": make_ika}
ORDER = [
    ("unagi", "ウナギ", 2), ("salmon", "サーモン", 1), ("kohada", "コハダ", 1), ("konoshiro", "コノシロ", 2),
    ("tai", "タイ", 2), ("hirame", "ヒラメ", 2), ("saba", "サバ", 1), ("hamachi", "ハマチ", 2),
    ("buri", "ブリ", 3), ("ika", "イカ", 2), ("kanpachi", "カンパチ", 3), ("maguro", "マグロ", 3),
]


def finlets(cv, xs, ytop, ybot, color):
    for x in xs:
        cv.set(x, ytop, color)
        cv.set(x, ybot, color)


def main():
    os.makedirs(TEX_DIR, exist_ok=True)
    os.makedirs(BUILD_DIR, exist_ok=True)
    imgs = {}
    for fid, _, _ in ORDER:
        cv = CUSTOM[fid]() if fid in CUSTOM else side_fish(SPECS[fid])
        img = cv.image()
        img.save(os.path.join(TEX_DIR, fid + ".png"))
        imgs[fid] = img
    contact_sheet(imgs)


def contact_sheet(imgs):
    fonts = glob.glob("/System/Library/Fonts/ヒラギノ角ゴシック*") + glob.glob("/System/Library/Fonts/*Hiragino*") \
        + glob.glob("/Library/Fonts/*.ttf")
    font = ImageFont.truetype(fonts[0], 19) if fonts else ImageFont.load_default()
    scale, cols = 8, 4
    tile = N * scale
    pad, lab = 16, 40
    rows = math.ceil(len(ORDER) / cols)
    W = cols * (tile + pad) + pad
    H = rows * (tile + lab + pad) + pad
    sheet = Image.new("RGB", (W, H), (58, 62, 70))
    d = ImageDraw.Draw(sheet)
    for i, (fid, name, star) in enumerate(ORDER):
        cx = pad + (i % cols) * (tile + pad)
        cy = pad + (i // cols) * (tile + lab + pad)
        bg = Image.new("RGB", (tile, tile), (92, 100, 112))
        bgd = ImageDraw.Draw(bg)
        for gy in range(0, tile, 32):
            for gx in range(0, tile, 32):
                if (gx // 32 + gy // 32) % 2:
                    bgd.rectangle([gx, gy, gx + 31, gy + 31], fill=(84, 92, 104))
        big = imgs[fid].resize((tile, tile), Image.NEAREST)
        bg.paste(big, (0, 0), big)
        sheet.paste(bg, (cx, cy))
        d.text((cx, cy + tile + 6), f"{name}  {'★' * star}  {fid}", font=font, fill=(240, 240, 240))
    sheet.save(os.path.join(BUILD_DIR, "contact_sheet.png"))


if __name__ == "__main__":
    main()
