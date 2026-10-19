#!/usr/bin/env python3
"""料理32品の器と盛り付けを組み、Blockbenchに渡す編集データを作る。"""

import base64
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw
from artwork import PACK, BUILD, DISHES

TEXTURES_3D = PACK / 'assets/hnmt/textures/item/dish3d'
PROJECTS = PACK / 'blockbench/dish'
DISPLAY = {
    'gui': {'rotation': [35, 225, 0], 'translation': [0, 1, 0], 'scale': [0.94] * 3},
    'ground': {'rotation': [0, 0, 0], 'translation': [0, 2, 0], 'scale': [0.5] * 3},
    'fixed': {'rotation': [0, 180, 0], 'translation': [0, 0, -1], 'scale': [0.85] * 3},
    'firstperson_righthand': {'rotation': [0, -35, 0], 'translation': [0, 1, 0], 'scale': [0.65] * 3},
    'thirdperson_righthand': {'rotation': [75, 45, 0], 'translation': [0, 2, 0], 'scale': [0.55] * 3},
}
TILES = {
    'ceramic': (0, 0, 8, 8), 'rim': (8, 0, 16, 8), 'rice': (16, 0, 24, 8),
    'leaf': (24, 0, 28, 4), 'roe': (24, 4, 28, 8), 'roe_top': (28, 4, 32, 8), 'fish': (0, 8, 16, 16),
    'skin': (16, 8, 24, 16), 'broth': (24, 8, 32, 16), 'nori': (0, 16, 8, 24),
    'plate': (8, 16, 16, 24), 'fish_edge': (16, 16, 24, 24), 'radish': (24, 16, 32, 24),
    'foot': (0, 24, 8, 32), 'blue': (8, 24, 16, 32), 'glaze': (16, 24, 24, 32),
}
FISH = {
    'salmon': ('#ef985f', '#ffd1a2', '#c76643'),
    'maguro': ('#c44b50', '#f39a92', '#8a303e'),
    'tai': ('#efc1b4', '#fff1df', '#bf807d'),
    'hirame': ('#e9dfc9', '#fff8e6', '#bfbbb2'),
    'hamachi': ('#e6bdad', '#ffead4', '#b98179'),
    'buri': ('#ddb29a', '#ffe8cd', '#ae7564'),
    'ika': ('#eee8d9', '#fff9ef', '#c4bebc'),
    'kanpachi': ('#e4b8a2', '#ffebcf', '#b77565'),
    'saba': ('#c9b8b0', '#f3dfce', '#748b9b'),
    'kohada': ('#b9c9c7', '#eaf0dd', '#5f7d88'),
    'unagi': ('#a76238', '#e6ad65', '#55392b'),
    'konoshiro': ('#c2a374', '#eac894', '#6f675b'),
    'ikura': ('#e77928', '#ffc35b', '#ad4125'),
}


def atlas(name):
    kind, fish = name.split('_', 1)
    flesh, fat, shadow = FISH[fish]
    cooked = kind in ('grill', 'simmer')
    if cooked:
        flesh, fat, shadow = {
            'salmon': ('#d88b58', '#ffd2a0', '#8e5437'),
            'buri': ('#b97b45', '#e9b872', '#70472f'),
            'saba': ('#a78b70', '#dbc7a2', '#566976'),
            'hirame': ('#b38e61', '#ecd3a3', '#76624d'),
            'konoshiro': ('#ab9b7e', '#e2caa0', '#5e655e'),
            'unagi': FISH['unagi'],
        }[fish]
    elif kind == 'soup':
        flesh, fat, shadow = '#eee3cd', '#fff4df', '#c2b19a'
    image = Image.new('RGBA', (32, 32), '#e7dfcf')
    draw = ImageDraw.Draw(image)
    fills = {'ceramic': '#d8dfd6', 'rim': '#f4f0df', 'rice': '#f4ead1', 'leaf': '#5c8855',
             'roe': '#e56729', 'roe_top': '#ef7830', 'fish': flesh, 'skin': '#657c86', 'broth': '#ad7441',
             'nori': '#334c38', 'plate': '#eee9d8', 'fish_edge': shadow, 'radish': '#f8f4e7',
             'foot': '#b6c2bf', 'blue': '#4b7284', 'glaze': '#7c452d'}
    for tile, box in TILES.items():
        x0, y0, x1, y1 = box
        draw.rectangle((x0, y0, x1 - 1, y1 - 1), fill=fills[tile])
    # 陶器の縁は紺の細線、白米は短い粒、魚には筋と脂を描く。
    draw.line((8, 1, 15, 1), fill='#4b7284')
    draw.line((8, 6, 15, 6), fill='#76939a')
    draw.line((0, 0, 7, 0), fill='#f6f0df')
    draw.line((0, 7, 7, 7), fill='#a9b9ba')
    for x, y in [(17, 1), (20, 2), (22, 5), (17, 6), (19, 4), (21, 0)]:
        draw.line((x, y, x + 1, y), fill='#fff9e9')
        if y < 6:
            draw.point((x, y + 1), fill='#d8c9a9')
    for x in (1, 5, 9, 13):
        draw.line((x, 8, min(15, x + 3), 15), fill=fat)
        draw.line((x + 1, 8, min(15, x + 4), 15), fill=fat if fish == 'salmon' else flesh)
    draw.line((0, 15, 15, 15), fill=shadow)
    for x in (17, 20, 23):
        draw.line((x, 9, x - 1, 14), fill='#b8c9c4')
    if cooked:
        for x in (2, 6, 10, 14):
            draw.line((x, 9, x - 1, 14), fill=shadow)
        draw.line((1, 9, 13, 9), fill=fat)
    if fish == 'unagi':
        for x in (3, 7, 11):
            draw.line((x, 9, x, 14), fill=shadow)
    draw.line((25, 4, 27, 4), fill='#fa9a49')
    draw.point((25, 5), fill='#ffd18a')
    draw.line((24, 7, 27, 7), fill='#b63b24')
    draw.point((29, 5), fill='#ffd18a')
    draw.line((28, 7, 31, 7), fill='#d45424')
    draw.line((26, 0, 26, 3), fill='#a4b779')
    draw.line((24, 12, 31, 12), fill='#c99559')
    return image


def cube(parts, name, center, size, side, top=None, angle=0):
    low = [round(c - s / 2, 4) for c, s in zip(center, size)]
    high = [round(c + s / 2, 4) for c, s in zip(center, size)]
    faces = {face: {'uv': [v / 2 for v in TILES[top if face == 'up' and top else side]], 'texture': '#0'}
             for face in ('north', 'east', 'south', 'west', 'up', 'down')}
    part = {'name': name, 'from': low, 'to': high, 'faces': faces}
    if angle:
        part['rotation'] = {'angle': angle, 'axis': 'y', 'origin': [round(c, 5) for c in center], 'rescale': False}
    parts.append(part)


def ring(parts, tag, radius, y, height, wall=0.5, side='ceramic', top='rim'):
    """8枚の側板で中が空いた八角形を作る。箱や塊を器の代わりにしない。"""
    length = radius * (math.sqrt(2) - 1) * 2 + 0.16
    for sign in (-1, 1):
        cube(parts, f'vessel_{tag}_z{sign}', (8, y + height / 2, 8 + sign * radius), (length, height, wall), side, top)
        cube(parts, f'vessel_{tag}_x{sign}', (8 + sign * radius, y + height / 2, 8), (wall, height, length), side, top)
    diagonal = radius / math.sqrt(2)
    for sx in (-1, 1):
        for sz in (-1, 1):
            cube(parts, f'vessel_{tag}_corner{sx}_{sz}', (8 + sx * diagonal, y + height / 2, 8 + sz * diagonal),
                 (length, height, wall), side, top, 45 if sx == sz else -45)


def fill(parts, tag, y, height, width, depth, material, top=None):
    cube(parts, tag + '_a', (8, y, 8), (width, height, depth * 0.72), material, top)
    cube(parts, tag + '_b', (8, y - 0.01, 8), (width * 0.72, height, depth), material, top)


def octagonal_fill(parts, tag, y, height, radius, material):
    # 器の内側まで汁や米を敷き、十字形の表面にならないよう9本の帯で埋める。
    step = radius * 2 / 9
    for i in range(9):
        z = -radius + step * (i + 0.5)
        half_width = min(radius, radius * math.sqrt(2) - abs(z) - step / 2)
        cube(parts, f'{tag}_{i}', (8, y, 8 + z), (half_width * 2, height, step), material)


def plate(parts, cooked=False):
    ring(parts, 'foot', 2.5, 0.65, 0.5, 0.45, 'foot', 'foot')
    fill(parts, 'vessel_plate', 1.25, 0.4, 10.3, 9.2, 'ceramic', 'plate')
    ring(parts, 'shoulder', 4.85, 1.1, 0.45, 0.7, 'ceramic', 'plate')
    ring(parts, 'lip', 5.25, 1.5, 0.4, 0.5, 'ceramic', 'rim')
    if cooked:
        fill(parts, 'food_sauce', 1.51, 0.1, 7.6, 6.4, 'broth')


def bowl(parts, soup=False):
    ring(parts, 'foot', 2.35, 0.55, 0.6, 0.5, 'foot', 'foot')
    fill(parts, 'vessel_floor', 1.3, 0.55, 6, 5.7, 'ceramic', 'plate')
    for index, (radius, y, height) in enumerate([(3.15, 1.3, 1.2), (4.0, 2.45, 1.2), (4.8, 3.6, 1.2), (5.3, 4.75, 0.95)]):
        ring(parts, f'wall{index}', radius, y, height, 1.1, 'ceramic', 'plate')
    ring(parts, 'lip', 5.4, 5.65, 0.4, 0.5, 'ceramic', 'rim')
    if soup:
        octagonal_fill(parts, 'food_broth', 5.2, 0.2, 4.4, 'broth')
    else:
        octagonal_fill(parts, 'food_rice', 4.8, 0.65, 4.3, 'rice')


def leaf(parts, x, y, z, index):
    cube(parts, f'garnish_leaf{index}', (x, y, z), (2.8, 0.15, 1.4), 'leaf', angle=45)
    cube(parts, f'garnish_stem{index}', (x, y + 0.1, z), (0.25, 0.12, 2.5), 'leaf', angle=45)


def fish_piece(parts, name, center, length=3.6, width=1.6, angle=0, skin=False):
    x, y, z = center
    cube(parts, 'food_' + name, (x, y, z), (length, 0.75, width), 'fish_edge', 'skin' if skin else 'fish', angle)
    cube(parts, 'food_' + name + '_ridge', (x, y + 0.4, z), (length - 0.5, 0.2, width - 0.3), 'fish', 'fish', angle)


def geometry(name):
    kind, fish = name.split('_', 1)
    parts = []
    if kind == 'nigiri':
        plate(parts)
        for i, (x, z) in enumerate([(6.0, 6.5), (9.7, 9.0)]):
            cube(parts, f'food_rice{i}_base', (x, 1.95, z), (3.0, 0.5, 1.9), 'rice')
            cube(parts, f'food_rice{i}_middle', (x, 2.35, z), (3.5, 0.6, 2.3), 'rice')
            cube(parts, f'food_rice{i}_mound', (x, 2.7, z), (2.9, 0.4, 1.85), 'rice')
            neta_top = 'skin' if fish in ('kohada', 'saba') else 'fish'
            cube(parts, f'food_neta{i}_center', (x, 3.1, z), (3.0, 0.45, 2.35), 'fish_edge', neta_top)
            for sign in (-1, 1):
                cube(parts, f'food_neta{i}_end{sign}', (x + sign * 1.75, 2.95, z), (0.5, 0.35, 2.15), 'fish_edge', neta_top)
            if fish == 'unagi':
                cube(parts, f'food_nori{i}', (x, 3.36, z), (0.65, 0.1, 2.4), 'nori')
        leaf(parts, 10.8, 1.9, 5.2, 0)
    elif kind == 'sashimi':
        plate(parts)
        for i in range(6):
            cube(parts, f'garnish_radish{i}', (6.1 + i * 0.65, 1.85 + (i % 2) * 0.13, 9.8), (0.25, 0.22, 3.0), 'radish', angle=22.5 if i % 2 else -22.5)
        leaf(parts, 9.7, 1.8, 6, 0)
        for i in range(5):
            fish_piece(parts, f'slice{i}', (5.1 + i * 1.38, 2.35 + (i % 2) * 0.1, 7.3 + abs(i - 2) * 0.3), 2.0, 3.2, 22.5 if i < 2 else -22.5 if i > 2 else 0)
        cube(parts, 'garnish_wasabi', (10.9, 1.95, 10.6), (1.0, 0.5, 1.0), 'leaf')
    elif kind == 'don':
        bowl(parts)
        if fish == 'ikura':
            index = 0
            for row in range(-3, 4):
                for col in range(-3, 4):
                    if col * col + row * row > 10:
                        continue
                    x, z = 8 + col * 1.02 + (row % 2) * 0.14, 8 + row * 1.02
                    y = 5.35 + (0.2 if (col + row) % 3 == 0 else 0)
                    cube(parts, f'food_roe{index}', (x, y, z), (0.92, 0.62, 0.92), 'roe', 'roe_top')
                    cube(parts, f'food_roe{index}_cap', (x - 0.04, y + 0.37, z - 0.04), (0.72, 0.14, 0.72), 'roe', 'roe_top')
                    index += 1
        else:
            for i in range(5):
                fish_piece(parts, f'topping{i}', (5.2 + i * 1.4, 5.45, 7.7 + abs(i - 2) * 0.4), 1.8, 4.4, 22.5 if i < 2 else -22.5 if i > 2 else 0)
        leaf(parts, 10.5, 5.5, 5.2, 0)
        for i in range(3):
            cube(parts, f'garnish_nori{i}', (6.5 + i * 0.7, 5.9, 8.7), (0.18, 0.15, 2.1), 'nori', angle=-22.5)
    elif kind == 'soup':
        bowl(parts, True)
        for i, (x, z) in enumerate([(6.2, 7.0), (9.1, 8.7), (6.6, 9.6)]):
            fish_piece(parts, f'chunk{i}', (x, 5.35, z), 2.4, 1.8, angle=22.5)
        for i, (x, z) in enumerate([(9.2, 6.2), (10.5, 9), (7.8, 7.8)]):
            cube(parts, f'garnish_wakame{i}', (x, 5.4, z), (1.0, 0.2, 1.8), 'nori', angle=45)
        for i in range(6):
            cube(parts, f'garnish_negi{i}', (5.5 + i * 0.8, 5.6, 7 + (i % 3)), (0.35, 0.3, 0.35), 'leaf')
    else:
        plate(parts, True)
        if fish == 'unagi':
            for i in range(3):
                fish_piece(parts, f'fillet{i}', (5.2 + i * 2.7, 2.2, 8), 2.5, 3.7)
        elif fish in ('hirame', 'konoshiro'):
            fish_piece(parts, 'body', (8, 2.2, 8), 6.5, 4.3 if fish == 'hirame' else 2.8)
            cube(parts, 'food_tail_a', (3.9, 2.0, 7.5), (2.2, 0.4, 0.8), 'skin', angle=22.5)
            cube(parts, 'food_tail_b', (3.9, 2.0, 8.5), (2.2, 0.4, 0.8), 'skin', angle=-22.5)
        else:
            fish_piece(parts, 'fillet0', (6.3, 2.25, 7), 4.0, 3.0, 22.5)
            fish_piece(parts, 'fillet1', (9.6, 2.3, 9), 3.8, 2.7, -22.5)
        leaf(parts, 10.6, 1.8, 5.3, 0)
        for i in range(3):
            cube(parts, f'garnish_ginger{i}', (5.6 + i * 0.45, 1.85, 10.8), (0.3, 0.25, 1.3), 'radish', angle=22.5)
    return parts


def build(name):
    if name not in dict(DISHES):
        raise ValueError('Unknown dish: ' + name)
    TEXTURES_3D.mkdir(parents=True, exist_ok=True)
    image = atlas(name)
    image.save(TEXTURES_3D / (name + '.png'))
    texture = 'hnmt:item/dish3d/' + name
    data = {'credit': 'HNMT food models / Blockbench', 'texture_size': [32, 32], 'gui_light': 'front',
            'textures': {'0': texture, 'particle': texture}, 'elements': geometry(name), 'display': DISPLAY}
    path = PACK / 'models3d/dish' / (name + '.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    return data


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review', action='store_true', help='既存のBlockbenchプレビューから一覧だけを生成する')
    args = parser.parse_args()
    target = BUILD / 'food3d'
    target.mkdir(parents=True, exist_ok=True)
    if args.review:
        from artwork import sheet
        images = [(Image.open(target / (name + '-preview.png')), label, name) for name, label in DISHES]
        sheet(images, 'food3d/contact-sheet.png', columns=8, tile=168)
        selected = ('don_ikura', 'don_salmon', 'nigiri_salmon', 'sashimi_maguro', 'grill_unagi', 'soup_tai')
        sheet([entry for entry in images if entry[2] in selected], 'food3d/preview-selection.png', columns=3, tile=256)
        return
    manifest = []
    for name, label in DISHES:
        data = build(name)
        manifest.append({'name': name, 'label': label, 'model': data,
                         'image': 'data:image/png;base64,' + base64.b64encode((TEXTURES_3D / (name + '.png')).read_bytes()).decode()})
    (target / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False))
    print(f'Generated {len(manifest)} 3D dish recipes; original 2D textures unchanged')


if __name__ == '__main__':
    main()
