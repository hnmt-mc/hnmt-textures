#!/usr/bin/env python3
"""食べ物（餅・団子・粉・麺・茶・南蛮菓子・そば・茶の苗と作物・5つの道具）の絵とモデルを作る。

材料と料理と苗は、16px の平らなアイコン（バニラの item/generated）。道具（臼と杵・挽き臼・麺打ち台・茶釜・南蛮菓子の窯）は、
精米機と同じ、4×4の小片を並べた絵と、直方体のモデル（models3d/food）。そば・茶の作物は、バニラの作物と同じ交差した板2枚。

  python3 tools/make_wafu_food.py            絵とモデルを書き出す
  python3 tools/make_wafu_food.py --preview  絵を拡大して並べる（build/food/preview.png）
"""
import argparse
import json
from PIL import Image, ImageDraw
from artwork import PACK, BUILD
from make_rice_models import _blade, _cube, _tile, display as rice_display, GENERATED, FIXED_PLAIN, MILL, PALETTE as RICE_PALETTE

SIZE = 16
PALETTE = dict(RICE_PALETTE)
PALETTE.update({
    'white': '#fbf9f3', 'white_shade': '#e3e0d4', 'white_dark': '#c4bfae', 'cream': '#f1e6c4',
    'seed': '#6b4a2f', 'seed_light': '#8a6a45', 'seed_dark': '#43301f',
    'leaf_deep': '#2f6b2f', 'leaf_mid': '#4f9a3f', 'leaf_pale': '#7fc15a', 'leaf_new': '#b7e07a',
    'flour': '#f4f1ea', 'flour_shade': '#d9d4c7', 'soba_flour': '#cbbfae', 'soba_flour_shade': '#a89d8c',
    'matcha': '#8fcf5a', 'matcha_dark': '#5fa83a', 'matcha_light': '#d7f09a', 'tea': '#7aa84a', 'tea_dark': '#5f8e36',
    'clay': '#d8c7a6', 'clay_shade': '#b59f78', 'clay_dark': '#8a6f4d', 'bowl_blue': '#3f6fa8', 'bowl_white': '#e8eef5',
    'pink': '#f4b6c2', 'pink_dark': '#d98aa0', 'green_dango': '#a9d68a', 'stick': '#b38b52',
    'noodle': '#f3ecd2', 'noodle_dark': '#6b5a4a', 'noodle_shade': '#4a3d31', 'onion': '#5aa84a', 'bamboo': '#c9a85a', 'bamboo_dark': '#9c7e3a', 'nori': '#1f2a1f',
    'sponge': '#f2cf5a', 'sponge_shade': '#d9ae3a', 'crust': '#b5651d', 'crust_dark': '#8a4a12',
    'candy_pink': '#f48fb1', 'candy_white': '#ffffff', 'candy_yellow': '#ffe082', 'candy_green': '#a5d6a7', 'candy_lilac': '#c5b3e6',
    'brick': '#a8432b', 'brick_dark': '#8d3523', 'brick_light': '#c25a3a', 'brick_deep': '#6e2a1c', 'soot': '#1e1b1a',
    'fire': '#ff9b21', 'fire_light': '#ffcf4a', 'brass': '#c9a23a', 'brass_dark': '#9a7a22',
    'pot': '#3b3f45', 'pot_light': '#5b6068', 'pot_dark': '#25282c', 'wood_pale': '#d9b98a',
})

# 平らなアイコンの名前 → 表示名（絵のID。FoodItem.id() と同じ）
ICONS = [('buckwheat', 'そばの実'), ('tea_leaf', '茶葉'), ('wheat_flour', '小麦粉'), ('buckwheat_flour', 'そば粉'), ('matcha_powder', '抹茶の粉'),
         ('chawan', '茶碗'), ('mochi', '餅'), ('dango', '団子'), ('udon', 'うどん'), ('soba', 'そば'), ('konpeito', '金平糖'),
         ('kasutera', 'カステラ'), ('green_tea', '緑茶'), ('matcha', '抹茶'), ('buckwheat_seedling', 'そばの苗'), ('tea_seedling', '茶の苗')]
TOOLS = [('mortar', '臼と杵'), ('grinder', '挽き臼'), ('noodle', '麺打ち台'), ('kettle', '茶釜'), ('oven', '南蛮菓子の窯')]
PLANTS = [('%s_plant_%s' % (crop, stage), '%s・%s' % (label, stage_label))
          for crop, label in (('buckwheat', 'そば'), ('tea', '茶'))
          for stage, stage_label in (('seedling', '苗'), ('growing', '成長中'), ('mature', '実り'))]


def rgba(key):
    return tuple(bytes.fromhex(PALETTE[key][1:])) + (255,)


def new():
    return Image.new('RGBA', (SIZE, SIZE))


def put(image, x, y, key):
    if 0 <= x < SIZE and 0 <= y < SIZE: image.putpixel((x, y), rgba(key))


def rect(image, x0, y0, x1, y1, key):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1): put(image, x, y, key)


def ellipse(image, box, light, shade, outline=None):
    """box = (x0, y0, x1, y1)の楕円。下と右を影にする。"""
    x0, y0, x1, y1 = box
    cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2 + 0.3, (y1 - y0) / 2 + 0.3
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d > 1: continue
            edge = d > 0.62
            key = shade if (edge and (x >= cx or y >= cy)) else light
            if outline and d > 0.82: key = outline
            put(image, x, y, key)


def mound(image, base_y, width, light, shade, top_y):
    """粉などの小さな山（下が広く、上が細い）。"""
    cx = 8
    for y in range(top_y, base_y + 1):
        half = max(1, round(width / 2 * (y - top_y + 1) / (base_y - top_y + 1)))
        for x in range(cx - half, cx + half + 1):
            put(image, x, y, shade if (x == cx - half or y == base_y or (x + y) % 5 == 0) else light)


def bowl(image, body, rim, interior_key, y_rim=8):
    """茶碗の形（横から見て、上から少し見下ろす）。"""
    ellipse(image, (2, y_rim, 13, y_rim + 2), interior_key, interior_key)
    for y in range(y_rim + 1, y_rim + 6):
        shrink = max(0, y - (y_rim + 2))
        for x in range(2 + shrink, 14 - shrink):
            put(image, x, y, body if x < 9 else (rim if y == y_rim + 1 else 'clay_shade'))
    rect(image, 5, y_rim + 6, 10, y_rim + 6, 'clay_dark')
    for x in range(2, 14): put(image, x, y_rim + 1, rim)


def draw(name):
    image = new()
    if name == 'buckwheat':
        for x, y in ((3, 11), (6, 12), (9, 11), (11, 13), (5, 8), (8, 8), (4, 14), (8, 14), (12, 10), (7, 5), (10, 6)):
            put(image, x, y - 1, 'seed_light'); put(image, x - 1, y, 'seed'); put(image, x, y, 'seed'); put(image, x + 1, y, 'seed_dark'); put(image, x, y + 1, 'seed_dark')
    elif name == 'tea_leaf':
        for cx, cy, tilt in ((5, 10, 1), (10, 8, -1), (8, 4, 0)):
            for i in range(6):
                put(image, cx + (i * tilt) // 3, cy - i, 'leaf_mid')
                put(image, cx + (i * tilt) // 3 + 1, cy - i, 'leaf_pale')
                put(image, cx + (i * tilt) // 3 - 1, cy - i, 'leaf_deep')
            put(image, cx, cy + 1, 'leaf_deep')
    elif name == 'wheat_flour':
        mound(image, 14, 11, 'flour', 'flour_shade', 6)
        for x, y in ((6, 9), (9, 11), (11, 13)): put(image, x, y, 'white')
    elif name == 'buckwheat_flour':
        mound(image, 14, 11, 'soba_flour', 'soba_flour_shade', 6)
        for x, y in ((6, 9), (9, 11), (11, 13)): put(image, x, y, 'seed_light')
    elif name == 'matcha_powder':
        mound(image, 14, 11, 'matcha', 'matcha_dark', 6)
        for x, y in ((6, 9), (9, 11), (11, 13)): put(image, x, y, 'matcha_light')
    elif name == 'chawan':
        bowl(image, 'clay', 'clay_dark', 'clay_dark')
        for x, y in ((4, 11), (6, 12)): put(image, x, y, 'white_shade')
    elif name == 'mochi':
        ellipse(image, (2, 5, 13, 13), 'white', 'white_shade')
        for x in range(4, 12): put(image, x, 13, 'white_dark')
        put(image, 5, 7, 'white'); put(image, 6, 7, 'white')
    elif name == 'dango':
        for x in range(7, 9): rect(image, x, 1, x, 15, 'stick')
        for (cy, key, shade) in ((12, 'pink', 'pink_dark'), (8, 'white', 'white_dark'), (4, 'green_dango', 'leaf_pale')):
            ellipse(image, (4, cy - 2, 11, cy + 2), key, shade)
    elif name == 'udon':
        ellipse(image, (1, 5, 14, 8), 'bowl_white', 'white_shade')
        for y in range(8, 14):
            shrink = max(0, y - 10)
            for x in range(2 + shrink, 14 - shrink): put(image, x, y, 'bowl_white' if x < 9 else 'white_shade')
        rect(image, 2, 9, 13, 9, 'bowl_blue')
        for x in range(3, 13): put(image, x, 6, 'noodle' if x % 2 == 0 else 'cream')
        for x, y in ((5, 5), (8, 5), (10, 6)): put(image, x, y, 'onion')
    elif name == 'soba':
        rect(image, 1, 9, 14, 13, 'bamboo')
        for x in range(1, 15, 2): rect(image, x, 9, x, 13, 'bamboo_dark')
        for y in (6, 7, 8):
            for x in range(3, 13): put(image, x, y, 'noodle_dark' if (x + y) % 2 == 0 else 'noodle_shade')
        rect(image, 7, 5, 8, 8, 'nori')
    elif name == 'konpeito':
        for (x, y, key) in ((3, 10, 'candy_pink'), (7, 12, 'candy_white'), (11, 10, 'candy_yellow'), (5, 6, 'candy_green'), (9, 7, 'candy_lilac'), (12, 4, 'candy_pink'), (3, 3, 'candy_yellow')):
            put(image, x, y, key); put(image, x - 1, y, key); put(image, x + 1, y, key); put(image, x, y - 1, key); put(image, x, y + 1, key)
    elif name == 'kasutera':
        rect(image, 2, 6, 13, 7, 'crust')
        rect(image, 2, 8, 13, 12, 'sponge')
        rect(image, 2, 12, 13, 12, 'sponge_shade')
        rect(image, 13, 6, 14, 12, 'sponge_shade')
        rect(image, 2, 5, 13, 5, 'crust_dark')
        for x, y in ((4, 9), (7, 10), (10, 9), (5, 11), (11, 11)): put(image, x, y, 'sponge_shade')
    elif name == 'green_tea':
        bowl(image, 'clay', 'clay_dark', 'tea')
        for x in range(4, 12): put(image, x, 9, 'tea_dark' if x % 3 == 0 else 'tea')
    elif name == 'matcha':
        bowl(image, 'clay', 'clay_dark', 'matcha')
        for x in range(4, 12): put(image, x, 9, 'matcha_light' if x % 2 == 0 else 'matcha_dark')
        put(image, 7, 8, 'matcha_light'); put(image, 9, 8, 'matcha_light')
    elif name == 'buckwheat_seedling':
        for y in range(8, 15): put(image, 8, y, 'leaf_mid')
        for x, y in ((5, 8), (6, 7), (10, 8), (11, 7), (7, 5), (9, 5), (6, 10), (10, 11)):
            put(image, x, y, 'leaf_pale'); put(image, x - 1, y, 'leaf_mid') if x < 8 else put(image, x + 1, y, 'leaf_mid')
        put(image, 8, 4, 'pink'); put(image, 8, 3, 'white')
        rect(image, 6, 15, 10, 15, 'root')
    elif name == 'tea_seedling':
        for y in range(9, 15): put(image, 8, y, 'wood_dark')
        for x, y in ((6, 8), (10, 8), (5, 10), (11, 10), (7, 6), (9, 6), (8, 4)):
            put(image, x, y, 'leaf_mid'); put(image, x - 1 if x < 8 else x + 1, y, 'leaf_deep'); put(image, x, y - 1, 'leaf_pale')
        rect(image, 6, 15, 10, 15, 'root')
    else:
        raise ValueError('Unknown food icon: ' + name)
    return image


def plant(name):
    """交差した板2枚に貼る、作物の絵（背景は透明）。"""
    crop, _, stage = name.split('_')
    image = new()
    if crop == 'buckwheat':
        if stage == 'seedling':
            for x, h, lean in ((4, 4, 1), (8, 5, 0), (12, 4, -1)): _blade(image, x, h, lean, False)
        elif stage == 'growing':
            for x, h, lean in ((3, 9, 1), (7, 11, 0), (10, 10, 0), (13, 8, -1)): _blade(image, x, h, lean, False)
            for x, y in ((3, 7), (7, 5), (10, 6), (13, 8)): put(image, x, y, 'leaf_pale')
        else:
            for x, h, lean in ((3, 9, 1), (7, 12, 0), (10, 11, 0), (13, 8, -1)): _blade(image, x, h, lean, False)
            for x, y in ((3, 6), (4, 5), (7, 3), (8, 4), (10, 4), (11, 5), (13, 7)): put(image, x, y, 'white')
            for x, y in ((7, 4), (10, 5), (3, 7), (12, 7), (8, 5)): put(image, x, y, 'seed_light'); put(image, x, y + 1, 'seed')
    else:
        base = [(4, 12, 'leaf_deep'), (8, 12, 'leaf_deep'), (12, 12, 'leaf_deep')]
        heights = {'seedling': 4, 'growing': 8, 'mature': 11}[stage]
        for y in range(15 - heights, 16):
            half = 2 + (y - (15 - heights)) * 5 // max(1, heights)
            for x in range(8 - half, 8 + half + 1):
                key = 'leaf_deep' if (x + y) % 3 == 0 else ('leaf_mid' if (x + y) % 3 == 1 else 'leaf_pale')
                put(image, x, y, key)
        if stage == 'mature':
            for x, y in ((6, 6), (10, 7), (8, 5), (5, 9), (11, 10)): put(image, x, y, 'leaf_new'); put(image, x, y - 1, 'white')
        rect(image, 7, 15, 9, 15, 'root')
    return image


# 道具の絵: 小片（列, 行）→（ふつうの色, 点の色）。モデルは、面ごとに小片を1つ割り当てる。
SWATCHES = {
    'mortar': {(0, 0): ('wood_dark', 'wood'), (1, 0): ('wood', 'wood_light'), (2, 0): ('wood_light', 'wood'), (3, 0): ('hole', 'wood_dark'),
               (0, 1): ('rice_light', 'rice'), (1, 1): ('wood_dark', 'hole'), (2, 1): ('iron', 'iron_dark'), (3, 1): ('wood_pale', 'wood_light'),
               (0, 2): ('wood', 'wood_dark'), (1, 2): ('wood_light', 'wood_pale'), (2, 2): ('stone', 'stone_speck'), (3, 2): ('red', 'red_light'),
               (0, 3): ('wood_dark', 'hole'), (1, 3): ('wood', 'wood_dark'), (2, 3): ('wood_light', 'wood'), (3, 3): ('stone_dark', 'stone_speck')},
    'grinder': {(0, 0): ('stone_dark', 'stone_speck'), (1, 0): ('stone', 'stone_speck'), (2, 0): ('stone_light', 'stone'), (3, 0): ('stone_light', 'hole'),
                (0, 1): ('wood', 'wood_dark'), (1, 1): ('wood_light', 'wood'), (2, 1): ('grain', 'rice_light'), (3, 1): ('hole', 'hole'),
                (0, 2): ('iron', 'iron_dark'), (1, 2): ('stone', 'stone_dark'), (2, 2): ('wood_dark', 'wood'), (3, 2): ('red', 'red_light'),
                (0, 3): ('stone_dark', 'hole'), (1, 3): ('stone_light', 'stone'), (2, 3): ('stone', 'stone_light'), (3, 3): ('wood', 'wood_light')},
    'noodle': {(0, 0): ('wood_light', 'wood'), (1, 0): ('wood', 'wood_light'), (2, 0): ('wood_dark', 'wood'), (3, 0): ('wood_pale', 'wood_light'),
               (0, 1): ('white', 'white_shade'), (1, 1): ('noodle', 'cream'), (2, 1): ('wood', 'wood_dark'), (3, 1): ('hole', 'hole'),
               (0, 2): ('wood_dark', 'hole'), (1, 2): ('wood_light', 'wood_pale'), (2, 2): ('cream', 'noodle'), (3, 2): ('onion', 'leaf_deep'),
               (0, 3): ('wood', 'wood_dark'), (1, 3): ('wood_light', 'wood'), (2, 3): ('wood_dark', 'wood'), (3, 3): ('stone', 'stone_dark')},
    'kettle': {(0, 0): ('stone_dark', 'stone_speck'), (1, 0): ('pot', 'pot_light'), (2, 0): ('pot_dark', 'pot'), (3, 0): ('pot_light', 'pot'),
               (0, 1): ('brass', 'brass_dark'), (1, 1): ('fire', 'fire_light'), (2, 1): ('hole', 'hole'), (3, 1): ('pot', 'pot_dark'),
               (0, 2): ('iron', 'iron_dark'), (1, 2): ('pot_dark', 'hole'), (2, 2): ('pot_light', 'iron'), (3, 2): ('stone', 'stone_dark'),
               (0, 3): ('wood', 'wood_dark'), (1, 3): ('pot', 'pot_light'), (2, 3): ('pot_dark', 'pot'), (3, 3): ('matcha', 'matcha_dark')},
    'oven': {(0, 0): ('stone', 'stone_dark'), (1, 0): ('brick', 'brick_dark'), (2, 0): ('brick_light', 'brick'), (3, 0): ('soot', 'soot'),
             (0, 1): ('brick_deep', 'brick_dark'), (1, 1): ('stone_dark', 'stone_speck'), (2, 1): ('brick_dark', 'brick_deep'), (3, 1): ('fire', 'fire_light'),
             (0, 2): ('stone_light', 'stone'), (1, 2): ('brick', 'brick_light'), (2, 2): ('soot', 'brick_deep'), (3, 2): ('brick_light', 'brick'),
             (0, 3): ('brick_deep', 'soot'), (1, 3): ('brick_dark', 'brick'), (2, 3): ('stone', 'stone_light'), (3, 3): ('brick', 'brick_dark')},
}


def tool_texture(name):
    image = new()
    for (col, row), (light, dark) in SWATCHES[name].items():
        for y in range(4):
            for x in range(4):
                key = dark if (x * 5 + y * 3 + col * 7 + row * 11) % 4 == 0 else light
                put(image, col * 4 + x, row * 4 + y, key)
    return image


def part(name, start, end, up, side, bottom=None, front=None, rotation=None):
    bottom, front = bottom or side, front or side
    return _cube(name, start, end, {'north': _tile(*front), 'south': _tile(*side), 'east': _tile(*side), 'west': _tile(*side),
                                    'up': _tile(*up), 'down': _tile(*bottom)}, rotation)


def tool_geometry(name):
    if name == 'mortar':
        tilt = {'angle': 22.5, 'axis': 'z', 'origin': [8, 9, 8]}
        return [part('Foot', (3, 0, 3), (13, 2, 13), (0, 0), (0, 3)),
                part('Body', (2, 2, 2), (14, 9, 14), (1, 0), (1, 0), front=(2, 0)),
                part('RimN', (2, 9, 2), (14, 10, 4), (2, 0), (2, 0)), part('RimS', (2, 9, 12), (14, 10, 14), (2, 0), (2, 0)),
                part('RimW', (2, 9, 4), (4, 10, 12), (2, 0), (2, 0)), part('RimE', (12, 9, 4), (14, 10, 12), (2, 0), (2, 0)),
                part('Inside', (4, 8, 4), (12, 9.4, 12), (0, 1), (0, 1)),
                part('Handle', (7.4, 8, 7.4), (8.6, 15, 8.6), (3, 1), (3, 1), rotation=tilt),
                part('Head', (5.8, 12.5, 5.8), (10.2, 16, 10.2), (1, 2), (1, 2), rotation=tilt)]
    if name == 'grinder':
        return [part('Base', (2, 0, 2), (14, 3, 14), (0, 0), (0, 0)),
                part('Lower', (2.5, 3, 2.5), (13.5, 5.5, 13.5), (1, 0), (1, 0)),
                part('Upper', (2.5, 5.5, 2.5), (13.5, 8, 13.5), (2, 0), (2, 0)),
                part('Hole', (6.5, 8, 6.5), (9.5, 8.3, 9.5), (3, 1), (3, 1)),
                part('Grain', (5, 8, 10), (11, 9, 12.5), (2, 1), (2, 1)),
                part('Post', (12, 8, 7.2), (13.2, 12, 8.4), (0, 1), (0, 1)),
                part('Bar', (8.5, 11.2, 7.2), (13.2, 12.4, 8.4), (1, 1), (1, 1))]
    if name == 'noodle':
        legs = [part('Leg%d' % i, (x, 0, z), (x + 2, 9, z + 2), (2, 0), (2, 0)) for i, (x, z) in enumerate(((2, 3), (12, 3), (2, 11), (12, 11)))]
        return legs + [part('Board', (1, 9, 2), (15, 11, 14), (0, 0), (1, 0)),
                       part('Dough', (3.5, 11, 5), (8.5, 12.5, 10), (0, 1), (0, 1)),
                       part('Noodles', (9.5, 11, 4), (13, 11.7, 12), (1, 1), (1, 1)),
                       part('Pin', (3, 12.6, 11.5), (13, 14, 13), (3, 0), (3, 0)),
                       part('Rail', (1, 8, 2), (15, 9, 3.5), (2, 2), (2, 2))]
    if name == 'kettle':
        return [part('Stand', (3, 0, 3), (13, 2, 13), (0, 0), (0, 0)),
                part('Fire', (5, 2, 1.5), (11, 4, 3), (1, 1), (1, 1)),
                part('PotLow', (3.5, 2, 3.5), (12.5, 5, 12.5), (1, 0), (1, 0)),
                part('PotMid', (2.5, 5, 2.5), (13.5, 10, 13.5), (2, 0), (2, 0)),
                part('Neck', (4, 10, 4), (12, 12, 12), (1, 0), (1, 0)),
                part('Lid', (5, 12, 5), (11, 13, 11), (3, 0), (3, 0)),
                part('Knob', (7.3, 13, 7.3), (8.7, 14.4, 8.7), (0, 1), (0, 1)),
                part('Spout', (12.5, 6, 6.5), (15, 8, 9.5), (2, 0), (2, 0)),
                part('HandleL', (1, 7, 7.2), (3, 10, 8.8), (0, 2), (0, 2)),
                part('Matcha', (6, 12.9, 6), (10, 13.1, 10), (3, 3), (3, 3))]
    if name == 'oven':
        return [part('Base', (1, 0, 1), (15, 2, 15), (0, 0), (0, 0)),
                part('Body', (2, 2, 2), (14, 10, 14), (2, 0), (1, 0), front=(1, 0)),
                part('Mouth', (5, 2, 1.8), (11, 7, 2.1), (3, 0), (3, 0)),
                part('Glow', (6, 2.2, 1.7), (10, 3.8, 2.0), (3, 1), (3, 1)),
                part('Arch', (4.4, 7, 1.8), (11.6, 8, 2.1), (2, 3), (2, 3)),
                part('Roof1', (3, 10, 3), (13, 12, 13), (2, 0), (1, 0)),
                part('Roof2', (5, 12, 5), (11, 14, 11), (2, 0), (1, 0)),
                part('Chimney', (7, 14, 7), (9, 16, 9), (0, 1), (0, 1))]
    raise ValueError('Unknown food tool: ' + name)


def tool_icon(name):
    """道具の、平らなアイコン（リソースパックが平らな版のときと、持ち物の絵）。"""
    image = new()
    if name == 'mortar':
        ellipse(image, (2, 7, 13, 9), 'hole', 'wood_dark')
        for y in range(8, 14):
            for x in range(3, 13): put(image, x, y, 'wood' if x < 9 else 'wood_dark')
        rect(image, 2, 8, 13, 8, 'wood_light')
        for y in range(2, 8): put(image, 11, y, 'wood_light'); put(image, 12, y, 'wood')
        rect(image, 10, 1, 13, 3, 'wood_dark')
    elif name == 'grinder':
        ellipse(image, (1, 10, 14, 14), 'stone', 'stone_dark')
        ellipse(image, (2, 6, 13, 10), 'stone_light', 'stone', 'stone')
        rect(image, 7, 7, 8, 8, 'hole')
        rect(image, 12, 3, 12, 8, 'wood'); rect(image, 8, 3, 12, 3, 'wood_light')
    elif name == 'noodle':
        rect(image, 1, 7, 14, 9, 'wood_light'); rect(image, 1, 9, 14, 9, 'wood')
        for x in (2, 12): rect(image, x, 10, x + 1, 15, 'wood_dark')
        ellipse(image, (3, 4, 7, 6), 'white', 'white_shade')
        rect(image, 9, 5, 13, 6, 'noodle'); rect(image, 3, 2, 12, 3, 'wood')
    elif name == 'kettle':
        ellipse(image, (2, 5, 13, 13), 'pot', 'pot_dark')
        rect(image, 5, 3, 10, 5, 'pot_light'); rect(image, 7, 1, 8, 2, 'brass')
        rect(image, 12, 7, 15, 8, 'pot_light'); rect(image, 0, 6, 1, 9, 'pot_light')
        rect(image, 4, 14, 11, 15, 'stone_dark')
    elif name == 'oven':
        rect(image, 2, 6, 13, 14, 'brick'); rect(image, 2, 14, 13, 15, 'stone')
        ellipse(image, (4, 8, 11, 13), 'soot', 'soot'); rect(image, 6, 11, 9, 12, 'fire')
        rect(image, 4, 3, 11, 5, 'brick_light'); rect(image, 7, 0, 8, 2, 'brick_deep')
        for y in (8, 11): rect(image, 2, y, 3, y, 'brick_dark')
    else:
        raise ValueError('Unknown food tool: ' + name)
    return image


def definition(name):
    return {'model': {'type': 'minecraft:model', 'model': 'hnmt:item/food/' + name}}


def flat(name, texture):
    return {'parent': 'minecraft:item/generated', 'textures': {'layer0': 'hnmt:item/food/' + texture}}


def model3d(textures, elements, display):
    return {'credit': 'HNMT food models', 'texture_size': [SIZE, SIZE], 'gui_light': 'front',
            'textures': {'0': 'hnmt:item/food/' + textures, 'particle': 'hnmt:item/food/' + textures}, 'elements': elements, 'display': display}


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def save_png(name, image):
    path = PACK / 'assets/hnmt/textures/item/food' / (name + '.png')
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def build():
    full = [0, 0, 16, 16]
    for name, _ in ICONS:
        save_png(name, draw(name))
        write_json(PACK / 'assets/hnmt/items/food' / (name + '.json'), definition(name))
        write_json(PACK / 'assets/hnmt/models/item/food' / (name + '.json'), flat(name, name))
    for name, _ in TOOLS:
        save_png(name, tool_texture(name))
        save_png(name + '_icon', tool_icon(name))
        write_json(PACK / 'assets/hnmt/items/food' / (name + '.json'), definition(name))
        write_json(PACK / 'assets/hnmt/models/item/food' / (name + '.json'), flat(name, name + '_icon'))
        write_json(PACK / 'models3d/food' / (name + '.json'), model3d(name, tool_geometry(name), {**MILL, 'fixed': FIXED_PLAIN}))
    planes = [_cube('Plant_a', (-2.6, -1, 8), (18.6, 15, 8), {'north': full, 'south': full}, {'angle': 45, 'axis': 'y', 'origin': [8, 8, 8]}),
              _cube('Plant_b', (-2.6, -1, 8), (18.6, 15, 8), {'north': full, 'south': full}, {'angle': -45, 'axis': 'y', 'origin': [8, 8, 8]})]
    plant_display = {'fixed': FIXED_PLAIN, 'gui': GENERATED['gui'], 'ground': GENERATED['ground'],
                     'firstperson_righthand': GENERATED['firstperson_righthand'], 'thirdperson_righthand': GENERATED['thirdperson_righthand']}
    for name, _ in PLANTS:
        save_png(name, plant(name))
        write_json(PACK / 'assets/hnmt/items/food' / (name + '.json'), definition(name))
        write_json(PACK / 'assets/hnmt/models/item/food' / (name + '.json'), flat(name, name))
        write_json(PACK / 'models3d/food' / (name + '.json'), model3d(name, planes, plant_display))
    print('Wrote %d icons, %d tools, %d plants' % (len(ICONS), len(TOOLS), len(PLANTS)))


def preview():
    target = BUILD / 'food'
    target.mkdir(parents=True, exist_ok=True)
    names = [n for n, _ in ICONS] + [n + '_icon' for n, _ in TOOLS] + [n for n, _ in TOOLS] + [n for n, _ in PLANTS]
    images = [draw(n) for n, _ in ICONS] + [tool_icon(n) for n, _ in TOOLS] + [tool_texture(n) for n, _ in TOOLS] + [plant(n) for n, _ in PLANTS]
    scale, columns = 8, 8
    rows = (len(images) + columns - 1) // columns
    sheet = Image.new('RGBA', (columns * (SIZE * scale + 8) + 8, rows * (SIZE * scale + 8) + 8), (232, 226, 214, 255))
    for i, image in enumerate(images):
        big = image.resize((SIZE * scale, SIZE * scale), Image.NEAREST)
        sheet.paste(big, (8 + (i % columns) * (SIZE * scale + 8), 8 + (i // columns) * (SIZE * scale + 8)), big)
    sheet.save(target / 'preview.png')
    print('Preview: ' + str(target / 'preview.png') + ' (' + ', '.join(names) + ')')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview', action='store_true', help='絵を拡大して並べる')
    args = parser.parse_args()
    preview() if args.preview else build()


if __name__ == '__main__': main()
