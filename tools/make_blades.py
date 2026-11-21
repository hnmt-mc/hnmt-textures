#!/usr/bin/env python3
"""刀と鞘（刀3種・妖刀・名刀2振り・刺股・レイピア・鞘2状態）の絵とモデルを作る。

どれも、32×32の平らなアイコン（斜めに、左下が柄・右上が切っ先）。モデルは、バニラの剣と同じ item/handheld
（手に持ったとき、剣と同じ向きになる）。鞘は、持つ物ではないので item/generated。統合版も、平らなアイコンのまま出す。

  python3 tools/make_blades.py            絵とモデルを書き出す
  python3 tools/make_blades.py --preview  絵を拡大して並べる（build/blades/preview.png）
"""
import argparse
import json
from PIL import Image
from artwork import PACK, BUILD

SIZE = 32
# （名前, 表示名, 持ち方）。持ち方: handheld は剣のように持つ、generated は物のように持つ
BLADES = [('katana_iron', '鉄の刀', 'handheld'), ('katana_diamond', 'ダイヤの刀', 'handheld'), ('katana_netherite', 'ネザライトの刀', 'handheld'),
          ('youtou', '妖刀', 'handheld'), ('meito_izumi', '和泉守兼定', 'handheld'), ('meito_nagasone', '長曽祢虎徹', 'handheld'),
          ('sasumata', '刺股', 'handheld'), ('rapier', 'レイピア', 'handheld'), ('sheath', '鞘', 'generated'), ('sheath_full', '鞘（刀入り）', 'generated')]

# 刀ごとの色: 刃（明・中・暗）・刃の縁（ふつうは刃の明るい色）・つば・柄（地・巻き）・飾り
STYLES = {
    'katana_iron': dict(blade=('#e6eaee', '#b4bcc6', '#80899a'), guard='#8a6f3a', grip=('#2b2b33', '#4a4a55'), pommel='#8a6f3a'),
    'katana_diamond': dict(blade=('#d6fbf7', '#6fe0da', '#2fa6a0'), guard='#2fa6a0', grip=('#1f3a52', '#355d80'), pommel='#2fa6a0'),
    'katana_netherite': dict(blade=('#a39aaa', '#6a6070', '#443d4a'), guard='#b88a3a', grip=('#2a1c1c', '#4a3030'), pommel='#b88a3a'),
    'youtou': dict(blade=('#d9b8e8', '#8445ad', '#431d5c'), guard='#7a1030', grip=('#1b0f1f', '#3a1f44'), pommel='#e0245e', glow='#e0245e'),
    'meito_izumi': dict(blade=('#fafbff', '#d6dce8', '#9aa6ba'), guard='#f0c040', grip=('#7a1f1f', '#b03030'), pommel='#f0c040', hamon='#ffffff'),
    'meito_nagasone': dict(blade=('#eef5ff', '#bccfee', '#8397be'), guard='#cfd0da', grip=('#1a2a55', '#2f4690'), pommel='#cfd0da', hamon='#ffffff'),
}
LACQUER = ('#3a3a44', '#1d1d22', '#0f0f13')
GOLD, GOLD_DARK = '#e0b84a', '#a8862a'
WOOD, WOOD_DARK, STEEL, STEEL_DARK = '#a47a45', '#7a5630', '#aab4c0', '#6f7a88'


def rgba(color):
    return tuple(bytes.fromhex(color[1:])) + (255,)


def put(image, x, y, color):
    if 0 <= x < SIZE and 0 <= y < SIZE: image.putpixel((x, y), rgba(color))


def diagonal(image, start, end, colors, half=1):
    """左下（start）から右上（end）へ、斜めに太さのある線を引く。colors は、左上の縁・中・右下の縁。"""
    x0, y0 = start
    steps = end[0] - x0
    for i in range(steps + 1):
        x, y = x0 + i, y0 - i
        for k in range(-half, half + 1):
            index = 0 if k < 0 else (len(colors) - 1 if k > 0 else len(colors) // 2)
            put(image, x + k, y + k, colors[index])
            # 斜めの点だけでは、市松模様のように隙間が空く。右隣も塗って、1本の線につなぐ
            put(image, x + k + 1, y + k, colors[index])


def cross(image, center, half, colors):
    """刀に直角の線（つば・鍔元の飾り）。center を通り、左上から右下へ。"""
    cx, cy = center
    for k in range(-half, half + 1):
        put(image, cx + k, cy + k, colors[0] if len(colors) == 1 else colors[min(abs(k) * len(colors) // (half + 1), len(colors) - 1)])
        put(image, cx + k + 1, cy + k, colors[0])


def katana(name):
    style = STYLES[name]
    image = Image.new('RGBA', (SIZE, SIZE))
    light, mid, dark = style['blade']
    diagonal(image, (11, 21), (29, 3), (light, mid, dark), half=1)           # 刃
    for i in range(0, 17, 2):                                                # 刃紋（波打つ明るい線）
        if 'hamon' in style: put(image, 13 + i, 20 - i - 0, style['hamon'])
    for t in range(3):                                                       # 切っ先
        put(image, 29 + t * 0, 3, light)
    if 'glow' in style:
        for i in range(2, 17, 3): put(image, 12 + i, 22 - i, style['glow'])
    cross(image, (9, 23), 3, [style['guard']])                               # つば
    diagonal(image, (3, 29), (8, 24), style['grip'], half=1)                 # 柄
    for i in range(0, 5, 2): put(image, 4 + i, 28 - i, style['grip'][1])     # 柄巻き
    put(image, 2, 30, style['pommel']); put(image, 3, 30, style['pommel'])   # 柄頭
    return image


def sasumata():
    image = Image.new('RGBA', (SIZE, SIZE))
    diagonal(image, (3, 29), (22, 10), (WOOD, WOOD, WOOD_DARK), half=0)       # 柄（長い棒）
    for i in range(0, 18, 4): put(image, 3 + i, 29 - i, '#d9c9a0')           # 棒の巻き
    # U字の先（2本の腕とつなぎ）
    diagonal(image, (20, 12), (28, 4), (STEEL, STEEL, STEEL_DARK), half=0)
    diagonal(image, (23, 9), (31, 1), (STEEL, STEEL, STEEL_DARK), half=0)
    for k in range(0, 4): put(image, 20 + k, 12 - k + 1 + (0), STEEL_DARK); put(image, 21 + k, 11 - k + 3, STEEL)
    cross(image, (21, 11), 2, [STEEL_DARK])
    return image


def rapier():
    image = Image.new('RGBA', (SIZE, SIZE))
    diagonal(image, (11, 21), (30, 2), ('#f2f5f8', '#c4ccd6', '#8c97a6'), half=0)   # 細い刃
    for i in range(0, 19, 3): put(image, 12 + i, 21 - i + 1, '#8c97a6')
    # 椀形の護拳（つばの丸い皿）
    for k in range(-4, 5):
        put(image, 8 + k, 24 + k, GOLD)
        if abs(k) < 4: put(image, 8 + k + 1, 24 + k, GOLD_DARK)
    for k in range(-3, 4): put(image, 7 + k, 25 + k, GOLD_DARK)
    diagonal(image, (3, 29), (7, 25), ('#4a2c1a', '#3a2010'), half=0)
    put(image, 2, 30, GOLD); put(image, 3, 30, GOLD)
    return image


def sheath(full):
    image = Image.new('RGBA', (SIZE, SIZE))
    diagonal(image, (7, 25), (28, 4), LACQUER, half=1)                        # 鞘（黒漆）
    for i in range(1, 20, 4): put(image, 9 + i, 23 - i - 1, '#5a5a66')       # 漆の艶
    cross(image, (8, 24), 2, [GOLD])                                           # 鯉口（口金）
    for k in (-1, 0, 1): put(image, 27 + k, 5 + k + 1 - 1, GOLD_DARK)         # 鐺（先の金具）
    put(image, 29, 3, GOLD); put(image, 28, 3, GOLD)
    cross(image, (17, 15), 2, [GOLD_DARK])                                     # 帯取りの金具
    if full:
        diagonal(image, (2, 30), (6, 26), ('#1a2a55', '#2f4690'), half=1)    # 柄（刀が入っている）
        for i in (0, 2, 4): put(image, 3 + i, 29 - i, '#9aa6ba')
        cross(image, (6, 26), 2, [GOLD])                                       # 鍔
    return image


def draw(name):
    if name in STYLES: return katana(name)
    if name == 'sasumata': return sasumata()
    if name == 'rapier': return rapier()
    if name == 'sheath': return sheath(False)
    if name == 'sheath_full': return sheath(True)
    raise ValueError('Unknown blade: ' + name)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def build():
    for name, _, holding in BLADES:
        path = PACK / 'assets/hnmt/textures/item/sword' / (name + '.png')
        path.parent.mkdir(parents=True, exist_ok=True)
        draw(name).save(path)
        write_json(PACK / 'assets/hnmt/items/sword' / (name + '.json'), {'model': {'type': 'minecraft:model', 'model': 'hnmt:item/sword/' + name}})
        write_json(PACK / 'assets/hnmt/models/item/sword' / (name + '.json'),
                   {'parent': 'minecraft:item/' + holding, 'textures': {'layer0': 'hnmt:item/sword/' + name}})
    print('Wrote %d blade icons' % len(BLADES))


def preview():
    target = BUILD / 'blades'
    target.mkdir(parents=True, exist_ok=True)
    scale, columns = 8, 5
    rows = (len(BLADES) + columns - 1) // columns
    sheet = Image.new('RGBA', (columns * (SIZE * scale + 8) + 8, rows * (SIZE * scale + 8) + 8), (232, 226, 214, 255))
    for i, (name, _, _) in enumerate(BLADES):
        big = draw(name).resize((SIZE * scale, SIZE * scale), Image.NEAREST)
        sheet.paste(big, (8 + (i % columns) * (SIZE * scale + 8), 8 + (i // columns) * (SIZE * scale + 8)), big)
    sheet.save(target / 'preview.png')
    print('Preview: ' + str(target / 'preview.png'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview', action='store_true', help='絵を拡大して並べる')
    args = parser.parse_args()
    preview() if args.preview else build()


if __name__ == '__main__': main()
