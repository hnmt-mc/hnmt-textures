#!/usr/bin/env python3
"""銃（火縄銃・短筒）の3Dモデルと、その絵（小さなタイル集）を作る。Blockbench で開ける、箱を組んだ Minecraft のモデル（JSON）。

銃身は、モデルの北（-z）へ向け、上を +y、右を +x にする。手に持ったときは、display の回転なしで、銃口が前へ向く。
持ち物の欄・落とした物・額縁では、平らなアイコン（make_guns.py の絵）を使い、手に持ったとき・身につけたときだけ、この3Dモデルを使う
（items の定義が、display_context で切り替える）。統合版は、平らなアイコンのままにする。

  python3 tools/make_gun_models.py   モデルとタイル集を書き出す（make_guns.py からも呼ばれる）
"""
import json
import math
import random
from PIL import Image
from artwork import PACK

ATLAS = 64
TILE = 16
# タイルの置き場所（列, 行）。絵は、描いた色の面を、箱の面に貼る
TILES = {'wood': (0, 0), 'wood_dark': (1, 0), 'steel': (2, 0), 'steel_dark': (3, 0),
         'brass': (0, 1), 'brass_dark': (1, 1), 'cord': (2, 1), 'ember': (3, 1),
         'iron': (0, 2), 'steel_light': (1, 2), 'wood_light': (2, 2)}
TEXTURE = 'hnmt:item/gun_model/atlas'


def paint_atlas():
    rng = random.Random(11)
    image = Image.new('RGBA', (ATLAS, ATLAS), (0, 0, 0, 0))
    def fill(name, base, noise=0, streak=0, shade=0):
        col, row = TILES[name]
        for y in range(TILE):
            for x in range(TILE):
                v = rng.randint(-noise, noise) + (streak if (y % 4 == 1) else 0) + int(shade * (y - 8) / 8)
                image.putpixel((col * TILE + x, row * TILE + y), tuple(max(0, min(255, c + v)) for c in base) + (255,))
    fill('wood', (122, 74, 38), noise=7, streak=-18)                # 木目（横の筋）
    fill('wood_dark', (74, 44, 24), noise=6, streak=-12)
    fill('wood_light', (168, 112, 60), noise=7, streak=-14)
    fill('steel', (86, 96, 114), noise=5, shade=-14)
    fill('steel_dark', (47, 54, 68), noise=4)
    fill('steel_light', (143, 156, 176), noise=5, shade=-10)
    fill('brass', (201, 160, 60), noise=6, shade=-12)
    fill('brass_dark', (138, 106, 30), noise=5)
    fill('cord', (138, 132, 114), noise=8, streak=-16)
    fill('iron', (30, 34, 44), noise=3)
    col, row = TILES['ember']
    for y in range(TILE):                                           # 火縄の先の、燃える光（中心が明るい）
        for x in range(TILE):
            d = math.hypot(x - 7.5, y - 7.5) / 8
            image.putpixel((col * TILE + x, row * TILE + y), (255, int(210 - 150 * min(1, d)), int(90 - 70 * min(1, d)), 255))
    return image


def uv(tile):
    col, row = TILES[tile]
    unit = 16 / (ATLAS / TILE)          # モデルの uv は 0〜16。タイル1枚は 4
    return [col * unit + 0.1, row * unit + 0.1, col * unit + unit - 0.1, row * unit + unit - 0.1]


def box(x1, y1, z1, x2, y2, z2, side, top=None, end=None, rotate=None, emission=None):
    """箱（from, to）。side は側面と下、top は上面、end は前後の端の面のタイル。rotate は (軸, 角度, 原点)。"""
    top, end = top or side, end or side
    faces = {'north': end, 'south': end, 'east': side, 'west': side, 'up': top, 'down': side}
    element = {'from': [x1, y1, z1], 'to': [x2, y2, z2], 'faces': {k: {'uv': uv(v), 'texture': '#0'} for k, v in faces.items()}}
    if rotate: element['rotation'] = {'axis': rotate[0], 'angle': rotate[1], 'origin': list(rotate[2])}
    if emission: element['light_emission'] = emission
    return element


def long_gun(loaded):
    e = []
    by = 9.5                                              # 銃身の中心の高さ
    e.append(box(7.25, by - 0.8, -14, 8.75, by + 0.8, 19, 'steel', top='steel_light', end='steel_dark'))                  # 銃身（八角: 2本の箱を45°重ねる）
    e.append(box(7.25, by - 0.8, -14, 8.75, by + 0.8, 19, 'steel', top='steel_light', end='steel_dark', rotate=('z', 45, (8, by, 0))))
    e.append(box(6.85, by - 1.15, -14, 9.15, by + 1.15, -12.4, 'steel_dark'))                                             # 銃口の広がり（朝顔）
    e.append(box(6.75, by - 1.25, -14.5, 9.25, by + 1.25, -13.9, 'brass', top='brass_dark'))                              # 銃口の口金
    for z in (-3.5, 5.0, 12.5):                                                                                           # 真鍮の帯（竹の節）
        e.append(box(6.8, by - 1.2, z, 9.2, by + 1.2, z + 1.0, 'brass', top='brass_dark'))
    e.append(box(7.7, by + 0.8, -12.8, 8.3, by + 1.4, -11.8, 'brass'))                                                    # 照星（台・柱・玉）
    e.append(box(7.85, by + 1.4, -12.4, 8.15, by + 2.2, -12.0, 'iron'))
    e.append(box(7.7, by + 2.1, -12.5, 8.3, by + 2.6, -11.9, 'brass', top='steel_light'))
    e.append(box(7.2, by + 0.8, 17.7, 8.8, by + 1.1, 19.3, 'iron'))                                                       # 照門（台と2本の柱）
    e.append(box(7.2, by + 1.1, 18.1, 7.65, by + 1.9, 18.7, 'iron'))
    e.append(box(8.35, by + 1.1, 18.1, 8.8, by + 1.9, 18.7, 'iron'))
    e.append(box(7.1, 7.2, 15, 8.9, 10.0, 24, 'wood', top='wood_light', end='wood_dark'))                                 # 銃床（短く、細く）
    e.append(box(7.3, 7.0, 24, 8.7, 9.6, 31, 'wood', top='wood_light', end='wood_dark'))
    e.append(box(7.4, 6.5, 26.5, 8.6, 7.1, 31, 'wood_dark'))
    e.append(box(7.3, 7.6, 6, 8.7, 8.7, 15, 'wood', top='wood_light', end='wood_dark'))                                    # 銃身の下の台
    e.append(box(7.6, 7.2, -10, 8.4, 7.8, 6, 'wood_light'))                                                                # 込め矢
    e.append(box(6.55, 8.4, 15, 7.15, 10.4, 20.5, 'brass', top='brass_dark', end='brass_dark'))                           # 側板
    e.append(box(8.85, 8.4, 15, 9.45, 10.4, 20.5, 'brass', top='brass_dark', end='brass_dark'))
    e.append(box(6.9, by + 0.8, 18.1, 7.5, by + 1.2, 19.4, 'brass_dark'))                                                  # 火皿
    e.append(box(6.45, 10.2, 15.5, 6.8, 11.9, 16.3, 'iron'))                                                               # 蛇杖（火縄を挟む腕）
    e.append(box(6.45, 11.5, 13.6, 6.8, 12.0, 16.3, 'iron'))
    e.append(box(6.5, 11.6, 12.8, 6.75, 12.0, 13.8, 'cord'))                                                               # 火縄
    if loaded: e += ember(6.35, 11.4, 12.2)
    return e


def short_gun(loaded):
    e = []
    by = 9.5
    e.append(box(7.2, by - 0.9, -4, 8.8, by + 0.9, 13, 'steel', top='steel_light', end='steel_dark'))
    e.append(box(7.2, by - 0.9, -4, 8.8, by + 0.9, 13, 'steel', top='steel_light', end='steel_dark', rotate=('z', 45, (8, by, 0))))
    e.append(box(6.8, by - 1.25, -4, 9.2, by + 1.25, -2.4, 'steel_dark'))
    e.append(box(6.7, by - 1.35, -4.5, 9.3, by + 1.35, -3.9, 'brass', top='brass_dark'))
    for z in (3.0, 9.0):
        e.append(box(6.75, by - 1.3, z, 9.25, by + 1.3, z + 1.0, 'brass', top='brass_dark'))
    e.append(box(7.7, by + 0.9, -3.0, 8.3, by + 1.4, -2.2, 'brass'))
    e.append(box(7.85, by + 1.4, -2.7, 8.15, by + 2.0, -2.3, 'iron'))
    e.append(box(7.7, by + 1.9, -2.8, 8.3, by + 2.4, -2.2, 'brass', top='steel_light'))
    e.append(box(7.2, by + 0.9, 11.7, 8.8, by + 1.2, 13.2, 'iron'))
    e.append(box(7.2, by + 1.2, 12.1, 7.65, by + 1.9, 12.7, 'iron'))
    e.append(box(8.35, by + 1.2, 12.1, 8.8, by + 1.9, 12.7, 'iron'))
    e.append(box(7.2, 7.4, 10, 8.8, 9.2, 18, 'wood', top='wood_light', end='wood_dark'))                                   # 台
    e.append(box(7.25, 2.6, 13.5, 8.75, 8.2, 17.5, 'wood', top='wood_light', end='wood_dark', rotate=('x', -22.5, (8, 8, 15))))   # 握り（下へ曲がる）
    e.append(box(6.95, 0.6, 15.4, 9.05, 2.8, 18.0, 'brass', top='brass_dark', end='brass_dark', rotate=('x', -22.5, (8, 8, 15))))  # 握り玉
    e.append(box(7.2, 7.0, -1, 8.8, 7.9, 10, 'wood', end='wood_dark'))
    e.append(box(6.6, 8.4, 9.5, 7.2, 10.4, 14.5, 'brass', top='brass_dark', end='brass_dark'))
    e.append(box(8.8, 8.4, 9.5, 9.4, 10.4, 14.5, 'brass', top='brass_dark', end='brass_dark'))
    e.append(box(6.9, by + 0.9, 12.0, 7.5, by + 1.3, 13.2, 'brass_dark'))
    e.append(box(6.5, 10.2, 9.5, 6.85, 11.9, 10.3, 'iron'))
    e.append(box(6.5, 11.5, 7.7, 6.85, 12.0, 10.3, 'iron'))
    e.append(box(6.55, 11.6, 6.9, 6.8, 12.0, 7.9, 'cord'))
    if loaded: e += ember(6.4, 11.4, 6.3)
    return e


def ember(x, y, z):
    """火縄の先の、燃える光。小さな核と、少し大きな光の殻（light_emission で、暗い所でも光る）。"""
    return [box(x + 0.05, y + 0.15, z, x + 0.4, y + 0.75, z + 0.65, 'ember', emission=14),
            box(x - 0.15, y - 0.05, z - 0.2, x + 0.6, y + 0.95, z + 0.85, 'ember', emission=14)]


# ---- 構え（display） ----

def rot(rx, ry, rz):
    """display の回転（JOML の XYZ: 先に x、次に y、最後に z を回す）の行列。"""
    rx, ry, rz = math.radians(rx), math.radians(ry), math.radians(rz)
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    mx = [[1, 0, 0], [0, cx, -sx], [0, sx, cx]]
    my = [[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]
    mz = [[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]
    mm = lambda a, b: [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    return mm(mz, mm(my, mx))


def apply(matrix, v): return [sum(matrix[i][k] * v[k] for k in range(3)) for i in range(3)]


# バニラの剣の柄が、一人称で、手のどこに来るか（display の平行移動の単位。handheld の [0,-90,25]・[1.13,3.2,1.13]・0.68 から計算）
SWORD_GRIP = apply(rot(0, -90, 25), (-6, -6, 0))
SWORD_GRIP = [1.13 + 0.68 * SWORD_GRIP[0], 3.2 + 0.68 * SWORD_GRIP[1], 1.13 + 0.68 * SWORD_GRIP[2]]


def first_person(grip, scale, yaw, side):
    """銃の握り（モデル上の点 grip）が、剣の柄と同じ手の位置に来る、一人称の display。yaw は、銃口を中央へ向ける角度（度）。"""
    matrix = rot(0, yaw * side, 0)
    offset = apply(matrix, [grip[i] - 8 for i in range(3)])
    translation = [round(SWORD_GRIP[i] - scale * offset[i], 2) for i in range(3)]
    return {'rotation': [0, yaw * side, 0], 'translation': translation, 'scale': [scale] * 3}


def sword_hand_third_person():
    """バニラの剣の柄が、三人称で、手のどこに来るか（handheld の [0,-90,55]・[0,4,0.5]・0.85 から計算。display の座標）。"""
    g = apply(rot(0, -90, 55), (-6, -6, 0))
    return [(0, 4.0, 0.5)[i] + 0.85 * g[i] for i in range(3)]


def third_person(grip, scale):
    """三人称。銃身は、display の座標の北（-z）、つまり、クロスボウと同じ前向きにし（回転なし）、握りが、剣の柄と同じ手の位置に来るように動かす。"""
    hand = sword_hand_third_person()
    return {'rotation': [0, 0, 0], 'translation': [round(hand[i] - scale * (grip[i] - 8), 2) for i in range(3)], 'scale': [scale] * 3}


def display(grip, scale, hidden=False):
    if hidden:
        tiny = {'rotation': [0, 0, 0], 'translation': [0, -8, -8], 'scale': [0.001] * 3}
        return {'firstperson_righthand': tiny, 'firstperson_lefthand': tiny, 'thirdperson_righthand': third_person(grip, scale), 'thirdperson_lefthand': third_person(grip, scale)}
    return {
        'firstperson_righthand': first_person(grip, scale, 12, 1),
        'firstperson_lefthand': first_person(grip, scale, 12, -1),
        'thirdperson_righthand': third_person(grip, scale),
        'thirdperson_lefthand': third_person(grip, scale),
        'gui': {'rotation': [0, -90, 45], 'translation': [0, 0, 0], 'scale': [round(scale * 0.8, 2)] * 3},
    }


GRIPS = {'matchlock': ([8, 9, 17], 0.5), 'tanzutsu': ([8, 6, 14], 0.7)}


def models():
    """{'matchlock': (要素の並び, 握り, 倍率), ...}"""
    return {'matchlock': long_gun(False), 'matchlock_loaded': long_gun(True), 'tanzutsu': short_gun(False), 'tanzutsu_loaded': short_gun(True)}


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def build():
    atlas_path = PACK / 'assets/hnmt/textures/item/gun_model/atlas.png'
    atlas_path.parent.mkdir(parents=True, exist_ok=True)
    paint_atlas().save(atlas_path)
    for name, elements in models().items():
        grip, scale = GRIPS[name.replace('_loaded', '')]
        base = {'textures': {'0': TEXTURE, 'particle': TEXTURE}, 'texture_size': [ATLAS, ATLAS], 'elements': elements}
        write_json(PACK / 'assets/hnmt/models/item/gun' / (name + '.json'), dict(base, display=display(grip, scale)))
        if name.endswith('_loaded'):   # 覗いているあいだ（右クリックを押している間）の、手に持った銃は、見えなくする
            write_json(PACK / 'assets/hnmt/models/item/gun' / (name.replace('_loaded', '_aim') + '.json'), dict(base, display=display(grip, scale, hidden=True)))
    print('Wrote %d gun models' % len(models()))


if __name__ == '__main__': build()
