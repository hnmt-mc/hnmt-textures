#!/usr/bin/env python3
"""まな板のブロック（台の上にまな板と包丁が乗った形）の絵（16px）と座標を作り、Blockbenchへ渡す。

置いたまな板の本物のブロックは、石化したオークのハーフブロックの2段。Java 版は blockstates でこのモデルにし、
統合版は、同じモデルから、カスタムブロックのジオメトリを作る（make_bedrock.py）。
"""
import argparse
import base64
import json
from PIL import Image
from artwork import PACK, BUILD

SIZE = 16
PALETTE = {
    'side': '#6e4a2c', 'side_grain': '#5a3b22', 'side_light': '#80593a',
    'top': '#a8794a', 'top_grain': '#96693d', 'top_light': '#b88a58',
    'board': '#e0b97a', 'board_grain': '#cfa566', 'board_edge': '#b8914e',
    'metal': '#c9ced4', 'metal_light': '#e6eaee', 'metal_edge': '#9aa1a9',
    'handle': '#4a3020', 'handle_light': '#5e4029',
    'trim': '#4f331d', 'trim_light': '#c29a62',
}
FACES = ('north', 'south', 'east', 'west', 'up', 'down')
# テクスチャの領域（Java の UV。16 × 16 を、このまま使う）
REGIONS = {'side': [0, 0, 8, 8], 'top': [8, 0, 16, 8], 'board': [0, 8, 8, 12], 'metal': [8, 8, 12, 12],
           'handle': [12, 8, 16, 12], 'trim': [0, 12, 16, 15]}


def rgba(key):
    return tuple(bytes.fromhex(PALETTE[key][1:])) + (255,)


def _fill(image, box, pick):
    x0, y0, x1, y1 = box
    for y in range(y0, y1):
        for x in range(x0, x1):
            image.putpixel((x, y), rgba(pick(x - x0, y - y0)))


def texture():
    image = Image.new('RGBA', (SIZE, SIZE), rgba('side'))
    # 台の側面: 縦の板（4画素ごとに継ぎ目）
    _fill(image, (0, 0, 8, 8), lambda x, y: 'side_grain' if x % 4 == 0 else 'side_light' if (x * 3 + y) % 7 == 0 else 'side')
    # 台の上面: 横目
    _fill(image, (8, 0, 16, 8), lambda x, y: 'top_grain' if y % 3 == 1 and x % 5 != 0 else 'top_light' if (x + y * 2) % 9 == 0 else 'top')
    # まな板: 明るい木。縁だけ少し濃く
    _fill(image, (0, 8, 8, 12), lambda x, y: 'board_edge' if y in (0, 3) else 'board_grain' if (x + y) % 4 == 0 else 'board')
    # 包丁の刃
    _fill(image, (8, 8, 12, 12), lambda x, y: 'metal_edge' if y == 3 else 'metal_light' if y == 0 else 'metal')
    # 包丁の柄
    _fill(image, (12, 8, 16, 12), lambda x, y: 'handle_light' if (x + y) % 3 == 0 else 'handle')
    # 台の上の縁（細い帯）
    _fill(image, (0, 12, 16, 15), lambda x, y: 'trim_light' if y == 0 else 'trim')
    return image


def _cube(name, start, end, up, side, down=None):
    faces = {face: {'uv': list(REGIONS[side]), 'texture': '#0'} for face in FACES}
    faces['up']['uv'] = list(REGIONS[up])
    faces['down']['uv'] = list(REGIONS[down or side])
    return {'name': name, 'from': list(start), 'to': list(end), 'faces': faces}


def geometry():
    return [
        _cube('Counter', (0, 0, 0), (16, 10, 16), 'side', 'side'),
        _cube('Top', (0, 10, 0), (16, 12, 16), 'top', 'trim', 'side'),
        _cube('Board', (2, 12, 3), (14, 13.5, 13), 'board', 'board'),
        _cube('Blade', (4, 13.5, 9), (11, 14, 10.5), 'metal', 'metal'),
        _cube('Handle', (11, 13.5, 9), (14.5, 14.8, 10.5), 'handle', 'handle'),
    ]


def build():
    image = texture()
    path = PACK/'assets/hnmt/textures/block/board.png'
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    model = {'credit': 'HNMT cutting board block / Blockbench', 'texture_size': [SIZE, SIZE],
             'textures': {'0': 'hnmt:block/board', 'particle': 'hnmt:block/board'}, 'elements': geometry()}
    return model, path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--textures', action='store_true', help='絵だけを拡大して保存する（Blockbench なしで見た目を確かめる）')
    args = parser.parse_args()
    target = BUILD/'board3d'
    target.mkdir(parents=True, exist_ok=True)
    model, path = build()
    if args.textures:
        big = texture().resize((SIZE*16, SIZE*16), Image.NEAREST)
        big.save(target/'texture-preview.png')
        return
    entry = {'name': 'board', 'label': 'まな板（ブロック）', 'model': model,
             'image': 'data:image/png;base64,' + base64.b64encode(path.read_bytes()).decode()}
    (target/'manifest.json').write_text(json.dumps([entry], ensure_ascii=False, indent=2) + '\n')
    print('Prepared the board block for Blockbench')


if __name__ == '__main__': main()
