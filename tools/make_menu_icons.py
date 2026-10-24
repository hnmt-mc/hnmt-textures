#!/usr/bin/env python3
"""町のメニュー（hnmt-townymenu）のボタン用アイコン（16px、バニラに近い粗さ）を作る。

`hnmt:menu/<名前>` として、テクスチャ・モデル・アイテム定義の3つを書く。
絵は、塗りだけを描き、まわりの1画素の縁取り（暗い色）は自動で付ける。
使い方: python3 tools/make_menu_icons.py [--sheet 見本.png]
"""
import argparse
import json
from PIL import Image, ImageDraw
from artwork import PACK

SIZE = 16
ASSETS = PACK / 'assets/hnmt'
# プラグイン側（hnmt-townymenu の menu_icons.json）と同じ並び。ここを変えたら、あちらの写しも変える。
ICONS = [
    'blank', 'back', 'close', 'previous', 'next', 'filter', 'help',
    'status', 'find', 'invites', 'create', 'mytown', 'manage', 'locked',
    'door_open', 'door_closed', 'notown',
    'join', 'cancel', 'talk', 'flow',
    'check_ok', 'check_ng', 'start',
    'mayor', 'residents', 'tax', 'bank', 'spawn',
    'allow', 'deny', 'pvp', 'fire', 'explosion', 'mobs',
    'preset_residents', 'preset_visit', 'preset_open',
    'terms', 'trouble', 'web',
    'plot', 'claim', 'unclaim', 'forsale', 'notforsale', 'plot_type', 'trust',
]
# 統合版（Geyser）は、「元のアイテム」と item_model の組み合わせで見た目を決める。アイコンごとに、元のアイテムを1つに決める。
# プラグイン（hnmt-townymenu）も、同じ元のアイテムを使う（tools/menu_icons.json の写しで、テストが突き合わせる）。
BASES = {
    'blank': 'gray_stained_glass_pane', 'back': 'arrow', 'close': 'barrier', 'previous': 'arrow', 'next': 'arrow',
    'filter': 'ender_eye', 'help': 'book', 'status': 'paper', 'find': 'compass', 'invites': 'paper',
    'create': 'crafting_table', 'mytown': 'oak_sign', 'manage': 'anvil', 'locked': 'tripwire_hook',
    'door_open': 'oak_door', 'door_closed': 'iron_door', 'notown': 'paper', 'join': 'emerald_block', 'cancel': 'barrier',
    'talk': 'writable_book', 'flow': 'book', 'check_ok': 'lime_concrete', 'check_ng': 'red_concrete', 'start': 'crafting_table',
    'mayor': 'golden_helmet', 'residents': 'white_bed', 'tax': 'gold_nugget', 'bank': 'gold_ingot', 'spawn': 'ender_pearl',
    'allow': 'lime_concrete', 'deny': 'red_concrete', 'pvp': 'diamond_sword', 'fire': 'flint_and_steel', 'explosion': 'tnt',
    'mobs': 'zombie_head', 'preset_residents': 'shield', 'preset_visit': 'spyglass', 'preset_open': 'emerald',
    'terms': 'written_book', 'trouble': 'bell', 'web': 'white_banner',
    'plot': 'map', 'claim': 'red_banner', 'unclaim': 'gray_banner', 'forsale': 'oak_sign', 'notforsale': 'oak_sign',
    'plot_type': 'painting', 'trust': 'tripwire_hook',
}
P = {
    'ink': '#2b2f3a',
    'white': '#f7f7f2', 'light': '#d5dae2', 'gray': '#9aa3b0', 'dark': '#5d6573',
    'red': '#dc5a5a', 'red_d': '#a23c3c', 'orange': '#ec9a40', 'yellow': '#f2d466', 'gold': '#d6a838', 'gold_d': '#a67c22',
    'green': '#5cbd6b', 'green_d': '#3a8a4a', 'lime': '#7fe08a',
    'blue': '#5b92dc', 'blue_d': '#3a64a8', 'cyan': '#80d4e6', 'teal': '#2f8f86', 'purple': '#9b6ed6',
    'wood': '#9a7040', 'wood_d': '#664828', 'tan': '#dcc08c', 'beige': '#f1e8cb',
}


def color(key):
    return tuple(bytes.fromhex(P[key][1:])) + (255,)


class Canvas:
    def __init__(self):
        self.image = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)

    def rect(self, x0, y0, x1, y1, key):
        self.draw.rectangle([x0, y0, x1, y1], fill=color(key))

    def poly(self, points, key):
        self.draw.polygon(points, fill=color(key))

    def line(self, points, key, width=1):
        self.draw.line(points, fill=color(key), width=width)

    def ellipse(self, x0, y0, x1, y1, key):
        self.draw.ellipse([x0, y0, x1, y1], fill=color(key))

    def px(self, points, key):
        for x, y in points:
            if 0 <= x < SIZE and 0 <= y < SIZE: self.image.putpixel((x, y), color(key))

    def finish(self, outline=True):
        """二値の透明にそろえ、まわりに暗い縁を付ける。"""
        src = self.image
        for y in range(SIZE):
            for x in range(SIZE):
                r, g, b, a = src.getpixel((x, y))
                src.putpixel((x, y), (r, g, b, 255) if a >= 128 else (0, 0, 0, 0))
        if not outline: return src
        out = src.copy()
        for y in range(SIZE):
            for x in range(SIZE):
                if src.getpixel((x, y))[3]: continue
                if any(0 <= x + dx < SIZE and 0 <= y + dy < SIZE and src.getpixel((x + dx, y + dy))[3]
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    out.putpixel((x, y), color('ink'))
        return out


def block(c, base, hi, lo):
    """立体感のある四角（上と左が明るく、下と右が暗い）。"""
    c.rect(2, 2, 13, 13, base)
    c.rect(2, 2, 13, 2, hi); c.rect(2, 2, 2, 13, hi)
    c.rect(2, 13, 13, 13, lo); c.rect(13, 2, 13, 13, lo)


def check(c, key='white'):
    """太さ2のチェック。"""
    for x, y in ((4, 8), (5, 9), (6, 10), (7, 9), (8, 8), (9, 7), (10, 6), (11, 5)):
        c.px([(x, y), (x, y + 1)], key)


def cross(c, key='white', lo=4, size=8):
    """太さ2の×。lo から size 画素ぶんの斜め線2本。"""
    for i in range(size):
        c.px([(lo + i, lo + i), (lo + i + 1, lo + i), (lo + size - 1 - i, lo + i), (lo + size - i, lo + i)], key)


def house(c, scale_down=False):
    c.poly([(1, 8), (8, 2), (14, 8)], 'red'); c.px([(8, 2)], 'red_d')
    c.rect(3, 8, 12, 14, 'tan'); c.rect(3, 8, 12, 8, 'light')
    c.rect(7, 10, 9, 14, 'wood'); c.px([(9, 12)], 'yellow')


def padlock(c, ox=0, oy=0, open_=False):
    c.rect(3 + ox, 7 + oy, 12 + ox, 13 + oy, 'gold'); c.rect(3 + ox, 7 + oy, 12 + ox, 7 + oy, 'yellow')
    c.rect(3 + ox, 13 + oy, 12 + ox, 13 + oy, 'gold_d')
    if open_:
        c.rect(9 + ox, 3 + oy, 10 + ox, 5 + oy, 'light'); c.rect(5 + ox, 2 + oy, 10 + ox, 3 + oy, 'light')
    else:
        c.rect(5 + ox, 3 + oy, 6 + ox, 7 + oy, 'light'); c.rect(9 + ox, 3 + oy, 10 + ox, 7 + oy, 'light'); c.rect(5 + ox, 3 + oy, 10 + ox, 4 + oy, 'light')
    c.rect(7 + ox, 9 + oy, 8 + ox, 11 + oy, 'ink')


def draw(name):
    c = Canvas()
    if name == 'blank':
        return c.finish(outline=False)
    elif name == 'back':
        c.poly([(2, 8), (8, 2), (8, 5), (13, 5), (13, 11), (8, 11), (8, 14)], 'white'); c.rect(9, 6, 12, 7, 'light')
    elif name == 'close':
        cross(c, 'red', lo=3, size=10)
    elif name == 'previous':
        c.poly([(11, 2), (4, 8), (11, 14)], 'blue'); c.line([(10, 4), (6, 8)], 'cyan')
    elif name == 'next':
        c.poly([(4, 2), (11, 8), (4, 14)], 'blue'); c.line([(5, 4), (9, 8)], 'cyan')
    elif name == 'filter':
        c.poly([(2, 3), (13, 3), (9, 8), (9, 13), (6, 11), (6, 8)], 'cyan'); c.rect(2, 3, 13, 4, 'white')
    elif name == 'help':
        c.rect(2, 3, 13, 13, 'wood'); c.rect(4, 4, 12, 12, 'beige')
        c.px([(7, 5), (8, 5), (9, 6), (9, 7), (8, 8), (7, 9), (7, 11)], 'ink')
    elif name == 'status':
        c.rect(3, 2, 12, 14, 'beige')
        for y in (5, 7, 9, 11): c.rect(5, y, 10, y, 'gray')
    elif name == 'find':
        c.ellipse(2, 2, 10, 10, 'blue'); c.ellipse(4, 4, 8, 8, 'cyan'); c.line([(9, 9), (13, 13)], 'wood', 2)
    elif name == 'invites':
        c.rect(2, 4, 13, 12, 'beige'); c.line([(2, 4), (7, 8)], 'gray'); c.line([(13, 4), (8, 8)], 'gray'); c.rect(7, 8, 8, 9, 'red')
    elif name == 'create':
        house(c); c.rect(11, 9, 14, 10, 'green'); c.rect(12, 8, 13, 11, 'green')
    elif name == 'mytown':
        c.rect(2, 2, 13, 8, 'tan'); c.rect(2, 2, 13, 2, 'beige'); c.rect(7, 9, 8, 14, 'wood')
        c.rect(4, 4, 11, 4, 'wood_d'); c.rect(4, 6, 9, 6, 'wood_d')
    elif name == 'manage':
        c.poly([(3, 2), (12, 2), (12, 8), (8, 14), (3, 8)], 'blue'); c.poly([(5, 4), (10, 4), (10, 8), (7, 11), (5, 8)], 'cyan')
    elif name == 'locked':
        padlock(c)
    elif name == 'door_open':
        c.rect(4, 2, 11, 14, 'wood'); c.rect(5, 3, 10, 7, 'tan'); c.rect(5, 9, 10, 13, 'tan'); c.px([(9, 8)], 'yellow')
    elif name == 'door_closed':
        c.rect(4, 2, 11, 14, 'gray'); c.rect(5, 3, 10, 7, 'light'); c.rect(5, 9, 10, 13, 'light')
        c.px([(5, 3), (10, 3), (5, 13), (10, 13), (9, 8)], 'dark')
    elif name == 'notown':
        for i in range(2, 14, 2):
            c.px([(i, 3), (i, 13), (2, i + 1 if i + 1 < 14 else 13), (13, i)], 'gray')
        c.rect(7, 6, 8, 11, 'gray'); c.rect(5, 8, 10, 9, 'gray')
    elif name == 'join':
        block(c, 'green', 'lime', 'green_d'); check(c)
    elif name == 'cancel':
        block(c, 'red', 'orange', 'red_d'); cross(c)
    elif name == 'talk':
        c.rect(2, 3, 13, 10, 'white'); c.poly([(4, 10), (4, 13), (8, 10)], 'white'); c.px([(5, 6), (8, 6), (11, 6)], 'dark')
    elif name == 'flow':
        c.rect(3, 3, 12, 13, 'beige'); c.rect(2, 2, 13, 4, 'tan'); c.rect(2, 12, 13, 14, 'tan')
        for y in (6, 8, 10): c.rect(5, y, 10, y, 'gray')
    elif name == 'check_ok':
        c.ellipse(1, 1, 14, 14, 'green'); check(c)
    elif name == 'check_ng':
        c.ellipse(1, 1, 14, 14, 'red'); cross(c)
    elif name == 'start':
        c.line([(4, 13), (11, 6)], 'wood', 2); c.poly([(9, 2), (14, 7), (12, 9), (7, 4)], 'gray'); c.line([(9, 3), (13, 7)], 'light')
    elif name == 'mayor':
        c.poly([(2, 12), (2, 5), (5, 8), (8, 3), (11, 8), (14, 5), (14, 12)], 'gold'); c.rect(2, 12, 14, 13, 'gold_d')
        c.px([(8, 8)], 'red'); c.px([(5, 10), (11, 10)], 'blue')
    elif name == 'residents':
        c.ellipse(2, 2, 6, 6, 'tan'); c.rect(1, 7, 7, 13, 'blue')
        c.ellipse(9, 3, 13, 7, 'tan'); c.rect(8, 8, 14, 13, 'green')
    elif name == 'tax':
        c.ellipse(2, 2, 13, 13, 'gold'); c.ellipse(4, 4, 11, 11, 'yellow'); c.rect(7, 5, 8, 10, 'gold_d'); c.rect(5, 7, 10, 7, 'gold_d')
    elif name == 'bank':
        for top, key in ((10, 'gold'), (7, 'yellow'), (4, 'gold')):
            c.rect(3, top, 12, top + 2, key); c.rect(3, top, 12, top, 'yellow' if key == 'gold' else 'white')
    elif name == 'spawn':
        c.ellipse(2, 2, 13, 13, 'teal'); c.ellipse(4, 4, 9, 9, 'green'); c.px([(5, 5), (6, 4)], 'lime'); c.px([(10, 10), (9, 11)], 'green_d')
    elif name == 'allow':
        c.rect(2, 2, 13, 13, 'lime'); check(c)
    elif name == 'deny':
        c.rect(2, 2, 13, 13, 'red'); cross(c)
    elif name == 'pvp':
        c.line([(3, 12), (12, 3)], 'light', 2); c.line([(12, 12), (3, 3)], 'light', 2)
        c.px([(2, 13), (3, 13), (13, 13), (12, 13)], 'wood'); c.px([(1, 14), (14, 14)], 'wood_d')
    elif name == 'fire':
        c.poly([(8, 1), (12, 6), (13, 11), (10, 14), (6, 14), (3, 11), (4, 7), (6, 9)], 'orange')
        c.poly([(8, 6), (10, 9), (10, 12), (8, 13), (6, 12), (6, 9)], 'yellow')
    elif name == 'explosion':
        pts = [(8, 0), (10, 5), (15, 4), (11, 8), (14, 13), (9, 10), (6, 15), (6, 10), (1, 12), (4, 8), (1, 4), (6, 5)]
        c.poly(pts, 'orange'); c.poly([(8, 4), (10, 7), (8, 11), (6, 7)], 'yellow')
    elif name == 'mobs':
        c.rect(2, 2, 13, 13, 'green'); c.rect(2, 2, 13, 3, 'lime')
        c.rect(4, 5, 6, 7, 'ink'); c.rect(9, 5, 11, 7, 'ink'); c.rect(7, 8, 8, 10, 'ink'); c.rect(6, 10, 9, 12, 'ink')
    elif name == 'preset_residents':
        c.poly([(0, 7), (6, 2), (11, 7)], 'red'); c.rect(2, 7, 9, 13, 'tan'); c.rect(5, 9, 6, 13, 'wood')
        c.rect(9, 9, 14, 14, 'gold'); c.rect(9, 9, 14, 9, 'yellow'); c.rect(10, 6, 10, 8, 'light'); c.rect(13, 6, 13, 8, 'light'); c.rect(10, 6, 13, 6, 'light'); c.px([(11, 11), (12, 11), (11, 12), (12, 12)], 'ink')
    elif name == 'preset_visit':
        c.ellipse(1, 4, 14, 11, 'white'); c.ellipse(5, 4, 10, 11, 'blue'); c.rect(7, 6, 8, 9, 'ink')
    elif name == 'preset_open':
        padlock(c, open_=True)
    elif name == 'terms':
        c.rect(3, 2, 12, 14, 'blue'); c.rect(3, 2, 4, 14, 'blue_d'); c.rect(6, 4, 10, 7, 'beige'); c.rect(9, 11, 10, 14, 'red')
    elif name == 'trouble':
        c.poly([(8, 2), (11, 5), (12, 11), (14, 12), (2, 12), (4, 11), (5, 5)], 'gold'); c.rect(6, 4, 7, 9, 'yellow'); c.ellipse(7, 12, 9, 14, 'gold_d')
    elif name == 'web':
        c.ellipse(2, 2, 13, 13, 'blue'); c.poly([(4, 4), (7, 3), (8, 6), (5, 8), (3, 7)], 'green'); c.poly([(8, 9), (12, 8), (11, 12), (9, 12)], 'green')
        c.line([(7, 2), (7, 13)], 'cyan')
    elif name == 'plot':
        for (x, y), key in (((2, 2), 'green'), ((8, 2), 'lime'), ((2, 8), 'lime'), ((8, 8), 'green')):
            c.rect(x, y, x + 5, y + 5, key)
        c.rect(7, 2, 7, 13, 'tan'); c.rect(2, 7, 13, 7, 'tan')
    elif name == 'claim':
        c.rect(3, 2, 4, 14, 'wood'); c.poly([(5, 2), (13, 4), (5, 8)], 'red'); c.px([(6, 3), (7, 3)], 'orange')
    elif name == 'unclaim':
        c.rect(3, 2, 4, 14, 'wood'); c.poly([(5, 2), (13, 4), (5, 8)], 'gray'); c.px([(6, 3), (7, 3)], 'light')
        c.line([(9, 13), (13, 9)], 'red'); c.line([(9, 9), (13, 13)], 'red')
    elif name == 'forsale':
        c.rect(2, 2, 13, 9, 'tan'); c.rect(2, 2, 13, 2, 'beige'); c.rect(7, 10, 8, 14, 'wood')
        c.ellipse(5, 3, 10, 8, 'gold'); c.rect(7, 4, 8, 7, 'gold_d')
    elif name == 'notforsale':
        c.rect(2, 2, 13, 9, 'tan'); c.rect(2, 2, 13, 2, 'beige'); c.rect(7, 10, 8, 14, 'wood')
        c.ellipse(5, 3, 10, 8, 'gold'); c.rect(7, 4, 8, 7, 'gold_d'); c.line([(3, 9), (12, 2)], 'red', 2)
    elif name == 'plot_type':
        c.ellipse(1, 2, 14, 13, 'tan'); c.ellipse(9, 8, 12, 11, 'tan')
        c.rect(4, 4, 5, 5, 'red'); c.rect(8, 3, 9, 4, 'blue'); c.rect(11, 5, 12, 6, 'green'); c.rect(3, 8, 4, 9, 'yellow')
    elif name == 'trust':
        c.ellipse(2, 2, 7, 7, 'gold'); c.ellipse(4, 4, 5, 5, 'ink'); c.line([(7, 7), (13, 13)], 'gold', 2); c.px([(11, 11), (12, 10), (10, 12)], 'gold_d')
    else:
        raise KeyError(name)
    return c.finish()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sheet')
    args = parser.parse_args()
    COLS, CELL = 8, SIZE * 8 + 8
    sheet = Image.new('RGBA', (COLS * CELL + 8, ((len(ICONS) + COLS - 1) // COLS) * CELL + 8), (58, 62, 72, 255))
    for index, name in enumerate(ICONS):
        image = draw(name)
        path = ASSETS / 'textures/item/menu' / f'{name}.png'
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path)
        write(ASSETS / 'models/item/menu' / f'{name}.json', {'parent': 'minecraft:item/generated', 'textures': {'layer0': f'hnmt:item/menu/{name}'}})
        write(ASSETS / 'items/menu' / f'{name}.json', {'model': {'type': 'minecraft:model', 'model': f'hnmt:item/menu/{name}'}})
        big = image.resize((SIZE * 8, SIZE * 8), Image.NEAREST)
        sheet.paste(big, (8 + (index % COLS) * CELL, 8 + (index // COLS) * CELL), big)
    (PACK / 'tools/menu_icons.json').write_text(json.dumps({name: 'minecraft:' + BASES[name] for name in ICONS}, indent=2) + '\n', encoding='utf-8')
    if args.sheet: sheet.save(args.sheet)
    print(len(ICONS), 'icons')


if __name__ == '__main__':
    main()
