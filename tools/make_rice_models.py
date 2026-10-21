#!/usr/bin/env python3
"""米作りの絵（16px、バニラの作物に近い粗さ）と座標を作り、Blockbenchへ渡す。

田んぼの稲は、バニラの作物と同じ「交差した板2枚」。苗と刈った稲は、薄い板1枚の平らなアイコン。石臼は直方体4個。
"""
import argparse
import base64
import json
from PIL import Image
from artwork import PACK, BUILD

RICE = [('seedling', '稲の苗'), ('stalk', '刈った稲'), ('mill', '石臼'),
        ('plant_seedling', '田んぼ・苗'), ('plant_growing', '田んぼ・成長中'), ('plant_mature', '田んぼ・実り')]
SIZE = 16
PALETTE = {
    'leaf_dark': '#3f7a33', 'leaf': '#5fa047', 'leaf_light': '#8cc865',
    'straw_dark': '#a8832c', 'straw': '#d4ae45', 'straw_light': '#efd777',
    'root': '#8a5f35', 'band': '#c4552e',
    'stone_light': '#a6a6a6', 'stone': '#8a8a8a', 'stone_dark': '#6c6c6c', 'stone_speck': '#797979',
    'wood': '#8f6a3c', 'wood_light': '#b38b52', 'hole': '#3a3a3a', 'grain': '#f0e6b0',
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


def texture(name):
    if name not in dict(RICE):
        raise ValueError('Unknown rice item: ' + name)
    image = Image.new('RGBA', (SIZE, SIZE))
    if name == 'mill':
        # 領域ごとに面へ割り当てる: 左上=上石の上面、右上=上石の側面、左下=土台、右下の4つ=木・木の明るい面・穴・米粒
        _noise(image, (0, 0, 8, 8), 'stone_light', 'stone', 1)
        _noise(image, (8, 0, 16, 8), 'stone', 'stone_speck', 2)
        _noise(image, (0, 8, 8, 16), 'stone_dark', 'stone_speck', 3)
        for x in range(8, 12):
            for y in range(8, 12): _put(image, x, y, 'wood' if (x + y) % 3 else 'wood_light')
        for x in range(12, 16):
            for y in range(8, 12): _put(image, x, y, 'wood_light')
        for x in range(8, 12):
            for y in range(12, 16): _put(image, x, y, 'hole')
        for x in range(12, 16):
            for y in range(12, 16): _put(image, x, y, 'grain')
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
        base = [0, 8, 8, 16]
        top, side = [0, 0, 8, 8], [8, 0, 16, 8]
        return [
            _cube('Base', (1, 0, 1), (15, 3, 15), _box_faces(base, base, base)),
            _cube('Top', (2, 3, 2), (14, 7, 14), _box_faces(top, side, side)),
            _cube('Hopper', (6.5, 7, 6.5), (9.5, 7.4, 9.5), _box_faces([8, 12, 12, 16], [8, 12, 12, 16], [8, 12, 12, 16])),
            _cube('Handle', (11.25, 7, 7.25), (12.75, 12, 8.75), _box_faces([12, 8, 16, 12], [8, 8, 12, 12], [8, 8, 12, 12])),
        ]
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
MILL = {'gui': {'rotation': [30, 225, 0], 'translation': [0, -1, 0], 'scale': [0.8, 0.8, 0.8]},
        'ground': {'translation': [0, 3, 0], 'scale': [0.4, 0.4, 0.4]},
        'firstperson_righthand': {'rotation': [0, -35, 0], 'translation': [0, 2, 0], 'scale': [0.55, 0.55, 0.55]},
        'thirdperson_righthand': {'rotation': [75, 45, 0], 'translation': [0, 2, 0], 'scale': [0.45, 0.45, 0.45]}}


def display(name):
    """fixed（ItemDisplay）は、回転・移動・拡大なし。田んぼの稲と石臼は、世界に出すときこの形で置く。"""
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
    print('Prepared 6 rice models for Blockbench')


if __name__ == '__main__': main()
