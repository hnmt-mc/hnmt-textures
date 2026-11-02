#!/usr/bin/env python3
"""米作りの絵（16px、バニラの作物に近い粗さ）と座標を作り、Blockbenchへ渡す。

田んぼの稲は、バニラの作物と同じ「交差した板2枚」。苗・刈った稲・炊く前の米は、薄い板1枚の平らなアイコン。精米機は直方体4個。
"""
import argparse
import base64
import json
from PIL import Image
from artwork import PACK, BUILD

RICE = [('seedling', '稲の苗'), ('stalk', '刈った稲'), ('grain', '米（炊く前）'), ('mill', '精米機'),
        ('plant_seedling', '田んぼ・苗'), ('plant_growing', '田んぼ・成長中'), ('plant_mature', '田んぼ・実り')]
SIZE = 16
PALETTE = {
    'leaf_dark': '#3f7a33', 'leaf': '#5fa047', 'leaf_light': '#8cc865',
    'straw_dark': '#a8832c', 'straw': '#d4ae45', 'straw_light': '#efd777',
    'root': '#8a5f35', 'band': '#c4552e',
    'stone_light': '#a6a6a6', 'stone': '#8a8a8a', 'stone_dark': '#6c6c6c', 'stone_speck': '#797979',
    'wood': '#8f6a3c', 'wood_light': '#b38b52', 'hole': '#3a3a3a', 'grain': '#f0e6b0',
    'rice_light': '#f7f2de', 'rice': '#e4dbb8', 'rice_shade': '#bfb48c',
    'wood_dark': '#6e4f2b', 'iron_dark': '#5e646b', 'iron': '#8d949b', 'iron_light': '#c4cacf',
    'red': '#b3412b', 'red_light': '#d4623f',
}


def rgba(key):
    return tuple(bytes.fromhex(PALETTE[key][1:])) + (255,)


def _put(image, x, y, key):
    if 0 <= x < SIZE and 0 <= y < SIZE: image.putpixel((x, y), rgba(key))


def _blade(image, x, height, lean, dry, head=False, base=15):
    """根元 (x, base) から height 段の茎を立てる。上のほうで lean 方向へ曲がり、途中に葉を付ける。"""
    stem = ('straw_dark', 'straw') if dry else ('leaf_dark', 'leaf')
    leaf = ('straw', 'straw_light') if dry else ('leaf', 'leaf_light')
    cx = x
    for i in range(height):
        y = base - i
        if i >= height * 0.65 and i % 2 == 0: cx += lean
        _put(image, cx, y, stem[i % 2])
        if i == round(height * 0.45):
            _put(image, cx - 1, y, leaf[0]); _put(image, cx - 2, y - 1, leaf[0])
        if i == round(height * 0.7):
            _put(image, cx + 1, y, leaf[1]); _put(image, cx + 2, y - 1, leaf[1])
    top = base - height + 1
    if head:
        for dx, dy, key in ((0, -1, 'straw_light'), (1, -1, 'straw'), (1, 0, 'straw_light'), (2, 1, 'straw'), (2, 2, 'straw_light')):
            _put(image, cx + dx, top + dy, key)


def _noise(image, box, light, dark, seed):
    x0, y0, x1, y1 = box
    for y in range(y0, y1):
        for x in range(x0, x1):
            _put(image, x, y, dark if (x * 7 + y * 13 + seed) % 5 == 0 else light)


def _grain_pile(image):
    """炊く前の米。白っぽい粒の小さな山（粒は横に長い2画素）。ご飯（湯気のある白い山）とは、粒の見える細かさで見分ける。"""
    rows = {15: range(2, 14), 14: range(3, 13), 13: range(4, 12), 12: range(5, 11), 11: range(6, 10), 10: range(7, 9)}
    for y, xs in rows.items():
        for x in xs:
            key = 'rice_light' if (x // 2 + y) % 2 == 0 else 'rice'
            if y == 15 or x == min(xs) or x == max(xs): key = 'rice_shade' if (x + y) % 2 == 0 else 'rice'
            _put(image, x, y, key)
    for x, y in ((1, 15), (14, 15), (3, 13), (12, 14)):    # こぼれた粒
        _put(image, x, y, 'rice_light')
    for x, y in ((4, 15), (7, 15), (10, 15), (6, 14), (9, 13), (7, 12)):    # 粒の境目
        _put(image, x, y, 'rice_shade')


def texture(name):
    if name not in dict(RICE):
        raise ValueError('Unknown rice item: ' + name)
    image = Image.new('RGBA', (SIZE, SIZE))
    if name == 'mill':
        # 4×4画素の小片を、4×4に並べる。面ごとに、小片を1つ割り当てる（MILL_TILES）。
        for (col, row), (light, dark) in MILL_SWATCHES.items():
            for y in range(4):
                for x in range(4):
                    key = dark if (x * 5 + y * 3 + col * 7 + row * 11) % 4 == 0 else light
                    _put(image, col * 4 + x, row * 4 + y, key)
        return image
    if name == 'grain':
        _grain_pile(image)
        return image
    dry = name in ('stalk', 'plant_mature')
    if name == 'plant_seedling':
        for x, h, lean in ((3, 5, 1), (7, 7, 0), (11, 6, -1)): _blade(image, x, h, lean, False)
    elif name == 'plant_growing':
        for x, h, lean in ((2, 11, 1), (6, 14, 1), (9, 13, -1), (13, 10, -1)): _blade(image, x, h, lean, False)
    elif name == 'plant_mature':
        for x, h, lean in ((2, 11, 1), (6, 14, 1), (9, 13, -1), (13, 10, -1)): _blade(image, x, h, lean, True, head=True)
    else:
        for x, h, lean in ((5, 11 if dry else 7, -1), (8, 13 if dry else 9, 0), (11, 11 if dry else 7, 1)):
            _blade(image, x, h, lean, dry, head=dry, base=13)
        for x in range(5, 12): _put(image, x, 11 if dry else 10, 'band')   # ひも
        for x in (5, 8, 11):
            _put(image, x, 14, 'root')
            _put(image, x - 1, 15, 'root')
    return image


# 精米機の絵: 小片（列, 行）→（ふつうの色, 点の色）
MILL_SWATCHES = {
    (0, 0): ('wood_dark', 'wood'), (1, 0): ('wood', 'wood_light'), (2, 0): ('wood_light', 'wood'), (3, 0): ('stone', 'stone_speck'),
    (0, 1): ('iron', 'iron_dark'), (1, 1): ('iron_light', 'iron'), (2, 1): ('iron_dark', 'iron'), (3, 1): ('hole', 'hole'),
    (0, 2): ('grain', 'iron_light'), (1, 2): ('stone_light', 'stone'), (2, 2): ('wood_dark', 'wood'), (3, 2): ('red', 'red_light'),
    (0, 3): ('iron_dark', 'hole'), (1, 3): ('stone_dark', 'stone_speck'), (2, 3): ('wood', 'wood_dark'), (3, 3): ('red_light', 'red'),
}


def _tile(col, row):
    return [col * 4, row * 4, col * 4 + 4, row * 4 + 4]


def _mill_part(name, start, end, up, side, bottom=None, front=None):
    """精米機の直方体1個。面ごとに小片（列, 行）を割り当てる（前=北は、front）。"""
    bottom, front = bottom or side, front or side
    return _cube(name, start, end, {'north': _tile(*front), 'south': _tile(*side), 'east': _tile(*side), 'west': _tile(*side),
                                    'up': _tile(*up), 'down': _tile(*bottom)})


def _mill_geometry():
    x0, x1, rim = 2, 14, 0.9
    return [
        _mill_part('Base', (0, 0, 0), (16, 2, 16), (1, 3), (3, 0)),                          # 石の受け皿
        _mill_part('Body', (3, 2, 3), (13, 8, 13), (0, 0), (1, 0), front=(2, 0)),            # 木の胴
        _mill_part('HoopLow', (2.6, 3.2, 2.6), (13.4, 4.2, 13.4), (2, 1), (2, 1)),           # 鉄のたが
        _mill_part('HoopHigh', (2.6, 6.2, 2.6), (13.4, 7.2, 13.4), (2, 1), (2, 1)),
        _mill_part('Hopper1', (4, 8, 4), (12, 10, 12), (1, 0), (0, 0)),                      # 漏斗（下から上へ広がる）
        _mill_part('Hopper2', (3, 10, 3), (13, 12, 13), (2, 0), (0, 0)),
        _mill_part('Hopper3', (x0, 12, x0), (x1, 14, x1), (3, 1), (1, 0)),                   # 上の面は穴（暗い）
        _mill_part('RimN', (x0, 14, x0), (x1, 15, x0 + rim), (2, 0), (2, 0)),                # 縁
        _mill_part('RimS', (x0, 14, x1 - rim), (x1, 15, x1), (2, 0), (2, 0)),
        _mill_part('RimW', (x0, 14, x0 + rim), (x0 + rim, 15, x1 - rim), (2, 0), (2, 0)),
        _mill_part('RimE', (x1 - rim, 14, x0 + rim), (x1, 15, x1 - rim), (2, 0), (2, 0)),
        _mill_part('Spout', (6, 2.5, 0.3), (10, 5.5, 3), (2, 3), (2, 3)),                    # 出口
        _mill_part('Tray', (4.5, 2, 0), (11.5, 3, 2), (1, 3), (1, 3)),                  # 受け皿
        _mill_part('Wheel', (13, 3.5, 6), (15, 8.5, 10), (2, 1), (2, 1)),                    # はずみ車
        _mill_part('Handle', (14.5, 7, 7.2), (16, 8.4, 8.8), (3, 2), (3, 2)),                # 取っ手（朱）
    ]


def _cube(name, start, end, faces, rotation=None):
    part = {'name': name, 'from': list(start), 'to': list(end),
            'faces': {face: {'uv': uv, 'texture': '#0'} for face, uv in faces.items()}}
    if rotation: part['rotation'] = rotation
    return part


def _box_faces(top, side, bottom):
    return {'north': side, 'south': side, 'east': side, 'west': side, 'up': top, 'down': bottom}


def geometry(name, image=None):
    if name not in dict(RICE):
        raise ValueError('Unknown rice item: ' + name)
    full = [0, 0, 16, 16]
    if name == 'mill':
        return _mill_geometry()
    if name.startswith('plant_'):
        # バニラの作物と同じ。幅いっぱいの板を、45度ずつ振って交差させる（足元は耕地の面より1下まで伸ばす）。
        def plane(label, angle):
            return _cube(label, (-2.6, -1, 8), (18.6, 15, 8), {'north': full, 'south': full},
                         {'angle': angle, 'axis': 'y', 'origin': [8, 8, 8]})
        return [plane('Plant_a', 45), plane('Plant_b', -45)]
    return [_cube('Sprite', (0, 0, 7.5), (16, 16, 8.5), {'north': full, 'south': full})]


# バニラの item/generated と同じ持たせ方（苗と稲は、ふつうのアイテムのように見せる）
GENERATED = {'gui': {'rotation': [0, 0, 0], 'translation': [0, 0, 0], 'scale': [1, 1, 1]},
             'ground': {'rotation': [0, 0, 0], 'translation': [0, 2, 0], 'scale': [0.5, 0.5, 0.5]},
             'fixed': {'rotation': [0, 180, 0], 'translation': [0, 0, 0], 'scale': [0.5, 0.5, 0.5]},
             'thirdperson_righthand': {'rotation': [0, 0, 0], 'translation': [0, 3, 1], 'scale': [0.55, 0.55, 0.55]},
             'firstperson_righthand': {'rotation': [0, -90, 25], 'translation': [1.13, 3.2, 1.13], 'scale': [0.68, 0.68, 0.68]}}
FIXED_PLAIN = {'rotation': [0, 0, 0], 'translation': [0, 0, 0], 'scale': [1, 1, 1]}
MILL = {'gui': {'rotation': [30, 225, 0], 'translation': [0, -1, 0], 'scale': [0.62, 0.62, 0.62]},
        'ground': {'translation': [0, 3, 0], 'scale': [0.4, 0.4, 0.4]},
        'firstperson_righthand': {'rotation': [0, -35, 0], 'translation': [0, 2, 0], 'scale': [0.55, 0.55, 0.55]},
        'thirdperson_righthand': {'rotation': [75, 45, 0], 'translation': [0, 2, 0], 'scale': [0.45, 0.45, 0.45]}}


def display(name):
    """fixed（ItemDisplay）は、回転・移動・拡大なし。田んぼの稲と精米機は、世界に出すときこの形で置く。"""
    if name.startswith('plant_'):
        return {'fixed': FIXED_PLAIN, 'gui': GENERATED['gui'], 'ground': GENERATED['ground'],
                'firstperson_righthand': GENERATED['firstperson_righthand'],
                'thirdperson_righthand': GENERATED['thirdperson_righthand']}
    if name == 'mill':
        return {**MILL, 'fixed': FIXED_PLAIN}
    return GENERATED


def build(name):
    image = texture(name)
    parts = geometry(name, image)
    path = PACK/'assets/hnmt/textures/item/rice'/f'{name}.png'
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    model = {'credit': 'HNMT rice models / Blockbench', 'texture_size': [SIZE, SIZE], 'gui_light': 'front',
             'textures': {'0': f'hnmt:item/rice/{name}', 'particle': f'hnmt:item/rice/{name}'},
             'elements': parts, 'display': display(name)}
    for folder, data in [('items', {'model': {'type': 'minecraft:model', 'model': f'hnmt:item/rice/{name}'}}),
                         ('models/item', {'parent': 'minecraft:item/generated', 'textures': {'layer0': f'hnmt:item/rice/{name}'}})]:
        out = PACK/'assets/hnmt'/folder/'rice'/f'{name}.json'
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    return model, path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review', action='store_true', help='Blockbenchのプレビュー一覧を作る')
    parser.add_argument('--textures', action='store_true', help='絵だけを拡大して並べる（Blockbench なしで見た目を確かめる）')
    args = parser.parse_args()
    target = BUILD/'rice3d'
    target.mkdir(parents=True, exist_ok=True)
    if args.textures:
        scale = 12
        sheet = Image.new('RGBA', (len(RICE)*SIZE*scale, SIZE*scale), (232, 226, 214, 255))
        for i, (name, _) in enumerate(RICE):
            big = texture(name).resize((SIZE*scale, SIZE*scale), Image.NEAREST)
            sheet.paste(big, (i*SIZE*scale, 0), big)
        sheet.save(target/'textures-preview.png')
        return
    if args.review:
        from artwork import sheet
        images = [Image.open(target/(n+'-preview.png')).convert('RGBA') for n, _ in RICE]
        boxes = [im.getbbox() for im in images]
        bounds = (min(b[0] for b in boxes)-12, min(b[1] for b in boxes)-12,
                  max(b[2] for b in boxes)+12, max(b[3] for b in boxes)+12)
        size = max(bounds[2]-bounds[0], bounds[3]-bounds[1])
        entries = []
        for image, (name, label) in zip(images, RICE):
            crop = image.crop(bounds)
            square = Image.new('RGBA', (size, size))
            square.paste(crop, ((size-crop.width)//2, (size-crop.height)//2))
            entries.append((square, label, name))
        sheet(entries, 'rice3d/contact-sheet.png', columns=3, tile=256)
        return
    entries = []
    for name, label in RICE:
        model, path = build(name)
        entries.append({'name': name, 'label': label, 'model': model, 'image': 'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()})
    (target/'manifest.json').write_text(json.dumps(entries, ensure_ascii=False, indent=2)+'\n')
    print('Prepared %d rice models for Blockbench' % len(RICE))


if __name__ == '__main__': main()
