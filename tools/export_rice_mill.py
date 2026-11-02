#!/usr/bin/env python3
"""精米機（hnmt:rice/mill）の書き出し。Blockbench を使わずに、Blockbench と同じ形のファイルを作る。

make_rice_models.py の形（MILL_SWATCHES と _mill_geometry）から、次の4つを作る。Blockbench で開き直して手直しもできる。
  assets/hnmt/textures/item/rice/mill.png   絵（16px）
  models3d/rice/mill.json                   3Dモデル（Javaのモデルの書き出し）
  blockbench/rice/mill.bbmodel              Blockbench のプロジェクト
  assets/hnmt/items|models/item/rice/mill.json
"""
import base64
import copy
import json
import uuid
from artwork import PACK
from make_rice_models import build, display

GROUPS = {'Base': ('Base', 'Tray'), 'Body': ('Body', 'HoopLow', 'HoopHigh'),
          'Hopper': ('Hopper1', 'Hopper2', 'Hopper3', 'RimN', 'RimS', 'RimW', 'RimE'),
          'Parts': ('Spout', 'Wheel', 'Handle')}


def _group_of(part):
    return next(group for group, names in GROUPS.items() if part in names)


def _normalized_display():
    shown = copy.deepcopy(display('mill'))
    shown.pop('fixed', None)       # すべて初期値なら、Blockbench は書き出さない
    gui = shown['gui']
    gui['rotation'] = [gui['rotation'][0], ((gui['rotation'][1] + 180) % 360) - 180, gui['rotation'][2]]
    return shown


def main():
    model, png = build('mill')
    elements = model['elements']
    order = [name for names in GROUPS.values() for name in names]
    elements = sorted(elements, key=lambda part: order.index(part['name']))
    groups, index = [], {}
    for position, part in enumerate(elements):
        index.setdefault(_group_of(part['name']), []).append(position)
    for group in GROUPS:
        groups.append({'name': group, 'origin': [8, 8, 8], 'scope': 0, 'color': 0, 'children': index[group]})
    java = {'format_version': '1.21.11', 'credit': model['credit'], 'textures': model['textures'], 'elements': elements,
            'gui_light': 'front', 'display': _normalized_display(), 'groups': groups}
    (PACK/'models3d/rice/mill.json').write_text(json.dumps(java, ensure_ascii=False, indent=2) + '\n')

    path = PACK/'blockbench/rice/mill.bbmodel'
    project = json.loads(path.read_text())
    cube, group_template = copy.deepcopy(project['elements'][0]), copy.deepcopy(project['groups'][0])
    project['elements'], project['groups'], project['outliner'] = [], [], []
    ids = {}
    for part in elements:
        item = copy.deepcopy(cube)
        item.update({'name': part['name'], 'from': part['from'], 'to': part['to'],
                     'uuid': str(uuid.uuid5(uuid.NAMESPACE_URL, 'hnmt:mill:cube:' + part['name']))})
        item['faces'] = {face: {'uv': data['uv'], 'texture': 0} for face, data in part['faces'].items()}
        project['elements'].append(item)
        ids[part['name']] = item['uuid']
    for group in GROUPS:
        entry = copy.deepcopy(group_template)
        entry.update({'name': group, 'uuid': str(uuid.uuid5(uuid.NAMESPACE_URL, 'hnmt:mill:group:' + group)), 'children': []})
        project['groups'].append(entry)
        project['outliner'].append({'uuid': entry['uuid'], 'isOpen': False,
                                    'children': [ids[part['name']] for part in elements if _group_of(part['name']) == group]})
    project['textures'][0]['source'] = 'data:image/png;base64,' + base64.b64encode(png.read_bytes()).decode()
    project['display'] = _normalized_display()
    path.write_text(json.dumps(project, ensure_ascii=False, indent=2))
    print('精米機を書き出しました: 直方体 %d 個' % len(elements))


if __name__ == '__main__': main()
