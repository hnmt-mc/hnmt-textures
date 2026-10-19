#!/usr/bin/env python3
"""料理・米・いくら・まな板の32x32の絵を、座標と配色の指定から作る。

スロットの中で小さく見えても、何の料理か分かるよう、皿や器を枠いっぱいに取り、
具の色を種類ごとにはっきり変え、1ピクセルの暗い輪郭で囲む。
使い方: python3 tools/make_food_art.py
"""

from PIL import Image, ImageDraw
from artwork import DISHES, save, sheet
from make_fish_art import Canvas, rgb, N, OUTLINE

C = rgb
RICE, RICE_SHADE, GRAIN = C("#fffdf0"), C("#e6dfc4"), C("#d8cfa6")
GREEN, GREEN_D, GREEN_L = C("#4fae5a"), C("#2f7d3f"), C("#9fdc86")
WASABI = C("#8fd16a")
DAIKON, DAIKON_S = C("#fbfdf6"), C("#dfe8dc")


def ell(cv, cx, cy, rx, ry, color):
    for y in range(N):
        for x in range(N):
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1:
                cv.set(x, y, color)


def hline(cv, x0, x1, y, color):
    for x in range(x0, x1 + 1):
        cv.set(x, y, color)


def vline(cv, x, y0, y1, color):
    for y in range(y0, y1 + 1):
        cv.set(x, y, color)


def to_image(cv):
    cv.outline()
    im = Image.new("RGBA", (N, N))
    for (x, y), c in cv.px.items():
        if 0 <= x < N:
            im.putpixel((x, y), c + (255,))
    return im


# 名前 -> (身, 縁の影, ハイライト)
FLESH = {
    "salmon": (C("#ff7d48"), C("#d24f2b"), C("#ffc3a0")),
    "maguro": (C("#dc3a55"), C("#a31f3b"), C("#ff93a2")),
    "tai": (C("#ffc9cf"), C("#e58f9c"), C("#ffffff")),
    "hirame": (C("#f5f2ea"), C("#c8c3b5"), C("#ffffff")),
    "hamachi": (C("#ffc796"), C("#dc9560"), C("#fff0d4")),
    "buri": (C("#f1a577"), C("#b9663d"), C("#ffd8b6")),
    "ika": (C("#fbf4f8"), C("#cbb4cb"), C("#ffffff")),
    "kanpachi": (C("#ffd6b2"), C("#d89e6e"), C("#fff4e0")),
    "saba": (C("#f4e4dc"), C("#b9a095"), C("#ffffff")),
    "kohada": (C("#f6eee4"), C("#b9ac9d"), C("#ffffff")),
    "unagi": (C("#8d4d2b"), C("#4f2a18"), C("#dd8f56")),
}
SKIN = {"saba": (C("#2f6fa3"), C("#cfe3f0")), "kohada": (C("#3a4f86"), C("#c9d9ea"))}


def plate(cv):
    ell(cv, 16, 22, 14.5, 7.2, C("#3f7189"))  # 影
    ell(cv, 16, 20.5, 14.5, 7.2, C("#7db6c8"))  # 縁
    ell(cv, 16, 20, 12.2, 5.8, C("#f3f8ee"))  # 内側
    ell(cv, 16, 21, 9.5, 3.8, C("#e4efe6"))


def shiso(cv, x, y):
    cv.poly([(x, y + 4), (x + 2, y), (x + 6, y - 1), (x + 7, y + 2), (x + 4, y + 5)], GREEN)
    cv.poly([(x + 1, y + 3), (x + 3, y + 1), (x + 5, y + 1)], GREEN_L)
    vline(cv, x + 3, y + 1, y + 4, GREEN_D)


def daikon(cv, x, y):
    for i in range(5):
        hline(cv, x + (i % 2), x + 6 - (i % 2), y + i, DAIKON if i % 2 == 0 else DAIKON_S)


def slice_(cv, x, y, fish, skin_top=False):
    base, edge, high = FLESH[fish]
    pts = [(x, y + 2), (x + 3, y), (x + 8, y + 1), (x + 8, y + 8), (x + 4, y + 9), (x, y + 7)]
    cv.poly(pts, edge)
    cv.poly([(x + 1, y + 2), (x + 3, y + 1), (x + 7, y + 2), (x + 7, y + 7), (x + 4, y + 8), (x + 1, y + 6)], base)
    if fish in SKIN:
        skin, shine = SKIN[fish]
        cv.poly([(x + 1, y + 2), (x + 3, y + 1), (x + 7, y + 2), (x + 7, y + 4), (x + 1, y + 4)], skin)
        hline(cv, x + 2, x + 6, y + 2, shine)
    else:
        vline(cv, x + 2, y + 3, y + 6, high)
        cv.set(x + 5, y + 3, high)
        cv.set(x + 5, y + 4, high)
    if fish == "salmon":
        for dx in (3, 5):
            cv.set(x + dx, y + 5, C("#ffe9d8")); cv.set(x + dx + 1, y + 6, C("#ffe9d8"))
    if fish == "maguro":
        cv.set(x + 4, y + 4, C("#f7b1b8")); cv.set(x + 5, y + 5, C("#f7b1b8"))
    if fish == "unagi":
        hline(cv, x + 2, x + 6, y + 4, C("#6a3820"))


def sashimi(fish):
    cv = Canvas()
    plate(cv)
    daikon(cv, 4, 18)
    shiso(cv, 3, 14)
    if fish in ("ika", "hirame"):
        # 薄造り・いか: 細長い切り身を並べる
        base, edge, high = FLESH[fish]
        for i, x in enumerate((9, 12, 15, 18, 21)):
            cv.poly([(x, 11 + i % 2), (x + 3, 10), (x + 4, 17), (x + 1, 18)], edge)
            cv.poly([(x + 1, 11 + i % 2), (x + 3, 11), (x + 3, 16), (x + 1, 17)], base)
            vline(cv, x + 1, 12, 15, high)
    else:
        for x, y in ((8, 11), (12, 10), (16, 11), (20, 12)):
            slice_(cv, x, y, fish)
    ell(cv, 24, 22, 2, 1.3, WASABI)
    return to_image(cv)


def nigiri(fish):
    cv = Canvas()
    base, edge, high = FLESH[fish]
    # シャリ
    cv.poly([(6, 21), (8, 17), (24, 17), (26, 21), (25, 26), (7, 26)], RICE_SHADE)
    cv.poly([(7, 21), (9, 18), (23, 18), (25, 21), (24, 24), (8, 24)], RICE)
    for p in [(10, 20), (13, 22), (16, 20), (19, 22), (22, 20), (11, 23), (18, 23)]:
        cv.set(*p, GRAIN)
    # ネタ
    cv.poly([(2, 16), (6, 9), (16, 7), (26, 9), (30, 16), (28, 21), (16, 19), (4, 21)], edge)
    cv.poly([(3, 16), (7, 10), (16, 8), (25, 10), (29, 16), (27, 19), (16, 17), (5, 19)], base)
    hline(cv, 8, 23, 9, high)
    if fish in SKIN:
        skin, shine = SKIN[fish]
        cv.poly([(4, 15), (7, 10), (16, 8), (25, 10), (28, 14), (16, 12), (6, 14)], skin)
        hline(cv, 9, 22, 10, shine)
        for x in range(9, 24, 3):
            cv.set(x, 12, shine)
    elif fish == "salmon":
        for x in (9, 13, 17, 21):
            for k in range(4):
                cv.set(x + k // 2, 11 + k, C("#ffe6d2"))
    elif fish == "maguro":
        for x in (9, 14, 19):
            cv.set(x, 11, C("#f7aab3")); cv.set(x + 1, 12, C("#f7aab3")); cv.set(x + 2, 13, C("#f7aab3"))
    elif fish == "tai":
        hline(cv, 6, 25, 15, C("#e4474f"))
        for x in (10, 15, 20):
            vline(cv, x, 11, 13, C("#ffffff"))
    elif fish == "hamachi":
        hline(cv, 5, 27, 13, C("#f2c94c"))
        for x in (10, 16, 22):
            vline(cv, x, 10, 12, high)
    elif fish == "buri":
        hline(cv, 5, 27, 14, C("#c0453a"))
        for x in (9, 14, 20):
            vline(cv, x, 10, 12, high)
    elif fish == "kanpachi":
        hline(cv, 5, 27, 13, C("#6d8a3f"))
        for x in (10, 16, 22):
            vline(cv, x, 10, 12, high)
    elif fish == "ika":
        for x in range(8, 25, 4):
            vline(cv, x, 10, 15, C("#e8d7e4"))
    elif fish == "unagi":
        for x in (8, 12, 19, 23):
            for k in range(4):
                cv.set(x + k // 2, 10 + k, C("#6a3820"))
        cv.poly([(14, 8), (18, 8), (19, 21), (13, 21)], C("#1f4d33"))  # 海苔の帯
        vline(cv, 15, 9, 20, C("#2f7d4f"))
    return to_image(cv)


def bowl(cv, rim_color=C("#e8b84a"), body=C("#b8323a"), body_d=C("#7e1f2c")):
    cv.poly([(2, 15), (30, 15), (27, 25), (22, 28), (10, 28), (5, 25)], body_d)  # 外側の影
    cv.poly([(3, 16), (29, 16), (26, 24), (21, 27), (11, 27), (6, 24)], body)
    cv.poly([(5, 20), (27, 20), (26, 22), (6, 22)], C("#d0575c"))  # つやの帯
    ell(cv, 16, 15, 14.5, 6, rim_color)  # 縁
    ell(cv, 16, 15, 12.8, 4.8, C("#fffdf0"))  # ごはん


def don(fish):
    cv = Canvas()
    bowl(cv)
    ell(cv, 16, 15, 11.5, 4, RICE)
    if fish == "ikura":
        for cy, off in ((12, 0), (15, 2), (18, 0)):
            for cx in range(6 + off, 27, 4):
                if ((cx - 16) / 11) ** 2 + ((cy - 15) / 4) ** 2 > 1:
                    continue
                ell(cv, cx, cy, 2, 2, C("#d96a2b"))
                ell(cv, cx - 0.4, cy - 0.4, 1.2, 1.2, C("#ffa24d"))
                cv.set(cx - 1, cy - 1, C("#ffe1a8"))
    elif fish == "unagi":
        for x in (7, 12, 17, 22):
            cv.poly([(x, 12), (x + 4, 11), (x + 5, 18), (x + 1, 19)], C("#4f2a18"))
            cv.poly([(x + 1, 12), (x + 3, 12), (x + 4, 17), (x + 2, 18)], C("#8d4d2b"))
            cv.set(x + 2, 13, C("#dd8f56"))
        shiso(cv, 23, 10)
    else:
        base, edge, high = FLESH[fish]
        for x, y in ((6, 11), (11, 11), (16, 11), (21, 12)):
            cv.poly([(x, y), (x + 5, y - 1), (x + 6, y + 6), (x + 1, y + 7)], edge)
            cv.poly([(x + 1, y), (x + 4, y), (x + 5, y + 5), (x + 2, y + 6)], base)
            vline(cv, x + 2, y + 1, y + 3, high)
        shiso(cv, 23, 9)
    return to_image(cv)


def soup():
    cv = Canvas()
    cv.poly([(3, 14), (29, 14), (26, 25), (21, 28), (11, 28), (6, 25)], C("#37596b"))
    cv.poly([(4, 15), (28, 15), (25, 24), (21, 27), (11, 27), (7, 24)], C("#6f9fb0"))
    cv.poly([(6, 19), (26, 19), (25, 22), (7, 22)], C("#9cc7d2"))
    ell(cv, 16, 14, 14, 6, C("#d8e8ec"))
    ell(cv, 16, 14, 12.2, 4.8, C("#e8c98a"))  # 汁
    cv.poly([(8, 12), (14, 9), (21, 10), (23, 14), (16, 17), (9, 16)], C("#d9505a"))  # 鯛の身
    cv.poly([(9, 12), (14, 10), (20, 11), (21, 14), (16, 16), (10, 15)], C("#ff9aa2"))
    hline(cv, 11, 18, 11, C("#ffffff"))
    cv.set(12, 13, C("#ffffff")); cv.set(15, 14, C("#ffffff"))
    for x, y in ((20, 15), (23, 13), (7, 15)):  # ねぎ
        ell(cv, x, y, 1.5, 1.2, GREEN)
    return to_image(cv)


def grill(fish):
    cv = Canvas()
    plate(cv)
    if fish == "konoshiro":  # 姿焼き
        cv.poly([(4, 17), (8, 11), (18, 10), (23, 13), (28, 10), (28, 20), (23, 17), (17, 21), (8, 21)], C("#6b4a2c"))
        cv.poly([(5, 17), (9, 12), (18, 11), (22, 14), (27, 12), (27, 18), (22, 16), (17, 20), (9, 20)], C("#d7a15a"))
        hline(cv, 8, 18, 12, C("#f0c987"))
        for x in (10, 13, 16):
            vline(cv, x, 13, 18, C("#7a5030"))
        cv.eye(6, 14, big=False)
    else:
        dark, mid, light = {
            "salmon": (C("#c0583b"), C("#f08a5f"), C("#ffc79f")),
            "buri": (C("#6e3a1c"), C("#b9672f"), C("#e9a15e")),
            "unagi": (C("#4a2514"), C("#8d4d2b"), C("#d98b50")),
        }[fish]
        cv.poly([(4, 17), (8, 10), (21, 9), (28, 13), (26, 20), (14, 21)], dark)
        cv.poly([(5, 17), (9, 11), (21, 10), (27, 13), (25, 19), (14, 20)], mid)
        hline(cv, 10, 22, 11, light)
        for x in (9, 13, 17, 21):  # 焼き目
            for k in range(5):
                cv.set(x + k // 2, 12 + k, dark)
    shiso(cv, 3, 16)
    ell(cv, 25, 22, 2.2, 1.6, C("#fff6c9"))  # 大根おろし/すだち
    cv.set(24, 21, C("#ffffff"))
    return to_image(cv)


def simmer(fish):
    cv = Canvas()
    plate(cv)
    ell(cv, 16, 20, 11, 4.8, C("#9a5a2e"))  # 煮汁
    ell(cv, 16, 19.5, 9.5, 3.8, C("#b97a45"))
    if fish == "saba":
        cv.poly([(5, 17), (9, 10), (22, 9), (27, 14), (22, 20), (9, 20)], C("#3d3a46"))
        cv.poly([(6, 17), (10, 11), (22, 10), (26, 14), (21, 19), (10, 19)], C("#f0d7c2"))
        cv.poly([(6, 16), (10, 11), (22, 10), (26, 13), (6, 14)], C("#2f6fa3"))
        hline(cv, 10, 22, 11, C("#cfe3f0"))
        for x in range(9, 24, 3):
            cv.set(x, 13, C("#173a5a"))
        for x in (11, 16, 21):  # 味噌
            cv.set(x, 17, C("#7a4a28")); cv.set(x + 1, 18, C("#7a4a28"))
    else:
        cv.poly([(5, 17), (9, 10), (22, 9), (27, 14), (22, 20), (9, 20)], C("#7a6a58"))
        cv.poly([(6, 17), (10, 11), (22, 10), (26, 14), (21, 19), (10, 19)], C("#f7f1e6"))
        hline(cv, 10, 22, 11, C("#ffffff"))
        for x in (11, 16, 21):
            vline(cv, x, 13, 17, C("#d6c8ad"))
        cv.eye(9, 12, big=False)
    ell(cv, 25, 22, 2, 1.4, GREEN)
    return to_image(cv)


def board():
    cv = Canvas()
    cv.poly([(2, 9), (24, 9), (27, 6), (30, 8), (30, 12), (27, 14), (24, 14), (24, 27), (2, 27)], C("#8f6a3c"))
    cv.poly([(3, 10), (23, 10), (23, 26), (3, 26)], C("#d7aa6a"))
    cv.poly([(24, 10), (27, 7), (29, 8), (29, 12), (27, 13), (24, 13)], C("#d7aa6a"))
    for y, c in ((13, C("#e8c88f")), (17, C("#c28f55")), (21, C("#e8c88f")), (24, C("#c28f55"))):
        hline(cv, 5, 21, y, c)
    ell(cv, 27.5, 10, 1.3, 1.3, C("#6b4a25"))  # 吊り下げ穴
    return to_image(cv)


def rice():
    cv = Canvas()
    cv.poly([(3, 16), (29, 16), (26, 26), (21, 28), (11, 28), (6, 26)], C("#3d5f8f"))
    cv.poly([(4, 17), (28, 17), (25, 25), (21, 27), (11, 27), (7, 25)], C("#5f8ac8"))
    cv.poly([(6, 21), (26, 21), (25, 23), (7, 23)], C("#8fb4e4"))
    ell(cv, 16, 14, 13, 8.5, RICE)  # 山盛り
    ell(cv, 16, 11.5, 9, 5.5, C("#ffffff"))
    for p in [(10, 10), (14, 8), (18, 9), (21, 12), (12, 13), (17, 14), (23, 15), (8, 14), (15, 11)]:
        cv.set(*p, RICE_SHADE)
    return to_image(cv)


def ikura():
    cv = Canvas()
    plate(cv)
    for cy, off in ((15, 0), (18, 2), (21, 0)):
        for cx in range(6 + off, 27, 4):
            if ((cx - 16) / 11) ** 2 + ((cy - 19) / 5.2) ** 2 > 1:
                continue
            ell(cv, cx, cy, 2, 2, C("#d96a2b"))
            ell(cv, cx - 0.4, cy - 0.4, 1.2, 1.2, C("#ffa24d"))
            cv.set(cx - 1, cy - 1, C("#ffe1a8"))
    shiso(cv, 21, 8)
    return to_image(cv)


def dish(identifier):
    kind, _, fish = identifier.partition("_")
    if kind == "sashimi":
        return sashimi(fish)
    if kind == "nigiri":
        return nigiri(fish)
    if kind == "don":
        return don(fish)
    if kind == "grill":
        return grill(fish)
    if kind == "simmer":
        return simmer(fish)
    if identifier == "soup_tai":
        return soup()
    raise ValueError(identifier)


def main():
    entries = []
    for identifier, label in DISHES:
        im = dish(identifier)
        save(im, "dish", identifier)
        entries.append((im, label, identifier))
    sheet(entries, "dishes_contact_sheet.png", columns=8, tile=128)
    extras = [("rice", "米", rice()), ("ikura", "いくら", ikura()), ("board", "まな板", board())]
    out = []
    for identifier, label, im in extras:
        save(im, "", identifier)
        out.append((im, label, identifier))
    sheet(out, "extras_contact_sheet.png", columns=3)


if __name__ == "__main__":
    main()
